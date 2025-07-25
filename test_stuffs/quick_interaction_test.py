#!/usr/bin/env python3
"""
WeWear Interaction Testing Script - Quick Test

Tests like, save, comment, and share functionality and verifies they work correctly.
"""

import os
import sys
import time
import requests
import json
from typing import Dict, Any, Optional

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
import django

django.setup()

from users.models import OTP, User
from content.models import Post, Like, Save, Comment, Share


def log(message: str):
    """Print timestamped log message"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    token: Optional[str] = None,
):
    """Make HTTP request"""
    url = f"http://localhost:8000{endpoint}"
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            response = requests.get(url, headers=headers, params=data)

        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
            "success": 200 <= response.status_code < 300,
        }
    except Exception as e:
        return {"status_code": 0, "data": {"error": str(e)}, "success": False}


def quick_interaction_test():
    """Quick test of all interactions"""
    log("🚀 Quick Interaction Test")
    log("=" * 40)

    # Get a post to test with
    post = Post.objects.first()
    if not post:
        log("❌ No posts available")
        return

    post_id = post.id
    log(f"🎯 Testing with post {post_id}")

    # Authenticate
    import random

    email = f"quick_test_{random.randint(1000, 9999)}@test.com"

    # Request OTP
    result = make_request("POST", "/api/auth/request-otp", {"email": email})
    if not result["success"]:
        log(f"❌ OTP request failed")
        return

    # Get OTP
    otp_obj = OTP.objects.filter(email=email).order_by("-created_at").first()
    otp_code = otp_obj.code

    # Verify OTP
    result = make_request(
        "POST", "/api/auth/verify-otp", {"email": email, "code": otp_code}
    )
    if not result["success"]:
        log(f"❌ Authentication failed")
        return

    token = result["data"]["access_token"]
    log("✅ Authenticated")

    # Test interactions
    interactions = []

    # Like
    result = make_request(
        "POST",
        f"/api/content/interactions/like/?post_id={post_id}",
        token=token,
    )
    interactions.append(("Like", result["success"]))

    # Save
    result = make_request(
        "POST",
        f"/api/content/interactions/save/?post_id={post_id}",
        token=token,
    )
    interactions.append(("Save", result["success"]))

    # Comment
    result = make_request(
        "POST",
        "/api/content/interactions/comment/",
        {
            "post_id": post_id,
            "text": f"Quick test comment at {time.strftime('%H:%M:%S')}",
        },
        token=token,
    )
    interactions.append(("Comment", result["success"]))

    # Share
    result = make_request(
        "POST",
        "/api/content/interactions/share/",
        {"post_id": post_id},
        token=token,
    )
    interactions.append(("Share", result["success"]))

    # Results
    log("-" * 40)
    passed = 0
    for name, success in interactions:
        status = "✅ PASSED" if success else "❌ FAILED"
        log(f"{name}: {status}")
        if success:
            passed += 1

    log("-" * 40)
    log(f"Result: {passed}/{len(interactions)} interactions successful")

    if passed == len(interactions):
        log("🎉 All interactions working perfectly!")
    else:
        log("⚠️ Some interactions failed")

    # Show database counts
    log("")
    log("📊 Database verification:")
    likes = Like.objects.filter(post_id=post_id).count()
    saves = Save.objects.filter(post_id=post_id).count()
    comments = Comment.objects.filter(post_id=post_id).count()
    shares = Share.objects.filter(post_id=post_id).count()

    log(
        f"Post {post_id} - Likes: {likes}, Saves: {saves}, Comments:"
        f" {comments}, Shares: {shares}"
    )


if __name__ == "__main__":
    quick_interaction_test()
