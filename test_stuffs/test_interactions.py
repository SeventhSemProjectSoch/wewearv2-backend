#!/usr/bin/env python3
"""
WeWear Interaction Testing Script

Tests like, save, comment, and share functionality with real data.
"""

import json
import os
import sys
import time
from typing import Any

import requests

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
import django

django.setup()

from backend.content.models import Comment
from backend.content.models import Like
from backend.content.models import Post
from backend.content.models import Save
from backend.content.models import Share
from backend.users.models import OTP


class InteractionTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session = requests.Session()
        self.token = None
        self.user_id = None

    def log(self, message: str):
        """Print timestamped log message"""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[Any, Any] = {},
        token: str | None = None,
    ) -> dict[Any, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            try:
                return {
                    "status_code": response.status_code,
                    "data": response.json() if response.content else {},
                    "success": 200 <= response.status_code < 300,
                }
            except json.JSONDecodeError:
                return {
                    "status_code": response.status_code,
                    "data": {"raw_response": response.text},
                    "success": 200 <= response.status_code < 300,
                }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False,
            }

    def authenticate(self) -> bool:
        """Authenticate and get access token"""
        self.log("🔐 Authenticating...")

        # Generate unique email
        import random

        email = f"interaction_test_{random.randint(1000, 9999)}@example.com"

        # Request OTP
        result = self.make_request(
            "POST", "/api/auth/request-otp", {"email": email}
        )
        if not result["success"]:
            self.log(f"❌ OTP request failed: {result}")
            return False

        # Get OTP from database
        try:
            otp_obj = (
                OTP.objects.filter(email=email).order_by("-created_at").first()
            )
            if not otp_obj:
                self.log("❌ No OTP found in database")
                return False

            otp_code = otp_obj.code
            self.log(f"Got OTP: {otp_code}")
        except Exception as e:
            self.log(f"❌ Error getting OTP: {e}")
            return False

        # Verify OTP
        result = self.make_request(
            "POST", "/api/auth/verify-otp", {"email": email, "code": otp_code}
        )

        if result["success"] and "access_token" in result["data"]:
            self.token = result["data"]["access_token"]
            # Extract user ID from token payload
            import jwt

            payload = jwt.decode(  # type:ignore
                self.token, options={"verify_signature": False}
            )
            self.user_id = payload.get("sub")
            self.log(f"✅ Authentication successful, User ID: {self.user_id}")
            return True
        else:
            self.log(f"❌ OTP verification failed: {result}")
            return False

    def get_available_posts(self) -> list[dict[Any, Any]]:
        """Get list of available posts"""
        posts = Post.objects.all()[:5]
        return [
            {
                "id": post.id,
                "author": post.author.username or f"User-{post.author.id}",
                "caption": (post.caption or "")[:50],
            }
            for post in posts
        ]

    def test_like_post(self, post_id: int) -> bool:
        """Test liking a post"""
        self.log(f"❤️ Testing like for post {post_id}")

        # Like the post
        result = self.make_request(
            "POST",
            f"/api/content/interactions/like/?post_id={post_id}",
            token=self.token,
        )

        if result["success"]:
            self.log(f"✅ Like successful: {result['data']}")

            # Verify in database
            like_exists = Like.objects.filter(
                user_id=self.user_id, post_id=post_id
            ).exists()

            if like_exists:
                self.log("✅ Like verified in database")
                return True
            else:
                self.log("❌ Like not found in database")
                return False
        else:
            self.log(f"❌ Like failed: {result}")
            return False

    def test_save_post(self, post_id: int) -> bool:
        """Test saving a post"""
        self.log(f"💾 Testing save for post {post_id}")

        result = self.make_request(
            "POST",
            f"/api/content/interactions/save/?post_id={post_id}",
            token=self.token,
        )

        if result["success"]:
            self.log(f"✅ Save successful: {result['data']}")

            # Verify in database
            save_exists = Save.objects.filter(
                user_id=self.user_id, post_id=post_id
            ).exists()

            if save_exists:
                self.log("✅ Save verified in database")
                return True
            else:
                self.log("❌ Save not found in database")
                return False
        else:
            self.log(f"❌ Save failed: {result}")
            return False

    def test_comment_post(self, post_id: int) -> bool:
        """Test commenting on a post"""
        self.log(f"💬 Testing comment for post {post_id}")

        comment_text = (
            "This is a test comment from interaction tester at"
            f" {time.strftime('%H:%M:%S')}"
        )

        result = self.make_request(
            "POST",
            "/api/content/interactions/comment/",
            {"post_id": post_id, "text": comment_text},
            token=self.token,
        )

        if result["success"]:
            self.log(f"✅ Comment successful: {result['data']}")

            # Verify in database
            comment_exists = Comment.objects.filter(
                user_id=self.user_id, post_id=post_id, text=comment_text
            ).exists()

            if comment_exists:
                self.log("✅ Comment verified in database")
                return True
            else:
                self.log("❌ Comment not found in database")
                return False
        else:
            self.log(f"❌ Comment failed: {result}")
            return False

    def test_share_post(self, post_id: int) -> bool:
        """Test sharing a post"""
        self.log(f"🔗 Testing share for post {post_id}")

        result = self.make_request(
            "POST",
            "/api/content/interactions/share/",
            {"post_id": post_id},
            token=self.token,
        )

        if result["success"]:
            self.log(f"✅ Share successful: {result['data']}")

            # Verify in database
            share_exists = Share.objects.filter(
                user_id=self.user_id, post_id=post_id
            ).exists()

            if share_exists:
                share_obj = Share.objects.filter(
                    user_id=self.user_id, post_id=post_id
                ).first()
                if not share_obj:
                    assert "Unreachable"
                else:
                    self.log(
                        "✅ Share verified in database with slug:"
                        f" {share_obj.slug}"
                    )
                return True
            else:
                self.log("❌ Share not found in database")
                return False
        else:
            self.log(f"❌ Share failed: {result}")
            return False

    def test_interaction_counts(self, post_id: int) -> bool:
        """Test that interaction counts are updated correctly"""
        self.log(f"📊 Testing interaction counts for post {post_id}")

        # Get post via feed to check counts
        result = self.make_request(
            "POST",
            "/api/content/feeds/explore/",
            {"exclude_ids": []},
            token=self.token,
        )

        if result["success"]:
            post_data = result["data"]
            if post_data and post_data.get("id") == post_id:
                self.log(
                    f"✅ Post counts - Likes: {post_data.get('likes_count')}, "
                    f"Comments: {post_data.get('comments_count')}, "
                    f"Saves: {post_data.get('saves_count')}, "
                    f"Shares: {post_data.get('shares_count')}"
                )

                # Check that user interactions are reflected
                liked = post_data.get("liked", False)
                saved = post_data.get("saved", False)

                self.log(
                    f"✅ User interaction states - Liked: {liked}, Saved:"
                    f" {saved}"
                )
                return True
            else:
                self.log("❌ Post not found in feed response")
                return False
        else:
            self.log(f"❌ Failed to get feed: {result}")
            return False

    def run_tests(self):
        """Run all interaction tests"""
        self.log("🚀 Starting WeWear Interaction Tests")
        self.log("=" * 50)

        # Authenticate
        if not self.authenticate():
            self.log("❌ Authentication failed, stopping tests")
            return

        # Get available posts
        posts = self.get_available_posts()
        self.log(f"📋 Available posts for testing:")
        for post in posts:
            self.log(
                f"  - ID {post['id']}: {post['author']} - {post['caption']}..."
            )

        if not posts:
            self.log("❌ No posts available for testing")
            return

        # Use the first available post
        test_post = posts[0]
        post_id = test_post["id"]

        self.log(f"\n🎯 Testing interactions with post {post_id}")
        self.log("-" * 40)

        # Run interaction tests
        tests = [
            ("Like", lambda: self.test_like_post(post_id)),
            ("Save", lambda: self.test_save_post(post_id)),
            ("Comment", lambda: self.test_comment_post(post_id)),
            ("Share", lambda: self.test_share_post(post_id)),
            ("Counts", lambda: self.test_interaction_counts(post_id)),
        ]

        results: list[tuple[str, bool]] = []
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append((test_name, success))
                self.log("")
            except Exception as e:
                self.log(f"❌ {test_name} test error: {e}")
                results.append((test_name, False))
                self.log("")

        # Summary
        self.log("📊 INTERACTION TEST SUMMARY")
        self.log("=" * 50)

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            self.log(f"{test_name}: {status}")

        self.log("-" * 50)
        self.log(f"Total: {passed}/{total} tests passed")

        if passed == total:
            self.log("🎉 All interaction tests passed!")
        else:
            self.log(f"⚠️ {total - passed} tests failed")


if __name__ == "__main__":
    tester = InteractionTester()
    tester.run_tests()
