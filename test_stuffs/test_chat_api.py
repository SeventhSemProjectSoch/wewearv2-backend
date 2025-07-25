#!/usr/bin/env python3
"""
Comprehensive Chat API Test Suite
Tests all chat-related endpoints with available users
"""

import requests
import json
import os
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class TestUser:
    id: str
    username: str
    email: str
    token: str = ""


class ChatAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.users: List[TestUser] = []
        self.messages: List[Dict[str, Any]] = []

    def setup_test_users(self):
        """Setup test users with authentication tokens"""
        print("🔧 Setting up test users...")

        # Use the users we know exist from the database
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
            {
                "id": "0cb3e34c-24e9-4245-a9e3-ad631f07783e",
                "username": "yajyoo1999",
                "email": "yajyoo1999@simulated.com",
            },
            {
                "id": "c85ee438-2a73-41a3-a45e-b62ea5fdc4ee",
                "username": "adamgonon",
                "email": "adamgonon@simulated.com",
            },
        ]

        for user_data in test_users_data:
            # Get JWT token for each user
            token_response = self._get_jwt_token(user_data["id"])
            if token_response:
                user = TestUser(
                    id=user_data["id"],
                    username=user_data["username"],
                    email=user_data["email"],
                    token=token_response,
                )
                self.users.append(user)
                print(f"✅ Setup user: {user.username} ({user.email})")
            else:
                print(
                    f"❌ Failed to get token for user: {user_data['username']}"
                )

        print(
            f"✅ Setup complete: {len(self.users)} users ready for testing\n"
        )

    def _get_jwt_token(self, user_id: str) -> str:
        """Generate JWT token for a user (simulating the auth system)"""
        try:
            # This simulates the token generation - in real scenario you'd call the auth endpoint
            import subprocess
            import tempfile

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

            # Clean up
            os.unlink(temp_file)

            return token if token else ""
        except Exception as e:
            print(f"Error generating token: {e}")
            return ""

    def test_send_message(self):
        """Test sending messages between users"""
        print("📤 Testing message sending...")

        if len(self.users) < 2:
            print("❌ Need at least 2 users for message testing")
            return False

        sender = self.users[0]
        receiver = self.users[1]

        # Test 1: Send a message
        url = f"{self.base_url}/api/chat/send/"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {sender.token}",
        }
        payload = {
            "receiver_id": receiver.id,
            "content": (
                f"Hello {receiver.username}! This is a test message from"
                f" {sender.username}."
            ),
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                message_data = response.json()
                self.messages.append(message_data)
                print(f"✅ Message sent successfully:")
                print(f"   From: {sender.username} → To: {receiver.username}")
                print(f"   Content: {payload['content']}")
                print(f"   Message ID: {message_data['id']}")

                # Test 2: Send reply
                reply_payload = {
                    "receiver_id": sender.id,
                    "content": (
                        f"Hey {sender.username}! Got your message, replying"
                        " back!"
                    ),
                }
                reply_headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {receiver.token}",
                }

                reply_response = requests.post(
                    url, headers=reply_headers, json=reply_payload
                )
                if reply_response.status_code == 200:
                    reply_data = reply_response.json()
                    self.messages.append(reply_data)
                    print(f"✅ Reply sent successfully:")
                    print(
                        f"   From: {receiver.username} → To: {sender.username}"
                    )
                    print(f"   Message ID: {reply_data['id']}")
                else:
                    print(
                        f"❌ Reply failed: {reply_response.status_code} -"
                        f" {reply_response.text}"
                    )

                return True
            else:
                print(
                    f"❌ Send message failed: {response.status_code} -"
                    f" {response.text}"
                )
                return False

        except Exception as e:
            print(f"❌ Send message error: {e}")
            return False

    def test_conversation_history(self):
        """Test retrieving conversation history"""
        print("\n📚 Testing conversation history...")

        if len(self.users) < 2:
            print("❌ Need at least 2 users for history testing")
            return False

        user1 = self.users[0]
        user2 = self.users[1]

        # Test conversation history from user1's perspective
        url = f"{self.base_url}/api/chat/history/"
        headers = {"Authorization": f"Bearer {user1.token}"}
        params = {"with_user_id": user2.id, "limit": 10}

        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                messages = response.json()
                print(
                    f"✅ Retrieved {len(messages)} messages in conversation:"
                )
                for msg in messages:
                    sender_name = (
                        user1.username
                        if msg["sender_id"] == user1.id
                        else user2.username
                    )
                    print(
                        f"   [{msg['created_at']}] {sender_name}:"
                        f" {msg['content'][:50]}..."
                    )

                # Test from user2's perspective
                headers2 = {"Authorization": f"Bearer {user2.token}"}
                params2 = {"with_user_id": user1.id, "limit": 10}

                response2 = requests.get(url, headers=headers2, params=params2)
                if response2.status_code == 200:
                    messages2 = response2.json()
                    print(
                        "✅ Same conversation from other user's view:"
                        f" {len(messages2)} messages"
                    )
                    return len(messages) == len(
                        messages2
                    )  # Should be the same
                else:
                    print(
                        "❌ History from user2 failed:"
                        f" {response2.status_code}"
                    )
                    return False
            else:
                print(
                    f"❌ History retrieval failed: {response.status_code} -"
                    f" {response.text}"
                )
                return False

        except Exception as e:
            print(f"❌ History retrieval error: {e}")
            return False

    def test_conversations_list(self):
        """Test listing all conversations for a user"""
        print("\n💬 Testing conversations list...")

        if not self.users:
            print("❌ No users available for testing")
            return False

        user = self.users[0]
        url = f"{self.base_url}/api/chat/conversations/"
        headers = {"Authorization": f"Bearer {user.token}"}

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                conversations = response.json()
                print(
                    f"✅ User {user.username} has"
                    f" {len(conversations)} conversations:"
                )
                for conv in conversations:
                    print(
                        f"   → {conv['username']}:"
                        f" {conv['last_message'][:50]}..."
                    )
                    print(f"     Last activity: {conv['last_timestamp']}")
                return True
            else:
                print(
                    f"❌ Conversations list failed: {response.status_code} -"
                    f" {response.text}"
                )
                return False

        except Exception as e:
            print(f"❌ Conversations list error: {e}")
            return False

    def test_multiple_users_conversation(self):
        """Test conversation between multiple users"""
        print("\n👥 Testing multi-user conversations...")

        if len(self.users) < 3:
            print("❌ Need at least 3 users for multi-user testing")
            return False

        # Create a chain of messages: user1 → user2 → user3 → user1
        messages_to_send = [
            (0, 1, "Hey user 2, starting a conversation chain!"),
            (1, 2, "Hi user 3, user 1 just messaged me. Passing it along!"),
            (2, 0, "Got the message! Completing the circle back to user 1."),
        ]

        url = f"{self.base_url}/api/chat/send/"
        success_count = 0

        for sender_idx, receiver_idx, content in messages_to_send:
            sender = self.users[sender_idx]
            receiver = self.users[receiver_idx]

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {sender.token}",
            }
            payload = {"receiver_id": receiver.id, "content": content}

            try:
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    success_count += 1
                    print(
                        f"✅ {sender.username} → {receiver.username}: Message"
                        " sent"
                    )
                else:
                    print(
                        f"❌ {sender.username} → {receiver.username}: Failed"
                        f" ({response.status_code})"
                    )
            except Exception as e:
                print(
                    f"❌ Error sending from {sender.username} to"
                    f" {receiver.username}: {e}"
                )

        return success_count == len(messages_to_send)

    def test_error_cases(self):
        """Test error handling scenarios"""
        print("\n🚨 Testing error cases...")

        if not self.users:
            print("❌ No users available for error testing")
            return False

        user = self.users[0]
        tests_passed = 0
        total_tests = 0

        # Test 1: Invalid receiver ID
        total_tests += 1
        url = f"{self.base_url}/api/chat/send/"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {user.token}",
        }
        payload = {
            "receiver_id": "invalid-uuid-format",
            "content": "This should fail",
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 400:
                tests_passed += 1
                print("✅ Invalid UUID format properly rejected")
            else:
                print(
                    "❌ Invalid UUID should return 400, got"
                    f" {response.status_code}"
                )
        except Exception as e:
            print(f"❌ Error testing invalid UUID: {e}")

        # Test 2: Non-existent receiver
        total_tests += 1
        payload = {
            "receiver_id": (
                "12345678-1234-1234-1234-123456789012"
            ),  # Valid format but non-existent
            "content": "This should fail too",
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 404:
                tests_passed += 1
                print("✅ Non-existent user properly rejected")
            else:
                print(
                    "❌ Non-existent user should return 404, got"
                    f" {response.status_code}"
                )
        except Exception as e:
            print(f"❌ Error testing non-existent user: {e}")

        # Test 3: Invalid token
        total_tests += 1
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid-token",
        }
        payload = {
            "receiver_id": user.id,
            "content": "This should fail due to auth",
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 401:
                tests_passed += 1
                print("✅ Invalid token properly rejected")
            else:
                print(
                    "❌ Invalid token should return 401, got"
                    f" {response.status_code}"
                )
        except Exception as e:
            print(f"❌ Error testing invalid token: {e}")

        return tests_passed == total_tests

    def run_all_tests(self):
        """Run all chat API tests"""
        print("🚀 Starting Chat API Test Suite")
        print("=" * 50)

        # Setup
        self.setup_test_users()

        if not self.users:
            print("❌ No users available - cannot run tests")
            return

        # Run tests
        tests = [
            ("Message Sending", self.test_send_message),
            ("Conversation History", self.test_conversation_history),
            ("Conversations List", self.test_conversations_list),
            (
                "Multi-User Conversations",
                self.test_multiple_users_conversation,
            ),
            ("Error Handling", self.test_error_cases),
        ]

        results = {}
        for test_name, test_func in tests:
            print(f"\n{'-' * 30}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False

        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<25} {status}")

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Chat API is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")


def main():
    """Run the chat API tests"""
    import os

    # Make sure Django is set up
    if "DJANGO_SETTINGS_MODULE" not in os.environ:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    tester = ChatAPITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
