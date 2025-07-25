#!/usr/bin/env python3
"""
WeWear User and Content Simulation Script

This script creates users and posts from scraped video data.
Structure: videos/username/video_id/video_id.info.json, video_id.mp4, video_id.image

Features:
- Creates users with random themes and fake names
- Skips existing users and videos
- Adds new videos for existing users on re-run
- Generates diverse user profiles based on video content
"""

import json
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add Django setup
sys.path.append("/home/kali_37/7th_sem_project/wewearv2-backend/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

import django

django.setup()

from django.db import transaction
from users.models import User, Theme
from content.models import Post


class VideoUserSimulator:
    def __init__(
        self,
        scraped_video_path: str = "/home/kali_37/7th_sem_project/wewearv2-backend/videos/",
    ):
        self.scraped_video_path = Path(scraped_video_path)
        self.themes = list(Theme.objects.all())
        self.fake_names = [
            "Alex Johnson",
            "Sam Smith",
            "Jordan Davis",
            "Casey Brown",
            "Riley Wilson",
            "Morgan Taylor",
            "Avery Anderson",
            "Quinn Thompson",
            "Blake Martinez",
            "Drew Garcia",
            "Sage Miller",
            "River Jones",
            "Sky Williams",
            "Phoenix Lee",
            "Sage Rodriguez",
            "Dakota Lewis",
            "Cameron Clark",
            "Emery Walker",
            "Finley Hall",
            "Hayden Allen",
        ]
        self.fashion_bios = [
            "Fashion enthusiast sharing my daily style journey ✨",
            "Styling tips and outfit inspiration for every occasion 👗",
            "Menswear lover creating timeless looks 🖤",
            "Sustainable fashion advocate | Thrifting queen 🌱",
            "Street style photographer & fashion blogger 📸",
            "Vintage collector sharing authentic retro vibes 🕰️",
            "Color coordination expert | Making fashion fun 🌈",
            "Minimalist wardrobe | Less is more philosophy ⚪",
            "Fashion designer showcasing creative concepts 🎨",
            "Style coach helping you find your aesthetic 💫",
            "Luxury fashion curator | High-end style inspiration 💎",
            "Budget-friendly fashion hacks and finds 💰",
            "Athletic wear styling | Fashion meets function 🏃",
            "Plus-size fashion advocate | Style has no size 💪",
            "Seasonal styling expert | Weather-appropriate fashion 🌟",
        ]

    def log(self, message: str):
        """Log with styling"""
        print(f"🎬 {message}")

    def get_scraped_usernames(self) -> List[str]:
        """Get all username directories from scraped videos"""
        if not self.scraped_video_path.exists():
            self.log(f"Video path {self.scraped_video_path} does not exist")
            return []

        usernames = []
        for item in self.scraped_video_path.iterdir():
            if item.is_dir():
                usernames.append(item.name)

        return usernames

    def get_user_videos(self, username: str) -> List[Dict]:
        """Get all video data for a username"""
        user_path = self.scraped_video_path / username
        videos = []

        if not user_path.exists():
            self.log(f"  User directory does not exist: {user_path}")
            return videos

        video_dirs_found = 0
        valid_videos = 0
        missing_files_count = 0

        for video_dir in user_path.iterdir():
            if video_dir.is_dir():
                video_dirs_found += 1
                video_id = video_dir.name
                json_file = video_dir / f"{video_id}.info.json"
                mp4_file = video_dir / f"{video_id}.mp4"
                web_mp4_file = (
                    video_dir / f"{video_id}_web.mp4"
                )  # Web-compatible video
                image_file = video_dir / f"{video_id}.image"

                # Check what files are missing
                missing_files = []
                if not json_file.exists():
                    missing_files.append("info.json")
                if not web_mp4_file.exists():
                    missing_files.append("_web.mp4")
                if not image_file.exists():
                    missing_files.append("image")

                if missing_files:
                    missing_files_count += 1
                    self.log(
                        f"  Video {video_id} missing files:"
                        f" {', '.join(missing_files)}"
                    )

                    # Skip if missing critical files (JSON or web-compatible MP4)
                    if not json_file.exists() or not web_mp4_file.exists():
                        self.log(
                            f"  Skipping {video_id} - missing critical files"
                        )
                        continue

                # Try to read the json file
                if json_file.exists() and web_mp4_file.exists():
                    try:
                        with open(json_file, "r") as f:
                            metadata = json.load(f)

                        videos.append(
                            {
                                "video_id": video_id,
                                "metadata": metadata,
                                "mp4_path": (
                                    str(mp4_file)
                                    if mp4_file.exists()
                                    else None
                                ),
                                "web_mp4_path": (
                                    str(web_mp4_file)
                                    if web_mp4_file.exists()
                                    else None
                                ),
                                "image_path": (
                                    str(image_file)
                                    if image_file.exists()
                                    else None
                                ),
                                "json_path": str(json_file),
                                "has_video": mp4_file.exists(),
                                "has_web_video": web_mp4_file.exists(),
                                "has_image": image_file.exists(),
                            }
                        )
                        valid_videos += 1
                    except Exception as e:
                        self.log(f"  Error reading {json_file}: {e}")

        # Log detailed summary for this user
        if video_dirs_found > 0:
            self.log(
                f"  Directory summary: {video_dirs_found} video dirs,"
                f" {valid_videos} valid, {missing_files_count} with missing"
                " files"
            )
        else:
            self.log(f"  No video directories found in {user_path}")

        return videos

    def extract_themes_from_description(
        self, description: str, title: str
    ) -> List[str]:
        """Extract relevant themes from video content"""
        text = f"{description} {title}".lower()

        # Fashion keyword mapping to our themes
        theme_keywords = {
            "formal": [
                "formal",
                "suit",
                "business",
                "office",
                "professional",
                "dress",
                "elegant",
            ],
            "informal": [
                "casual",
                "street",
                "everyday",
                "relaxed",
                "comfortable",
                "weekend",
            ],
            "classic": [
                "classic",
                "timeless",
                "traditional",
                "vintage",
                "retro",
                "heritage",
            ],
            "cultural": [
                "cultural",
                "traditional",
                "ethnic",
                "heritage",
                "festival",
                "celebration",
            ],
            "gothic": [
                "gothic",
                "dark",
                "black",
                "alternative",
                "edgy",
                "punk",
            ],
        }

        detected_themes = []
        for theme_name, keywords in theme_keywords.items():
            if any(keyword in text for keyword in keywords):
                detected_themes.append(theme_name)

        # Default fallback themes if none detected
        if not detected_themes:
            detected_themes = ["classic", "informal"]

        return detected_themes[:3]  # Max 3 themes as required

    def generate_user_profile(self, username: str, videos: List[Dict]) -> Dict:
        """Generate a complete user profile based on video content"""
        # Get a sample video for profile generation
        sample_video = videos[0] if videos else None

        if sample_video:
            metadata = sample_video["metadata"]
            channel_name = metadata.get(
                "channel", username.replace("_", " ").title()
            )
            description = metadata.get("description", "")
            title = metadata.get("title", "")

            # Extract themes from video content
            theme_names = self.extract_themes_from_description(
                description, title
            )
        else:
            channel_name = username.replace("_", " ").title()
            theme_names = ["classic", "informal"]

        # Generate profile data
        profile = {
            "username": username,
            "full_name": random.choice(self.fake_names),
            "bio": random.choice(self.fashion_bios),
            "themes": theme_names,
            "body_type": random.choice(
                ["slim", "athletic", "average", "plus-size", "muscular"]
            ),
            "height": round(random.uniform(150.0, 200.0), 1),
            "weight": round(random.uniform(45.0, 120.0), 1),
        }

        return profile

    def create_or_get_user(
        self, username: str, profile: Dict
    ) -> Optional[User]:
        """Create user or get existing one"""
        try:
            user = User.objects.filter(username=username).first()
            if user:
                self.log(f"User '{username}' already exists")
                return user

            # Create user with email based on username
            email = f"{username}@simulated.com"
            user = User.objects.create(
                username=username,
                email=email,
                full_name=profile["full_name"],
                bio=profile["bio"],
                body_type=profile["body_type"],
                height=profile["height"],
                weight=profile["weight"],
            )

            # Add themes
            theme_objects = Theme.objects.filter(name__in=profile["themes"])
            user.themes.set(theme_objects)

            self.log(
                f"✅ Created user '{username}' with themes:"
                f" {profile['themes']}"
            )
            return user

        except Exception as e:
            self.log(f"❌ Error creating user '{username}': {e}")
            return None

    def create_post_from_video(
        self, user: User, video_data: Dict
    ) -> Optional[Post]:
        """Create a post from video data"""
        try:
            video_id = video_data["video_id"]
            metadata = video_data["metadata"]

            # Check if post already exists
            existing_post = Post.objects.filter(
                author=user,
                caption__contains=video_id,  # Use video_id as identifier
            ).first()

            if existing_post:
                self.log(f"  Post for video {video_id} already exists")
                return existing_post

            # Validate that we have required files
            has_video = video_data.get("has_video", False)
            has_web_video = video_data.get("has_web_video", False)
            has_image = video_data.get("has_image", False)

            # Must have web-compatible video to create post
            if not has_web_video:
                self.log(
                    f"  ⚠️  Video {video_id} has no web-compatible MP4"
                    " (_web.mp4), skipping post creation"
                )
                return None

            if not has_image:
                self.log(
                    f"  ⚠️  Video {video_id} has no image file, using fallback"
                    " thumbnail"
                )

            # Extract post data
            title = metadata.get("title", "")
            description = metadata.get("description", "")
            caption = f"{title[:100]}..." if len(title) > 100 else title

            if not caption.strip():
                caption = f"Fashion post {video_id}"

            # Use web-compatible MP4 file path directly
            if video_data.get("web_mp4_path") and has_web_video:
                # Convert absolute path to relative URL path for _web.mp4
                web_mp4_path = Path(video_data["web_mp4_path"])
                # Extract the relative path from /videos/ onwards
                try:
                    # Find the videos directory in the path
                    path_parts = web_mp4_path.parts
                    videos_index = path_parts.index("videos")
                    relative_path = "/".join(path_parts[videos_index:])
                    media_url = f"/{relative_path}"
                except (ValueError, IndexError):
                    # Fallback if path structure is unexpected
                    media_url = f"/videos/{user.username}/{video_id}/{video_id}_web.mp4"
            else:
                # Use standard path structure for _web.mp4
                media_url = (
                    f"/videos/{user.username}/{video_id}/{video_id}_web.mp4"
                )
                self.log(f"  Using fallback _web.mp4 URL: {media_url}")

            # Detect themes from content
            theme_names = self.extract_themes_from_description(
                description, title
            )
            theme_objects = Theme.objects.filter(name__in=theme_names)

            # Create post
            post = Post.objects.create(
                author=user,
                caption=caption,
                media_url=media_url,
            )

            # Add themes
            post.themes.set(theme_objects)

            status_emoji = "✅" if has_web_video and has_image else "⚠️"
            file_status = (
                f"(web_video: {'✓' if has_web_video else '✗'}, image:"
                f" {'✓' if has_image else '✗'})"
            )
            self.log(
                f"  {status_emoji} Created post from video"
                f" {video_id} {file_status}"
            )
            return post

        except Exception as e:
            self.log(
                "  ❌ Error creating post from video"
                f" {video_data['video_id']}: {e}"
            )
            return None

    def simulate_user_and_content(self, username: str) -> bool:
        """Simulate complete user with all their content"""
        self.log(f"Processing user: {username}")

        # Get all videos for this user
        videos = self.get_user_videos(username)
        if not videos:
            self.log(f"  ❌ No valid videos found for {username}")
            return False

        self.log(f"  Found {len(videos)} valid videos")

        # Check if user has any usable content
        usable_videos = [v for v in videos if v.get("has_web_video")]
        if not usable_videos:
            self.log(
                "  ❌ No videos with web-compatible MP4 files found for"
                f" {username}"
            )
            return False

        if len(usable_videos) < len(videos):
            self.log(
                f"  ⚠️  Only {len(usable_videos)}/{len(videos)} videos have"
                " web-compatible MP4 files"
            )

        # Generate user profile
        profile = self.generate_user_profile(username, videos)

        # Create or get user
        user = self.create_or_get_user(username, profile)
        if not user:
            return False

        # Create posts from videos
        posts_created = 0
        posts_skipped = 0
        for video_data in videos:
            post = self.create_post_from_video(user, video_data)
            if post:
                posts_created += 1
            else:
                posts_skipped += 1

        if posts_skipped > 0:
            self.log(
                f"  Created {posts_created} posts, skipped"
                f" {posts_skipped} (missing web-compatible MP4)"
            )
        else:
            self.log(f"  Created {posts_created} new posts for {username}")

        return (
            posts_created > 0
        )  # Consider successful if at least one post was created

    def analyze_video_directories(self) -> Dict:
        """Analyze the video directories to provide detailed statistics"""
        stats = {
            "total_users": 0,
            "users_with_dirs": 0,
            "users_with_videos": 0,
            "total_video_dirs": 0,
            "missing_json": 0,
            "missing_mp4": 0,
            "missing_web_mp4": 0,
            "missing_image": 0,
            "complete_videos": 0,
            "web_ready_videos": 0,
            "problematic_users": [],
        }

        usernames = self.get_scraped_usernames()
        stats["total_users"] = len(usernames)

        for username in usernames:
            user_path = self.scraped_video_path / username
            if user_path.exists():
                stats["users_with_dirs"] += 1

                video_dirs = [d for d in user_path.iterdir() if d.is_dir()]
                if video_dirs:
                    stats["users_with_videos"] += 1
                    stats["total_video_dirs"] += len(video_dirs)

                    user_issues = []
                    for video_dir in video_dirs:
                        video_id = video_dir.name
                        json_file = video_dir / f"{video_id}.info.json"
                        mp4_file = video_dir / f"{video_id}.mp4"
                        web_mp4_file = video_dir / f"{video_id}_web.mp4"
                        image_file = video_dir / f"{video_id}.image"

                        if not json_file.exists():
                            stats["missing_json"] += 1
                            user_issues.append(f"{video_id}: no JSON")
                        if not mp4_file.exists():
                            stats["missing_mp4"] += 1
                            user_issues.append(f"{video_id}: no MP4")
                        if not web_mp4_file.exists():
                            stats["missing_web_mp4"] += 1
                            user_issues.append(f"{video_id}: no _web.mp4")
                        if not image_file.exists():
                            stats["missing_image"] += 1
                            user_issues.append(f"{video_id}: no image")

                        if (
                            json_file.exists()
                            and mp4_file.exists()
                            and image_file.exists()
                        ):
                            stats["complete_videos"] += 1

                        if json_file.exists() and web_mp4_file.exists():
                            stats["web_ready_videos"] += 1

                    if user_issues:
                        stats["problematic_users"].append(
                            {
                                "username": username,
                                "issues": user_issues[
                                    :3
                                ],  # Show first 3 issues
                            }
                        )

        return stats

    def run_simulation(self) -> None:
        """Run the complete simulation"""
        self.log("🚀 Starting WeWear User Simulation")
        self.log("=" * 60)

        # Check if themes exist
        if not self.themes:
            self.log(
                "❌ No themes found in database. Please run migrations first."
            )
            return

        self.log(f"Available themes: {[theme.name for theme in self.themes]}")

        # Analyze video directories first
        self.log("🔍 Analyzing video directories...")
        stats = self.analyze_video_directories()

        self.log("📊 VIDEO DIRECTORY ANALYSIS")
        self.log("-" * 40)
        self.log(f"Total user directories: {stats['total_users']}")
        self.log(f"Users with video directories: {stats['users_with_videos']}")
        self.log(f"Total video directories: {stats['total_video_dirs']}")
        self.log(f"Complete videos (all files): {stats['complete_videos']}")
        self.log(
            f"Web-ready videos (JSON + _web.mp4): {stats['web_ready_videos']}"
        )
        self.log(f"Missing JSON files: {stats['missing_json']}")
        self.log(f"Missing MP4 files: {stats['missing_mp4']}")
        self.log(f"Missing _web.mp4 files: {stats['missing_web_mp4']}")
        self.log(f"Missing image files: {stats['missing_image']}")

        if stats["problematic_users"]:
            self.log(
                f"Users with missing files: {len(stats['problematic_users'])}"
            )
            # Show a few examples
            for user in stats["problematic_users"][:5]:
                self.log(f"  {user['username']}: {', '.join(user['issues'])}")
            if len(stats["problematic_users"]) > 5:
                self.log(
                    f"  ... and {len(stats['problematic_users']) - 5} more"
                )

        # Get all scraped usernames
        usernames = self.get_scraped_usernames()
        if not usernames:
            self.log("❌ No scraped video directories found")
            return

        self.log(f"\nFound {len(usernames)} scraped users")
        self.log("-" * 60)

        # Process each user
        total_users = len(usernames)
        successful_users = 0

        for i, username in enumerate(usernames, 1):
            self.log(f"[{i}/{total_users}] Processing {username}")

            try:
                with transaction.atomic():
                    success = self.simulate_user_and_content(username)
                    if success:
                        successful_users += 1
            except Exception as e:
                self.log(f"❌ Failed to process {username}: {e}")

            self.log("-" * 40)

        # Summary
        self.log("📊 SIMULATION SUMMARY")
        self.log("=" * 60)
        self.log(f"Total users processed: {total_users}")
        self.log(f"Successful: {successful_users}")
        self.log(f"Failed: {total_users - successful_users}")

        # Database stats
        total_db_users = User.objects.count()
        total_db_posts = Post.objects.count()

        self.log(f"Total users in database: {total_db_users}")
        self.log(f"Total posts in database: {total_db_posts}")

        if successful_users == total_users:
            self.log("🎉 All users processed successfully!")
        else:
            self.log(
                f"⚠️  {total_users - successful_users} users failed to process"
            )


if __name__ == "__main__":
    # Read video path from developer_test.py if available
    video_path = "/home/kali_37/7th_sem_project/wewearv2-backend/videos/"

    try:
        with open(
            "/home/kali_37/7th_sem_project/wewearv2-backend/developer_test.py",
            "r",
        ) as f:
            content = f.read()
            if "SCRAPED_VIDEO_PATH" in content:
                # Extract the path
                for line in content.split("\n"):
                    if line.strip().startswith("SCRAPED_VIDEO_PATH"):
                        path = line.split("=")[1].strip().strip("\"'")
                        if not path.startswith("/"):
                            path = f"/home/kali_37/7th_sem_project/wewearv2-backend{path}"
                        video_path = path
                        break
    except Exception:
        pass

    simulator = VideoUserSimulator(video_path)
    simulator.run_simulation()
