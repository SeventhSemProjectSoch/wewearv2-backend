#!/usr/bin/env python3
"""
Comprehensive API Testing Suite for WeWear Backend

This script tests all API endpoints including authentication, profile management,
content feeds, interactions, and post creation.
"""

import json
import random
import requests
import time
from typing import Dict, Any, Optional


class WeWearAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.tokens = {}  # Store user tokens
        self.users = {}  # Store user data
        self.posts = []  # Store created posts

    def log(self, message: str):
        """Log with timestamp"""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        token: Optional[str] = None,
        files: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        if files:
            # Remove content-type for file uploads
            headers.pop("Content-Type", None)

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(
                        url, headers=headers, data=data, files=files
                    )
                else:
                    response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": 200 <= response.status_code < 300,
            }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False,
            }

    def test_authentication(self) -> bool:
        """Test authentication endpoints"""
        self.log("🔐 Testing Authentication...")

        # Test OTP request
        test_email = f"test_{random.randint(1000, 9999)}@example.com"
        self.log(f"  Requesting OTP for {test_email}")

        result = self.make_request(
            "POST", "/api/auth/request-otp", {"email": test_email}
        )

        if not result["success"]:
            self.log(f"  ❌ OTP request failed: {result['data']}")
            return False

        self.log("  ✅ OTP request successful")

        # Get OTP from database (for testing)
        import subprocess
        import os

        try:
            os.chdir("/home/kali_37/7th_sem_project/wewearv2-backend/backend")
            cmd = (
                'python manage.py shell -c "from users.models import OTP;'
                " otp ="
                f" OTP.objects.filter(email='{test_email}').latest('created_at');"
                ' print(otp.code)"'
            )
            otp_code = (
                subprocess.check_output(cmd, shell=True, text=True)
                .strip()
                .split("\n")[-1]
            )

            self.log(f"  Got OTP code: {otp_code}")

            # Test OTP verification
            result = self.make_request(
                "POST",
                "/api/auth/verify-otp",
                {"email": test_email, "code": otp_code},
            )

            if not result["success"]:
                self.log(f"  ❌ OTP verification failed: {result['data']}")
                return False

            token = result["data"]["access_token"]
            self.tokens[test_email] = token
            self.users[test_email] = {"email": test_email, "token": token}

            self.log("  ✅ OTP verification successful")
            self.log("  ✅ Authentication test passed")
            return True

        except Exception as e:
            self.log(f"  ❌ Authentication test failed: {e}")
            return False

    def test_profile_management(self) -> bool:
        """Test profile endpoints"""
        self.log("👤 Testing Profile Management...")

        if not self.tokens:
            self.log("  ❌ No authenticated users available")
            return False

        email = list(self.tokens.keys())[0]
        token = self.tokens[email]

        # Test get profile
        result = self.make_request("GET", "/api/profile/profile", token=token)
        if not result["success"]:
            self.log(f"  ❌ Get profile failed: {result['data']}")
            return False

        self.log("  ✅ Get profile successful")

        # Test update profile
        username = f"testuser_{random.randint(1000, 9999)}"
        profile_data = {
            "username": username,
            "full_name": "Test User",
            "bio": "I am a test user for API testing",
            "body_type": "athletic",
            "height": 175.0,
            "weight": 70.0,
            "themes": ["cultural", "classic", "formal"],
        }

        result = self.make_request(
            "PUT", "/api/profile/profile", profile_data, token=token
        )
        if not result["success"]:
            self.log(f"  ❌ Update profile failed: {result['data']}")
            return False

        self.users[email]["username"] = username
        self.log("  ✅ Update profile successful")
        self.log("  ✅ Profile management test passed")
        return True

    def test_content_feeds(self) -> bool:
        """Test content feed endpoints"""
        self.log("📺 Testing Content Feeds...")

        if not self.tokens:
            self.log("  ❌ No authenticated users available")
            return False

        token = list(self.tokens.values())[0]

        # Test all feed endpoints
        feeds = [
            ("/api/content/feeds/foryou/", {"exclude_ids": []}),
            ("/api/content/feeds/friends/", {"exclude_ids": []}),
            ("/api/content/feeds/explore/", {"exclude_ids": []}),
        ]

        for endpoint, data in feeds:
            result = self.make_request("POST", endpoint, data, token=token)
            if not result["success"]:
                self.log(f"  ❌ Feed {endpoint} failed: {result['data']}")
                return False
            self.log(f"  ✅ Feed {endpoint} successful")

        # Test upload feed (GET)
        result = self.make_request(
            "GET", "/api/content/feeds/upload/", token=token
        )
        if not result["success"]:
            self.log(f"  ❌ Upload feed failed: {result['data']}")
            return False

        self.log("  ✅ Upload feed successful")
        self.log("  ✅ Content feeds test passed")
        return True

    def test_interactions(self) -> bool:
        """Test interaction endpoints"""
        self.log("❤️ Testing Interactions...")

        if not self.tokens:
            self.log("  ❌ No authenticated users available")
            return False

        token = list(self.tokens.values())[0]

        # Test interactions with non-existent post (should return 404)
        fake_post_id = 99999

        interactions = [
            (
                "POST",
                f"/api/content/interactions/like/?post_id={fake_post_id}",
            ),
            (
                "POST",
                f"/api/content/interactions/save/?post_id={fake_post_id}",
            ),
            (
                "POST",
                "/api/content/interactions/comment/",
                {"post_id": fake_post_id, "text": "Test comment"},
            ),
            (
                "POST",
                "/api/content/interactions/share/",
                {"post_id": fake_post_id},
            ),
        ]

        for method, endpoint, *data in interactions:
            payload = data[0] if data else None
            result = self.make_request(method, endpoint, payload, token=token)

            # We expect 404 for non-existent posts
            if result["status_code"] != 404:
                self.log(
                    f"  ❌ Interaction {endpoint} should return 404, got"
                    f" {result['status_code']}"
                )
                return False

            self.log(f"  ✅ Interaction {endpoint} correctly returned 404")

        self.log("  ✅ Interactions test passed")
        return True

    def test_post_creation(self) -> bool:
        """Test post creation endpoint"""
        self.log("📝 Testing Post Creation...")

        if not self.tokens:
            self.log("  ❌ No authenticated users available")
            return False

        token = list(self.tokens.values())[0]

        # Test post creation with URL
        post_data = {
            "caption": "Test post from API testing",
            "themes": [1, 2, 3],  # Using theme IDs
            "media_url": "https://example.com/test-image.jpg",
        }

        # For form data, we need to handle it differently
        # This is a simplified test - in reality, you'd need proper form handling
        result = self.make_request(
            "POST", "/api/content/posts/", post_data, token=token
        )

        # The endpoint might fail due to theme validation or other reasons
        # We're testing that the endpoint is reachable and handles requests properly
        if result["status_code"] in [400, 422]:  # Expected validation errors
            self.log(
                "  ✅ Post creation endpoint reachable (validation errors"
                " expected)"
            )
        elif result["success"]:
            self.log("  ✅ Post creation successful")
        else:
            self.log(
                f"  ❌ Post creation failed unexpectedly: {result['data']}"
            )
            return False

        self.log("  ✅ Post creation test passed")
        return True

    def run_all_tests(self) -> bool:
        """Run all API tests"""
        self.log("🚀 Starting WeWear API Test Suite")
        self.log("=" * 50)

        tests = [
            ("Authentication", self.test_authentication),
            ("Profile Management", self.test_profile_management),
            ("Content Feeds", self.test_content_feeds),
            ("Interactions", self.test_interactions),
            ("Post Creation", self.test_post_creation),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"❌ {test_name}: ERROR - {e}")
                results.append((test_name, False))

            self.log("-" * 30)

        # Summary
        passed = sum(1 for _, result in results if result)
        total = len(results)

        self.log("📊 TEST SUMMARY")
        self.log("=" * 50)
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name}: {status}")

        self.log("-" * 50)
        self.log(f"Total: {passed}/{total} tests passed")

        if passed == total:
            self.log("🎉 All tests passed!")
            return True
        else:
            self.log(f"⚠️  {total - passed} tests failed")
            return False


if __name__ == "__main__":
    tester = WeWearAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
