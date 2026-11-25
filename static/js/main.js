/**
 * SupplierClarity AI - Frontend Application Controller
 * Handles image ingestion, async neural super-resolution, interactive split slider,
 * side-by-side inspection, and metrics telemetry.
 * Reference: SmartBridge Demo Project Architecture (Milestones 4.1 & 4.2)
 */

document.addEventListener("DOMContentLoaded", () => {
    // State variables
    let selectedFile = null;
    let selectedSampleId = "luxury_watch";
    let selectedScale = 4;
    let currentMethod = "realesrgan";
    let isSliderDragging = false;

    // DOM Elements
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const dropzonePrompt = document.getElementById("dropzone-prompt");
    const dropzonePreview = document.getElementById("dropzone-preview");
    const previewImg = document.getElementById("preview-img");
    const previewFilename = document.getElementById("preview-filename");
    const previewDims = document.getElementById("preview-dims");
    const btnClearUpload = document.getElementById("btn-clear-upload");
    const samplePills = document.querySelectorAll(".sample-pill");
    const scaleButtons = document.querySelectorAll("#scale-toggle-group .toggle-btn");
    const modelSelect = document.getElementById("model-select");
    const checkDenoise = document.getElementById("check-denoise");
    const checkSharpen = document.getElementById("check-sharpen");
    const upscaleForm = document.getElementById("upscale-form");
    const btnSubmit = document.getElementById("btn-submit");
    const btnText = btnSubmit.querySelector(".btn-text");
    const btnLoader = btnSubmit.querySelector(".btn-loader");

    // Results Elements
    const resultsSection = document.getElementById("results-section");
    const imgBefore = document.getElementById("img-before");
    const imgAfter = document.getElementById("img-after");
    const sideImgBefore = document.getElementById("side-img-before");
    const sideImgAfter = document.getElementById("side-img-after");
    const sideOrigRes = document.getElementById("side-orig-res");
    const sideEnhRes = document.getElementById("side-enh-res");
    const sliderWrapper = document.getElementById("slider-wrapper");
    const sliderAfterContainer = document.getElementById("slider-after-container");
    const sliderHandle = document.getElementById("slider-handle");
    const btnModeSlider = document.getElementById("btn-mode-slider");
    const btnModeSide = document.getElementById("btn-mode-side");
    const sideWrapper = document.getElementById("side-wrapper");

    // Metric Badges
    const metricResolution = document.getElementById("metric-resolution");
    const metricScale = document.getElementById("metric-scale");
    const metricLatency = document.getElementById("metric-latency");
    const metricSharpness = document.getElementById("metric-sharpness");
    const metricSharpnessVals = document.getElementById("metric-sharpness-vals");
    const metricPsnrSsim = document.getElementById("metric-psnr-ssim");
    const cardGroundTruth = document.getElementById("card-ground-truth");

    // Download buttons
    const btnDlPng = document.getElementById("btn-dl-png");
    const btnDlJpg = document.getElementById("btn-dl-jpg");

    // Modal
    const btnBenchmarkModal = document.getElementById("btn-benchmark-modal");
    const benchmarkModal = document.getElementById("benchmark-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");

    // =================================================================
    // 1. INITIALIZATION & SAMPLE LOADING
    // =================================================================
    loadSampleProduct("luxury_watch");

    function loadSampleProduct(sampleId) {
        selectedSampleId = sampleId;
        selectedFile = null;

        samplePills.forEach(pill => {
            pill.classList.toggle("active", pill.dataset.sampleId === sampleId);
        });

        fetch(`/api/sample/${sampleId}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showPreview(data.image_base64, `${sampleId}_vendor_input.jpg`, data.resolution);
                }
            })
            .catch(err => console.error("Error loading sample:", err));
    }

    samplePills.forEach(pill => {
        pill.addEventListener("click", () => {
            loadSampleProduct(pill.dataset.sampleId);
        });
    });

    // =================================================================
    // 2. FILE UPLOAD, GALLERY SELECTION & DRAG AND DROP
    // =================================================================
    const btnGalleryUpload = document.getElementById("btn-gallery-upload");
    const browseLink = document.getElementById("browse-link");

    if (btnGalleryUpload) {
        btnGalleryUpload.addEventListener("click", (e) => {
            e.stopPropagation();
            fileInput.click();
        });
    }

    if (browseLink) {
        browseLink.addEventListener("click", (e) => {
            e.stopPropagation();
            fileInput.click();
        });
    }

    dropZone.addEventListener("click", (e) => {
        if (!e.target.closest("#btn-clear-upload") && !e.target.closest("#btn-gallery-upload")) {
            fileInput.click();
        }
    });

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleUploadedFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
            handleUploadedFile(e.target.files[0]);
        }
    });

    // Support clipboard paste (e.g. copying image from photos/gallery or web)
    window.addEventListener("paste", (e) => {
        if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
            const file = e.clipboardData.files[0];
            const isImg = (file.type && file.type.startsWith("image/")) || 
                          /\.(png|jpe?g|webp|jfif|bmp)$/i.test(file.name);
            if (isImg) {
                handleUploadedFile(file);
            }
        }
    });

    function handleUploadedFile(file) {
        if (!file) return;

        // Support standard image MIME types and photo gallery formats
        const isImage = (file.type && file.type.startsWith("image/")) || 
                        /\.(png|jpe?g|webp|jfif|bmp)$/i.test(file.name);
        if (!isImage) {
            alert("Please upload a valid image file from your gallery or computer (PNG, JPG, JPEG, WEBP, BMP).");
            return;
        }

        if (file.size > 16 * 1024 * 1024) {
            alert("File size exceeds 16 MB limit.");
            return;
        }

        selectedFile = file;
        selectedSampleId = null;
        samplePills.forEach(pill => pill.classList.remove("active"));

        const reader = new FileReader();
        reader.onload = (e) => {
            const tempImg = new Image();
            tempImg.onload = () => {
                showPreview(e.target.result, file.name || "gallery_upload.jpg", `${tempImg.width}x${tempImg.height} px`);
            };
            tempImg.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    function showPreview(src, filename, dims) {
        previewImg.src = src;
        previewFilename.textContent = filename;
        previewDims.textContent = dims;
        dropzonePrompt.classList.add("hidden");
        dropzonePreview.classList.remove("hidden");
    }

    btnClearUpload.addEventListener("click", (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = "";
        dropzonePreview.classList.add("hidden");
        dropzonePrompt.classList.remove("hidden");
        // Re-activate default sample
        loadSampleProduct("luxury_watch");
    });

    // =================================================================
    // 3. UPSCALE SCALE & MODEL SELECTION
    // =================================================================
    scaleButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            scaleButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            selectedScale = parseInt(btn.dataset.scale);
        });
    });

    modelSelect.addEventListener("change", (e) => {
        currentMethod = e.target.value;
    });

    // =================================================================
    // 4. ASYNC FORM SUBMISSION & RESTORATION
    // =================================================================
    upscaleForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!selectedFile && !selectedSampleId) {
            alert("Please upload a vendor product image or select a demo sample.");
            return;
        }

        // Set Loading State
        btnSubmit.disabled = true;
        btnText.classList.add("hidden");
        btnLoader.classList.remove("hidden");

        const formData = new FormData();
        formData.append("scale", selectedScale);
        formData.append("method", modelSelect.value);
        formData.append("denoise", checkDenoise.checked);
        formData.append("sharpen", checkSharpen.checked);

        if (selectedFile) {
            formData.append("file", selectedFile);
        } else if (selectedSampleId) {
            formData.append("sample_id", selectedSampleId);
        }

        try {
            const response = await fetch("/api/upscale", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || "Enhancement failed on server.");
            }

            renderEnhancementResults(data);

        } catch (error) {
            console.error("Enhancement Error:", error);
            alert(`Error: ${error.message}`);
        } finally {
            // Restore button state
            btnSubmit.disabled = false;
            btnText.classList.remove("hidden");
            btnLoader.classList.add("hidden");
        }
    });

    // =================================================================
    // 5. RENDER RESULTS & TELEMETRY
    // =================================================================
    function renderEnhancementResults(data) {
        // 1. Set Images
        imgBefore.src = data.original_image;
        imgAfter.src = data.enhanced_image;
        sideImgBefore.src = data.original_image;
        sideImgAfter.src = data.enhanced_image;

        // 2. Set Dimension Labels
        sideOrigRes.textContent = `${data.original_resolution} px`;
        sideEnhRes.textContent = `${data.enhanced_resolution} px`;

        // 3. Update Metrics Grid
        metricResolution.textContent = `${data.original_resolution} → ${data.enhanced_resolution}`;
        metricScale.textContent = `${data.scale}× Geometric Super-Resolution (${data.method.toUpperCase()})`;
        metricLatency.textContent = `${data.latency_ms} ms (${data.latency_seconds}s)`;

        if (data.metrics) {
            metricSharpness.textContent = `+${data.metrics.sharpness_boost}`;
            metricSharpnessVals.textContent = `Laplacian: ${data.metrics.orig_sharpness} → ${data.metrics.enhanced_sharpness}`;

            if (data.metrics.has_ground_truth) {
                metricPsnrSsim.textContent = `SSIM: ${data.metrics.ssim} | PSNR: ${data.metrics.psnr_db} dB`;
                cardGroundTruth.classList.remove("hidden");
            } else {
                metricPsnrSsim.textContent = "Catalog Input (No reference)";
                cardGroundTruth.classList.add("hidden");
            }
        }

        // 4. Configure Download Links
        btnDlPng.href = data.download_png_url;
        btnDlJpg.href = data.download_jpg_url;

        // 5. Reset slider to center
        setSliderPosition(50);

        // 6. Reveal section and smooth scroll
        resultsSection.classList.remove("hidden");
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

        // 7. Store active ML context for the Multilingual Chatbot
        window.currentUpscaleResult = data;
        const chatContextBanner = document.getElementById("chat-context-banner");
        const chatContextSummary = document.getElementById("chat-context-summary");
        if (chatContextBanner && chatContextSummary) {
            chatContextBanner.style.display = "flex";
            const ssimText = data.metrics && data.metrics.ssim ? `SSIM: ${data.metrics.ssim}` : `Sharp: ${data.metrics.sharpness_boost}`;
            chatContextSummary.textContent = `Active Result: ${data.original_resolution} ➡️ ${data.enhanced_resolution} (${data.scale}×, ${ssimText})`;
        }
    }

    // =================================================================
    // 6. INTERACTIVE COMPARISON SLIDER LOGIC
    // =================================================================
    function setSliderPosition(percentage) {
        const clamped = Math.max(0, Math.min(100, percentage));
        sliderHandle.style.left = `${clamped}%`;
        sliderAfterContainer.style.clipPath = `polygon(${clamped}% 0, 100% 0, 100% 100%, ${clamped}% 100%)`;
    }

    function handleSliderMove(e) {
        if (!isSliderDragging) return;
        const rect = sliderWrapper.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const offsetX = clientX - rect.left;
        const percentage = (offsetX / rect.width) * 100;
        setSliderPosition(percentage);
    }

    sliderWrapper.addEventListener("mousedown", (e) => {
        isSliderDragging = true;
        handleSliderMove(e);
    });

    window.addEventListener("mousemove", handleSliderMove);
    window.addEventListener("mouseup", () => {
        isSliderDragging = false;
    });

    sliderWrapper.addEventListener("touchstart", (e) => {
        isSliderDragging = true;
        handleSliderMove(e);
    }, { passive: true });

    window.addEventListener("touchmove", handleSliderMove, { passive: true });
    window.addEventListener("touchend", () => {
        isSliderDragging = false;
    });

    // =================================================================
    // 7. VIEW MODE SWITCHING (SLIDER VS SIDE-BY-SIDE)
    // =================================================================
    btnModeSlider.addEventListener("click", () => {
        btnModeSlider.classList.add("active");
        btnModeSide.classList.remove("active");
        sliderWrapper.classList.remove("hidden");
        sideWrapper.classList.add("hidden");
    });

    btnModeSide.addEventListener("click", () => {
        btnModeSide.classList.add("active");
        btnModeSlider.classList.remove("active");
        sideWrapper.classList.remove("hidden");
        sliderWrapper.classList.add("hidden");
    });

    // =================================================================
    // 8. BENCHMARK RESULTS MODAL
    // =================================================================
    btnBenchmarkModal.addEventListener("click", () => {
        benchmarkModal.classList.remove("hidden");
    });

    btnCloseModal.addEventListener("click", () => {
        benchmarkModal.classList.add("hidden");
    });

    benchmarkModal.addEventListener("click", (e) => {
        if (e.target === benchmarkModal) {
            benchmarkModal.classList.add("hidden");
        }
    });

    // =================================================================
    // 9. AUTOMATED DEMO MODE FOR HEADLESS SCREENSHOT CAPTURE
    // =================================================================
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('demo') === 'results') {
        setTimeout(() => {
            if (upscaleForm) upscaleForm.dispatchEvent(new Event('submit'));
        }, 300);
    } else if (urlParams.get('demo') === 'modal') {
        setTimeout(() => {
            if (benchmarkModal) benchmarkModal.classList.remove('hidden');
        }, 200);
    } else if (urlParams.get('demo') === 'chat') {
        setTimeout(() => {
            if (chatbotDrawer) {
                chatbotDrawer.classList.add('active');
                appendChatBubble("user", "<p>What is this website about and how does it help e-commerce sellers?</p>");
                const chatgptAnswer = `<h3>🛍️ Welcome to SupplierClarity AI!</h3>
<p><strong>SupplierClarity AI</strong> is an enterprise-grade product image restoration platform engineered for e-commerce catalogs (Amazon, Shopify, Walmart).</p>
<p><strong>📌 The Problem:</strong> Suppliers frequently submit low-resolution (128x128 px), blurry, or WhatsApp-compressed photos. Requesting studio re-shoots costs <strong>$500–$1,000+ per batch</strong> and delays launches.</p>
<p><strong>🚀 What This Website Does:</strong></p>
<ul>
<li><strong>2× & 4× Super-Resolution:</strong> Upscales low-res thumbnails up to Ultra 4K in real time (<strong>~250 ms on CPU</strong>).</li>
<li><strong>Zero-Hallucination Guarantee:</strong> Reconstructs authentic textures, fabric weaves, and packaging typography without inventing fake logos.</li>
<li><strong>Interactive Split Slider:</strong> Inspect micro-details before and after in real time!</li>
</ul>`;
                appendChatBubble("assistant", chatgptAnswer, "Welcome to SupplierClarity AI! This website uses deep learning to upscale low-resolution supplier product photos into crisp catalog-ready images in under 250 milliseconds.");
            }
        }, 300);
    }

    // =================================================================
    // 10. MULTILINGUAL VOICE-ENABLED INTELLIGENT CHATBOT CONTROLLER
    // =================================================================
    const chatbotLauncher = document.getElementById("chatbot-launcher");
    const chatbotDrawer = document.getElementById("chatbot-drawer");
    const btnHeaderAssistant = document.getElementById("btn-header-assistant");
    const chatBtnMinimize = document.getElementById("chat-btn-minimize");
    const chatLangSelect = document.getElementById("chat-lang-select");
    const chatMessages = document.getElementById("chat-messages");
    const chatQuickPrompts = document.getElementById("chat-quick-prompts");
    const chatTextInput = document.getElementById("chat-text-input");
    const btnChatSend = document.getElementById("btn-chat-send");
    const btnVoiceRecord = document.getElementById("btn-voice-record");
    const voiceStatusBar = document.getElementById("voice-status-bar");
    const voiceStatusText = document.getElementById("voice-status-text");
    const btnExplainActive = document.getElementById("btn-explain-active");

    let currentChatLang = "en";
    let isSpeechRecording = false;
    let recognitionInstance = null;
    let currentSpeechButton = null;

    // Toggle Chatbot Drawer
    function toggleChatDrawer(forceOpen = null) {
        if (!chatbotDrawer) return;
        const willOpen = forceOpen !== null ? forceOpen : !chatbotDrawer.classList.contains("active");
        chatbotDrawer.classList.toggle("active", willOpen);
        if (willOpen && chatTextInput) {
            setTimeout(() => chatTextInput.focus(), 250);
        }
    }

    if (chatbotLauncher) chatbotLauncher.addEventListener("click", () => toggleChatDrawer());
    if (btnHeaderAssistant) btnHeaderAssistant.addEventListener("click", () => toggleChatDrawer(true));
    if (chatBtnMinimize) chatBtnMinimize.addEventListener("click", () => toggleChatDrawer(false));

    // Language Selector
    if (chatLangSelect) {
        chatLangSelect.addEventListener("change", (e) => {
            currentChatLang = e.target.value;
            const langNames = { en: "English", te: "తెలుగు (Telugu)", hi: "हिंदी (Hindi)" };
            const placeholders = {
                en: "Ask a question or speak...",
                te: "ప్రశ్న అడగండి లేదా మాట్లాడండి...",
                hi: "प्रश्न पूछें या बोलें..."
            };
            if (chatTextInput) chatTextInput.placeholder = placeholders[currentChatLang] || placeholders.en;
            console.log(`[Chatbot] Active language switched to: ${langNames[currentChatLang]}`);
        });
    }

    // Markdown Parser
    function renderMarkdownToHtml(md) {
        if (!md) return "";
        let html = md
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h3>$1</h3>')
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/gim, '<em>$1</em>')
            .replace(/`([^`]+)`/gim, '<code>$1</code>')
            .replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>')
            .replace(/^\s*\d+\.\s+(.*$)/gim, '<li>$1</li>')
            .replace(/\n\n/gim, '</p><p>')
            .replace(/\n/gim, '<br/>');

        // Wrap loose <li> tags in <ul>
        if (html.includes("<li>")) {
            html = html.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');
        }
        return `<p>${html}</p>`;
    }

    // Scroll Chat to Bottom
    function scrollChatToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Append Chat Bubble
    function appendChatBubble(role, htmlContent, speechText = "") {
        if (!chatMessages) return;

        const msgDiv = document.createElement("div");
        msgDiv.className = `chat-msg ${role}-msg`;

        const avatarDiv = document.createElement("div");
        avatarDiv.className = "msg-avatar";
        avatarDiv.innerHTML = role === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

        const bubbleDiv = document.createElement("div");
        bubbleDiv.className = "msg-bubble";
        bubbleDiv.innerHTML = htmlContent;

        if (role === "assistant" && speechText) {
            const listenBtn = document.createElement("button");
            listenBtn.type = "button";
            listenBtn.className = "btn-speech-play";
            listenBtn.dataset.speech = speechText;
            listenBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i> Listen';
            bubbleDiv.appendChild(listenBtn);
        }

        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(msgDiv);
        scrollChatToBottom();
    }

    // Send Query to /api/chat
    async function sendChatQuery(userQuery) {
        if (!userQuery || !userQuery.trim()) return;
        const cleanQuery = userQuery.trim();

        // 1. Display User Message
        appendChatBubble("user", `<p>${escapeHtml(cleanQuery)}</p>`);
        if (chatTextInput) chatTextInput.value = "";

        // 2. Display Typing Indicator
        const loadingId = "chat-loading-bubble";
        appendChatBubble("assistant", '<p><i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing with SupplierClarity AI...</p>');
        const loadingBubble = chatMessages.lastElementChild;
        loadingBubble.id = loadingId;

        // 3. Build Payload with ML Context
        const payload = {
            message: cleanQuery,
            language: currentChatLang,
            context: window.currentUpscaleResult || {
                scale: selectedScale,
                sample_id: selectedSampleId,
                method: modelSelect ? modelSelect.value : "realesrgan"
            }
        };

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (loadingBubble && loadingBubble.parentNode) {
                loadingBubble.parentNode.removeChild(loadingBubble);
            }

            if (!response.ok || !data.success) {
                throw new Error(data.error || "Assistant service unavailable.");
            }

            // 4. Render Assistant Response
            const parsedHtml = renderMarkdownToHtml(data.response_markdown);
            appendChatBubble("assistant", parsedHtml, data.speech_text);

            // 5. Update Quick Prompt Chips
            if (data.suggested_prompts && data.suggested_prompts.length > 0 && chatQuickPrompts) {
                chatQuickPrompts.innerHTML = "";
                data.suggested_prompts.forEach(p => {
                    const chip = document.createElement("button");
                    chip.className = "prompt-chip";
                    chip.dataset.query = p;
                    chip.innerHTML = `<i class="fa-solid fa-arrow-right"></i> ${escapeHtml(p)}`;
                    chatQuickPrompts.appendChild(chip);
                });
            }

        } catch (err) {
            console.error("Chatbot Request Error:", err);
            if (loadingBubble && loadingBubble.parentNode) {
                loadingBubble.parentNode.removeChild(loadingBubble);
            }
            appendChatBubble("assistant", `<p style="color: #f87171;"><i class="fa-solid fa-triangle-exclamation"></i> Error: ${escapeHtml(err.message)}</p>`);
        }
    }

    // Escape HTML helper
    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // Input Bar Listeners
    if (btnChatSend) {
        btnChatSend.addEventListener("click", () => {
            if (chatTextInput) sendChatQuery(chatTextInput.value);
        });
    }

    if (chatTextInput) {
        chatTextInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                sendChatQuery(chatTextInput.value);
            }
        });
    }

    // Quick Prompts Event Delegation
    if (chatQuickPrompts) {
        chatQuickPrompts.addEventListener("click", (e) => {
            const chip = e.target.closest(".prompt-chip");
            if (chip && chip.dataset.query) {
                sendChatQuery(chip.dataset.query);
            }
        });
    }

    // Explain Active Result Button Listener
    if (btnExplainActive) {
        btnExplainActive.addEventListener("click", () => {
            sendChatQuery("Explain this upscaled product image result");
        });
    }

    // =================================================================
    // SPEECH RECOGNITION (VOICE INPUT - STT)
    // =================================================================
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = false;
        recognitionInstance.interimResults = false;

        recognitionInstance.onstart = () => {
            isSpeechRecording = true;
            if (btnVoiceRecord) btnVoiceRecord.classList.add("recording");
            if (voiceStatusBar) {
                voiceStatusBar.style.display = "flex";
                const locales = { en: "English", te: "తెలుగు (Telugu)", hi: "हिंदी (Hindi)" };
                if (voiceStatusText) voiceStatusText.textContent = `Listening in ${locales[currentChatLang] || 'English'}... Speak now`;
            }
        };

        recognitionInstance.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log("[STT Recognized]:", transcript);
            if (chatTextInput) chatTextInput.value = transcript;
            sendChatQuery(transcript);
        };

        recognitionInstance.onerror = (event) => {
            console.warn("[STT Error]:", event.error);
            stopSpeechRecording();
        };

        recognitionInstance.onend = () => {
            stopSpeechRecording();
        };
    } else {
        if (btnVoiceRecord) {
            btnVoiceRecord.title = "Voice recognition not supported in this browser (Web Speech API)";
            btnVoiceRecord.style.opacity = "0.5";
        }
    }

    function startSpeechRecording() {
        if (!recognitionInstance) {
            alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
            return;
        }
        const langCodes = { en: "en-US", te: "te-IN", hi: "hi-IN" };
        recognitionInstance.lang = langCodes[currentChatLang] || "en-US";
        try {
            recognitionInstance.start();
        } catch (e) {
            console.warn("Speech recognition start warning:", e);
        }
    }

    function stopSpeechRecording() {
        isSpeechRecording = false;
        if (btnVoiceRecord) btnVoiceRecord.classList.remove("recording");
        if (voiceStatusBar) voiceStatusBar.style.display = "none";
        try {
            if (recognitionInstance) recognitionInstance.stop();
        } catch (e) {}
    }

    if (btnVoiceRecord) {
        btnVoiceRecord.addEventListener("click", () => {
            if (!isSpeechRecording) {
                startSpeechRecording();
            } else {
                stopSpeechRecording();
            }
        });
    }

    // =================================================================
    // SPEECH SYNTHESIS (VOICE OUTPUT - TTS)
    // =================================================================
    function speakText(text, lang = "en", buttonElem = null) {
        if (!("speechSynthesis" in window)) {
            alert("Text-to-speech is not supported in this browser.");
            return;
        }

        // If currently speaking, stop
        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
            if (currentSpeechButton) {
                currentSpeechButton.classList.remove("playing");
                currentSpeechButton.innerHTML = '<i class="fa-solid fa-volume-high"></i> Listen';
                currentSpeechButton = null;
            }
            if (buttonElem && buttonElem === currentSpeechButton) {
                return;
            }
        }

        if (!text) return;

        const utterance = new SpeechSynthesisUtterance(text);
        const langLocales = { en: "en-US", te: "te-IN", hi: "hi-IN" };
        utterance.lang = langLocales[lang] || "en-US";
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        // Try to match voice with locale
        const voices = window.speechSynthesis.getVoices();
        const matchedVoice = voices.find(v => v.lang.startsWith(langLocales[lang].substring(0, 2)));
        if (matchedVoice) {
            utterance.voice = matchedVoice;
        }

        if (buttonElem) {
            currentSpeechButton = buttonElem;
            buttonElem.classList.add("playing");
            buttonElem.innerHTML = '<i class="fa-solid fa-stop"></i> Stop';
        }

        utterance.onend = () => {
            if (buttonElem) {
                buttonElem.classList.remove("playing");
                buttonElem.innerHTML = '<i class="fa-solid fa-volume-high"></i> Listen';
            }
            currentSpeechButton = null;
        };

        utterance.onerror = () => {
            if (buttonElem) {
                buttonElem.classList.remove("playing");
                buttonElem.innerHTML = '<i class="fa-solid fa-volume-high"></i> Listen';
            }
            currentSpeechButton = null;
        };

        window.speechSynthesis.speak(utterance);
    }

    // Delegated click listener for Listen buttons
    if (chatMessages) {
        chatMessages.addEventListener("click", (e) => {
            const btn = e.target.closest(".btn-speech-play");
            if (btn && btn.dataset.speech) {
                speakText(btn.dataset.speech, currentChatLang, btn);
            }
        });
    }

    // =================================================================
    // MOUSE MOVE ANIMATION (from panwar8279/Mousemove-animation)
    // https://mousemove-animation.vercel.app/
    // =================================================================
    const animBody = document.body;
    let lastMouseMoveTs = 0;

    function cursorStyle(e) {
        const now = Date.now();
        if (now - lastMouseMoveTs < 16) return;
        lastMouseMoveTs = now;

        const cursor = document.createElement('div');
        cursor.setAttribute('class', 'swipe');
        cursor.setAttribute('style', `left: ${e.clientX - 10}px; top: ${e.clientY - 10}px;`);

        cursor.onanimationend = () => {
            cursor.remove();
        };
        setTimeout(() => {
            if (cursor && cursor.parentNode) cursor.remove();
        }, 650);

        animBody.insertAdjacentElement('beforeend', cursor);
    }

    document.addEventListener('mousemove', cursorStyle);
    document.addEventListener('click', (e) => {
        const cursor = document.createElement('div');
        cursor.setAttribute('class', 'swipe');
        cursor.setAttribute('style', `left: ${e.clientX - 10}px; top: ${e.clientY - 10}px;`);
        cursor.onanimationend = () => cursor.remove();
        setTimeout(() => {
            if (cursor && cursor.parentNode) cursor.remove();
        }, 650);
        animBody.insertAdjacentElement('beforeend', cursor);
    });

    function touchStyle(e) {
        if (!e.touches || !e.touches[0]) return;
        const now = Date.now();
        if (now - lastMouseMoveTs < 22) return;
        lastMouseMoveTs = now;

        const cursor = document.createElement('div');
        cursor.setAttribute('class', 'swipe');
        cursor.setAttribute('style', `left: ${e.touches[0].clientX - 10}px; top: ${e.touches[0].clientY - 10}px;`);

        cursor.onanimationend = () => {
            cursor.remove();
        };
        setTimeout(() => {
            if (cursor && cursor.parentNode) cursor.remove();
        }, 650);

        animBody.insertAdjacentElement('beforeend', cursor);
    }

    document.addEventListener('touchmove', touchStyle, { passive: true });
});
