"""
Locust Concurrent User Load Testing Suite for NU_AI_CHAT_BOT
Tests endpoints:
1. Static / Health checks (instant)
2. Student Chat UI (/chat)
3. Cached FAQ & Preloaded Instant Responses (<1ms)
4. Notice Filter Service Queries
5. Token Public Status Lookup
"""
import random
from locust import HttpUser, task, between

SAMPLE_QUERIES = [
    "hello",
    "what can you do?",
    "অনার্স ১ম বর্ষের ভর্তি কবে শুরু?",
    "সর্বশেষ নোটিশ দেখান",
    "Recent notices",
    "ডিগ্রি ফরম পূরণের নিয়ম কি?",
    "অনলাইনে সার্টিফিকেট তোলার নিয়ম কি?",
    "NU-2026-000001",
    "LLB formfillup notice",
    "পরীক্ষার রুটিন কবে দিবে?",
    "আসসালামু আলাইকুম"
]

class StudentChatUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def test_student_ui(self):
        self.client.get("/chat")

    @task(5)
    def test_instant_chat(self):
        query = random.choice(SAMPLE_QUERIES)
        payload = {
            "message": query,
            "history": [],
            "session_id": f"locust_user_{random.randint(1, 1000)}"
        }
        self.client.post("/api/v1/chat", json=payload, name="/api/v1/chat [Mixed Workload]")

    @task(2)
    def test_legacy_chat(self):
        payload = {
            "message": "hello",
            "history": [],
            "session_id": "legacy_locust_user"
        }
        self.client.post("/api/chat", json=payload, name="/api/chat [Legacy Fast Path]")

    @task(1)
    def test_widget_asset(self):
        self.client.get("/static/nu-chat-widget.js")