"""
Optional hosted-LLM provider adapter for the SuperClarity Assistant.

The app works fully without any provider configured (built-in rule engine).
When a user supplies a key in the assistant settings, requests are proxied
through this module so no CORS handling is needed in the browser.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

PROVIDER_DEFAULTS: Dict[str, Dict[str, str]] = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "label": "Groq",
    },
    "nim": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.3-70b-instruct",
        "label": "NVIDIA NIM",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.0-flash",
        "label": "Google Gemini",
    },
}


def normalize_provider(value: Optional[str]) -> str:
    provider = (value or "").strip().lower().replace(" ", "")
    aliases = {
        "google": "gemini",
        "googlegemini": "gemini",
        "nvidia": "nim",
        "nvidia-nim": "nim",
        "nvidianim": "nim",
        "groqai": "groq",
    }
    provider = aliases.get(provider, provider)
    return provider if provider in PROVIDER_DEFAULTS else ""


def _sanitize_model(model: Optional[str], provider: str) -> str:
    value = (model or "").strip() or PROVIDER_DEFAULTS[provider]["model"]
    return re.sub(r"[^A-Za-z0-9._:/-]", "", value)[:120]


def _sanitize_base_url(base_url: Optional[str], provider: str) -> str:
    value = (base_url or "").strip() or PROVIDER_DEFAULTS[provider]["base_url"]
    value = value.rstrip("/")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Base URL must start with http:// or https://")
    return value


def _post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: int = 30) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError("Provider returned an unexpected response")
    return data


def _read_error(error: Exception, secret: Optional[str] = None) -> str:
    if isinstance(error, urllib.error.HTTPError):
        try:
            text = error.read().decode("utf-8", errors="replace")
        except Exception:
            text = str(error)
    else:
        text = str(error)
    if secret:
        text = text.replace(secret, "[redacted]")
    return re.sub(r"\s+", " ", text).strip()[:300]


def _openai_compatible_reply(data: Dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("Provider returned no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Provider returned an empty response")
    return content.strip()


def _gemini_reply(data: Dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini returned no candidates")
    parts = (((candidates[0].get("content") or {}).get("parts")) or [])
    text = "\n".join(
        str(part.get("text", "")) for part in parts if isinstance(part, dict) and part.get("text")
    ).strip()
    if not text:
        raise ValueError("Gemini returned an empty response")
    return text


def generate_llm_reply(
    provider: str,
    api_key: str,
    message: str,
    system_prompt: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a provider answer or raise a safe, user-presentable error."""
    name = normalize_provider(provider)
    if not name:
        raise ValueError("Unknown AI provider")
    if not api_key or not api_key.strip():
        raise ValueError("API key is missing")
    if not message or not message.strip():
        raise ValueError("Message is empty")

    key = api_key.strip()
    model_name = _sanitize_model(model, name)
    endpoint_base = _sanitize_base_url(base_url, name)

    try:
        if name == "gemini":
            url = (
                f"{endpoint_base}/models/{urllib.parse.quote(model_name, safe='')}"
                f":generateContent?key={urllib.parse.quote(key, safe='')}"
            )
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": message}]}],
                "generationConfig": {"temperature": 0.45, "maxOutputTokens": 1200},
            }
            data = _post_json(url, payload, {}, timeout=35)
            text = _gemini_reply(data)
        else:
            url = f"{endpoint_base}/chat/completions"
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                "temperature": 0.45,
                "max_tokens": 1200,
                "stream": False,
            }
            data = _post_json(
                url, payload, {"Authorization": f"Bearer {key}"}, timeout=35
            )
            text = _openai_compatible_reply(data)
    except Exception as exc:
        raise RuntimeError(_read_error(exc, key)) from None

    return {
        "text": text,
        "provider": name,
        "provider_label": PROVIDER_DEFAULTS[name]["label"],
        "model": model_name,
        "base_url": endpoint_base if name != "gemini" else "",
    }
