#!/usr/bin/env python3
"""
Database Cleanup Script for WeWear

This script removes all existing posts and users from the database
so you can start fresh with the simulate_users.py script.
"""

import os
import sys
from pathlib import Path

# Add Django setup
sys.path.append("/home/kali_37/7th_sem_project/wewearv2-backend/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

import django

django.setup()

from django.db import transaction
from users.models import User, Theme
from content.models import Post, Follow, Like, Save, Comment, Share, Impression


def cleanup_database():
    """Remove all posts and users from the database"""
    print("🧹 Starting database cleanup...")
    print("=" * 50)

    try:
        with transaction.atomic():
            # Get counts before deletion
            users_count = User.objects.count()
            posts_count = Post.objects.count()
            follows_count = Follow.objects.count()
            likes_count = Like.objects.count()
            saves_count = Save.objects.count()
            comments_count = Comment.objects.count()
            shares_count = Share.objects.count()
            impressions_count = Impression.objects.count()

            print(f"📊 Current database state:")
            print(f"   Users: {users_count}")
            print(f"   Posts: {posts_count}")
            print(f"   Follows: {follows_count}")
            print(f"   Likes: {likes_count}")
            print(f"   Saves: {saves_count}")
            print(f"   Comments: {comments_count}")
            print(f"   Shares: {shares_count}")
            print(f"   Impressions: {impressions_count}")
            print()

            if users_count == 0 and posts_count == 0:
                print("✅ Database is already clean!")
                return

            # Confirm deletion
            confirm = (
                input(
                    "⚠️  This will delete ALL posts and users. Continue?"
                    " (y/N): "
                )
                .strip()
                .lower()
            )
            if confirm not in ["y", "yes"]:
                print("❌ Cleanup cancelled.")
                return

            print("🗑️  Deleting content...")

            # Delete in order to avoid foreign key constraints
            # Delete interactions first
            if impressions_count > 0:
                Impression.objects.all().delete()
                print(f"   ✅ Deleted {impressions_count} impressions")

            if shares_count > 0:
                Share.objects.all().delete()
                print(f"   ✅ Deleted {shares_count} shares")

            if comments_count > 0:
                Comment.objects.all().delete()
                print(f"   ✅ Deleted {comments_count} comments")

            if saves_count > 0:
                Save.objects.all().delete()
                print(f"   ✅ Deleted {saves_count} saves")

            if likes_count > 0:
                Like.objects.all().delete()
                print(f"   ✅ Deleted {likes_count} likes")

            if follows_count > 0:
                Follow.objects.all().delete()
                print(f"   ✅ Deleted {follows_count} follows")

            # Delete posts
            if posts_count > 0:
                Post.objects.all().delete()
                print(f"   ✅ Deleted {posts_count} posts")

            # Delete users (but keep themes)
            if users_count > 0:
                User.objects.all().delete()
                print(f"   ✅ Deleted {users_count} users")

            print()
            print("🎉 Database cleanup completed successfully!")
            print(
                "📝 You can now run simulate_users.py to repopulate with fresh"
                " data"
            )

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        print("🔄 Database transaction rolled back")


def show_themes():
    """Show available themes (these will be preserved)"""
    themes = Theme.objects.all()
    if themes:
        print(
            "🏷️  Available themes (preserved):"
            f" {', '.join([t.name for t in themes])}"
        )
    else:
        print("⚠️  No themes found. You may need to create themes first.")


if __name__ == "__main__":
    print("🎬 WeWear Database Cleanup Tool")
    print("=" * 50)

    # Show themes first
    show_themes()
    print()

    # Run cleanup
    cleanup_database()
