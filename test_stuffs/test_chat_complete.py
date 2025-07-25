#!/usr/bin/env python3
"""
Complete Chat API Test with Follow Relationship Setup
Tests all chat functionality with automatic follow setup
"""

import requests
import json
import os
import subprocess
import tempfile
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class TestUser:
    id: str
    username: str
    email: str
    token: str = ""


class CompleteChatAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.users: List[TestUser] = []

    def setup_test_users_and_follows(self):
        """Setup test users and their mutual follow relationships"""
        print("🔧 Setting up test users and follow relationships...")

        # Select users for testing
        test_users_data = [
            {
                "id": "1cce9468-945a-4fda-8f17-7ffe2fcf5b95",
                "username": "bot",
                "email": "b@b.com",
            },
            {
                "id": "6c547bcb-e5e1-47ee-8257-37797315ab66",
                "username": "Subash",
                "email": "email@gmail.com",
            },
            {
                "id": "a6d75bf2-e3c0-41f5-9a20-f2a54e9dc22a",
                "username": "devanondeck",
                "email": "devanondeck@simulated.com",
            },
        ]

        # Setup users with tokens
        for user_data in test_users_data:
            token = self._get_jwt_token(user_data["id"])
            if token:
                user = TestUser(
                    id=user_data["id"],
                    username=user_data["username"],
                    email=user_data["email"],
                    token=token,
                )
                self.users.append(user)
                print(f"✅ Setup user: {user.username}")

        # Create mutual follow relationships
        if len(self.users) >= 2:
            self._setup_follow_relationships()

        print(
            f"✅ Setup complete: {len(self.users)} users ready for testing\\n"
        )

    def _get_jwt_token(self, user_id: str) -> str:
        """Generate JWT token for a user"""
        try:
            script_content = f"""
import sys
import os
import django
sys.path.append("/home/kali_37/7th_sem_project/wewearv2-backend/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from users.auth import create_access_token
token = create_access_token(sub="{user_id}")
print(token)
"""

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as f:
                f.write(script_content)
                temp_file = f.name

            result = subprocess.run(
                ["python", temp_file], capture_output=True, text=True
            )
            token = result.stdout.strip()
            os.unlink(temp_file)

            return token if token else ""
        except Exception as e:
            print(f"Error generating token: {e}")
            return ""

    def _setup_follow_relationships(self):
        """Create mutual follow relationships between all test users"""
        print("🤝 Creating mutual follow relationships...")

        script_content = f"""
import sys
import os
import django
sys.path.append("/home/kali_37/7th_sem_project/wewearv2-backend/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from users.models import User
from content.models import Follow

user_ids = {[user.id for user in self.users]}

for i, user1_id in enumerate(user_ids):
    for j, user2_id in enumerate(user_ids):
        if i != j:
            user1 = User.objects.get(id=user1_id)
            user2 = User.objects.get(id=user2_id)
            Follow.objects.get_or_create(follower=user1, following=user2)

print("Follow relationships created")
"""

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as f:
                f.write(script_content)
                temp_file = f.name

            result = subprocess.run(
                ["python", temp_file], capture_output=True, text=True
            )
            os.unlink(temp_file)
            print("✅ Mutual follow relationships established")
        except Exception as e:
            print(f"❌ Error setting up follows: {e}")

    def test_chat_flow(self):
        """Test complete chat flow between users"""
        print("💬 Testing complete chat flow...")

        if len(self.users) < 2:
            print("❌ Need at least 2 users for chat testing")
            return False

        user1, user2 = self.users[0], self.users[1]

        # Step 1: Send initial message
        print(
            f"📤 Step 1: {user1.username} sending message to {user2.username}"
        )
        message1 = self._send_message(
            user1, user2, f"Hi {user2.username}! How are you doing?"
        )
        if not message1:
            return False

        # Step 2: Send reply
        print(f"📤 Step 2: {user2.username} replying to {user1.username}")
        message2 = self._send_message(
            user2,
            user1,
            f"Hey {user1.username}! I'm doing great, thanks for asking!",
        )
        if not message2:
            return False

        # Step 3: Continue conversation
        print(f"📤 Step 3: {user1.username} continuing conversation")
        message3 = self._send_message(
            user1, user2, "That's awesome! Want to grab coffee sometime?"
        )
        if not message3:
            return False

        # Step 4: Get conversation history
        print("📚 Step 4: Retrieving conversation history")
        history = self._get_conversation_history(user1, user2)
        if history is None:
            return False

        print(f"✅ Retrieved {len(history)} messages in conversation")
        for i, msg in enumerate(reversed(history), 1):
            sender = (
                user1.username
                if msg["sender_id"] == user1.id
                else user2.username
            )
            print(f"   {i}. {sender}: {msg['content']}")

        # Step 5: Check conversations list
        print("📋 Step 5: Checking conversations list")
        conversations = self._get_conversations_list(user1)
        if conversations is None:
            return False

        print(
            f"✅ {user1.username} has {len(conversations)} active"
            " conversations"
        )

        return True

    def _send_message(
        self, sender: TestUser, receiver: TestUser, content: str
    ) -> dict:
        """Send a message between two users"""
        url = f"{self.base_url}/api/chat/send/"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {sender.token}",
        }
        payload = {"receiver_id": receiver.id, "content": content}

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                message_data = response.json()
                print(f"   ✅ Message sent (ID: {message_data['id']})")
                return message_data
            else:
                print(
                    f"   ❌ Failed to send message: {response.status_code} -"
                    f" {response.text}"
                )
                return None
        except Exception as e:
            print(f"   ❌ Error sending message: {e}")
            return None

    def _get_conversation_history(
        self, user1: TestUser, user2: TestUser
    ) -> list:
        """Get conversation history between two users"""
        url = f"{self.base_url}/api/chat/history/"
        headers = {"Authorization": f"Bearer {user1.token}"}
        params = {"with_user_id": user2.id, "limit": 20}

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f"   ❌ Failed to get history: {response.status_code} -"
                    f" {response.text}"
                )
                return None
        except Exception as e:
            print(f"   ❌ Error getting history: {e}")
            return None

    def _get_conversations_list(self, user: TestUser) -> list:
        """Get list of all conversations for a user"""
        url = f"{self.base_url}/api/chat/conversations/"
        headers = {"Authorization": f"Bearer {user.token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    "   ❌ Failed to get conversations:"
                    f" {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            print(f"   ❌ Error getting conversations: {e}")
            return None

    def test_multi_user_scenario(self):
        """Test scenario with multiple users"""
        print("\\n👥 Testing multi-user chat scenario...")

        if len(self.users) < 3:
            print("❌ Need at least 3 users for multi-user testing")
            return False

        user1, user2, user3 = self.users[0], self.users[1], self.users[2]

        # Create a group chat scenario
        scenarios = [
            (
                user1,
                user2,
                f"Hey {user2.username}, did you see the new project update?",
            ),
            (
                user2,
                user1,
                (
                    f"Yes {user1.username}! It looks amazing. Have you told"
                    f" {user3.username}?"
                ),
            ),
            (
                user1,
                user3,
                (
                    f"Hi {user3.username}! Check out the new project update"
                    " when you get a chance."
                ),
            ),
            (
                user3,
                user1,
                f"Thanks {user1.username}! I'll take a look right now.",
            ),
            (
                user3,
                user2,
                (
                    f"Hey {user2.username}, {user1.username} told me about the"
                    " update. What do you think?"
                ),
            ),
            (
                user2,
                user3,
                (
                    f"I think it's great {user3.username}! We should discuss"
                    " it more."
                ),
            ),
        ]

        success_count = 0
        for sender, receiver, message in scenarios:
            if self._send_message(sender, receiver, message):
                success_count += 1

        print(
            f"✅ Sent {success_count}/{len(scenarios)} messages successfully"
        )

        # Check that each user has conversations
        for user in [user1, user2, user3]:
            conversations = self._get_conversations_list(user)
            if conversations is not None:
                print(
                    f"   {user.username} has"
                    f" {len(conversations)} conversations"
                )

        return success_count == len(scenarios)

    def run_complete_test(self):
        """Run the complete chat API test"""
        print("🚀 Starting Complete Chat API Test")
        print("=" * 50)

        # Setup
        self.setup_test_users_and_follows()

        if len(self.users) < 2:
            print("❌ Insufficient users for testing")
            return

        # Run main tests
        tests_passed = 0
        total_tests = 2

        if self.test_chat_flow():
            tests_passed += 1
            print("✅ Chat flow test PASSED")
        else:
            print("❌ Chat flow test FAILED")

        if self.test_multi_user_scenario():
            tests_passed += 1
            print("✅ Multi-user scenario test PASSED")
        else:
            print("❌ Multi-user scenario test FAILED")

        # Summary
        print("\\n" + "=" * 50)
        print("📊 FINAL RESULTS")
        print("=" * 50)
        print(f"Tests passed: {tests_passed}/{total_tests}")

        if tests_passed == total_tests:
            print("🎉 All chat API tests passed successfully!")
            print("💬 Chat system is fully functional and ready for use.")
        else:
            print("⚠️ Some tests failed. Please check the output above.")


def main():
    """Run the complete chat API test"""
    tester = CompleteChatAPITester()
    tester.run_complete_test()


if __name__ == "__main__":
    main()
