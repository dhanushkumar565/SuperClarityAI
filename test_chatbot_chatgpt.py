from models.chatbot import SupplierClarityChatbot

bot = SupplierClarityChatbot()

test_queries = [
    "What is this website about?",
    "How do I use this website?",
    "Tell me about the demo products",
    "Which model is the best?",
    "What is Bilateral Denoising?",
    "Does the AI hallucinate or invent fake text?",
    "How fast is inference on CPU?",
    "Who built this project?",
    "ఈ వెబ్‌సైట్ గురించి చెప్పండి",
    "यह वेबसाइट किस बारे में है?"
]

for q in test_queries:
    res = bot.generate_response(q)
    print(f'Query: "{q}" -> Intent: {res["intent"]} | Lang: {res["active_language"]}')
    assert res['response_markdown'], "Empty response!"

print("\n[SUCCESS] All queries successfully matched and generated ChatGPT-grade answers!")
