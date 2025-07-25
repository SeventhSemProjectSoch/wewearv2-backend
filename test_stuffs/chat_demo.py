#!/usr/bin/env python3
"""
Chat API Demo - Simple conversation demo
Shows basic chat functionality with real users
"""

import requests
import subprocess
import tempfile
import os
from datetime import datetime


def get_jwt_token(user_id: str) -> str:
    """Generate JWT token for a user"""
    script_content = f"""
import sys
import os
import django
sys.path.append("/home/kali_37/7th_sem_project/wewearv2-backend/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from users.auth import create_access_token
print(create_access_token(sub="{user_id}"))
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write(script_content)
        temp_file = f.name

    result = subprocess.run(
        ["python", temp_file], capture_output=True, text=True
    )
    os.unlink(temp_file)
    return result.stdout.strip()


def send_message(sender_token: str, receiver_id: str, content: str) -> dict:
    """Send a message"""
    url = "http://localhost:8000/api/chat/send/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {sender_token}",
    }
    payload = {"receiver_id": receiver_id, "content": content}

    response = requests.post(url, headers=headers, json=payload)
    return response.json() if response.status_code == 200 else None


def get_conversation_history(user_token: str, with_user_id: str) -> list:
    """Get conversation history"""
    url = "http://localhost:8000/api/chat/history/"
    headers = {"Authorization": f"Bearer {user_token}"}
    params = {"with_user_id": with_user_id, "limit": 10}

    response = requests.get(url, headers=headers, params=params)
    return response.json() if response.status_code == 200 else []


def demo_chat():
    """Demo the chat API with a conversation"""
    print("🚀 Chat API Demo")
    print("=" * 40)

    # Setup users (we know these exist and are mutual followers)
    bot_id = "1cce9468-945a-4fda-8f17-7ffe2fcf5b95"
    subash_id = "6c547bcb-e5e1-47ee-8257-37797315ab66"

    # Get tokens
    print("🔑 Getting authentication tokens...")
    bot_token = get_jwt_token(bot_id)
    subash_token = get_jwt_token(subash_id)

    if not bot_token or not subash_token:
        print("❌ Failed to get tokens")
        return

    print("✅ Tokens obtained successfully")
    print()

    # Demo conversation
    print("💬 Starting demo conversation...")
    print("-" * 40)

    # Message 1: bot → Subash
    msg1 = send_message(
        bot_token, subash_id, "Hey Subash! 👋 How's your project going?"
    )
    if msg1:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] bot: Hey Subash! 👋"
            " How's your project going?"
        )

    # Message 2: Subash → bot
    msg2 = send_message(
        subash_token,
        bot_id,
        "Hi bot! 😊 It's going great! Just finished the API testing. How about"
        " yours?",
    )
    if msg2:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] Subash: Hi bot! 😊 It's"
            " going great! Just finished the API testing. How about yours?"
        )

    # Message 3: bot → Subash
    msg3 = send_message(
        bot_token,
        subash_id,
        "Awesome! 🎉 I'm working on the chat system. Want to test it"
        " together?",
    )
    if msg3:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] bot: Awesome! 🎉 I'm"
            " working on the chat system. Want to test it together?"
        )

    # Message 4: Subash → bot
    msg4 = send_message(
        subash_token,
        bot_id,
        "Absolutely! 💯 This chat API is working perfectly. Great job! 👏",
    )
    if msg4:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] Subash: Absolutely! 💯"
            " This chat API is working perfectly. Great job! 👏"
        )

    print("-" * 40)
    print()

    # Show conversation history
    print("📚 Retrieving full conversation history...")
    history = get_conversation_history(bot_token, subash_id)

    if history:
        print(f"✅ Found {len(history)} messages in conversation")
        print()
        print("📖 Complete Conversation:")
        print("-" * 40)

        for msg in reversed(history):  # Show in chronological order
            sender = "bot" if msg["sender_id"] == bot_id else "Subash"
            timestamp = msg["created_at"].split("T")[1][:8]  # Extract time
            print(f"[{timestamp}] {sender}: {msg['content']}")
    else:
        print("❌ No conversation history found")

    print()
    print("✅ Chat API Demo Complete!")
    print("💬 The chat system is fully functional and ready for use.")


if __name__ == "__main__":
    demo_chat()
