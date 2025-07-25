from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
import json
import time
import yt_dlp
import re
import subprocess
import os
from pathlib import Path


def convert_to_web_compatible(video_path):
    """Convert video to web-compatible H.264/AAC format"""
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"❌ Video file not found: {video_path}")
        return False

    # Create web-compatible version filename
    web_path = video_path.parent / f"{video_path.stem}_web.mp4"

    # Skip if web version already exists
    if web_path.exists():
        print(f"⏭️  Web version already exists: {web_path.name}")
        return True

    print(f"🔄 Converting to web format: {video_path.name}")

    # FFmpeg command for web-compatible conversion
    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-c:v",
        "libx264",  # Use H.264 for video
        "-preset",
        "fast",  # Encoding speed
        "-crf",
        "23",  # Quality (lower = better quality)
        "-c:a",
        "aac",  # Use regular AAC for audio
        "-b:a",
        "128k",  # Audio bitrate
        "-movflags",
        "+faststart",  # Web optimization
        "-y",  # Overwrite output files
        str(web_path),
    ]

    try:
        # Run conversion with timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print(f"✅ Web conversion successful: {web_path.name}")

            # Get file sizes for comparison
            original_size = video_path.stat().st_size / (1024 * 1024)  # MB
            web_size = web_path.stat().st_size / (1024 * 1024)  # MB
            print(f"   Original: {original_size:.1f}MB → Web: {web_size:.1f}MB")

            return True
        else:
            print(f"❌ Conversion failed for {video_path.name}")
            print(f"   Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ Conversion timeout for {video_path.name}")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg not found! Please install FFmpeg:")
        print("   Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("   macOS: brew install ffmpeg")
        return False
    except Exception as e:
        print(f"❌ Conversion error for {video_path.name}: {e}")
        return False


def convert_existing_videos():
    """Convert all existing scraped videos to web-compatible format"""
    base_dir = Path("videos")

    if not base_dir.exists():
        print("❌ Videos directory not found!")
        return

    # Check if FFmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found! Please install FFmpeg first.")
        print("Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("macOS: brew install ffmpeg")
        return

    # Find all MP4 files
    mp4_files = list(base_dir.rglob("*.mp4"))
    # Exclude already converted web files
    original_files = [f for f in mp4_files if not f.name.endswith("_web.mp4")]

    if not original_files:
        print("❌ No original MP4 files found to convert!")
        return

    print(f"Found {len(original_files)} original MP4 files to convert...")

    converted_count = 0
    failed_count = 0
    skipped_count = 0

    for video_file in original_files:
        web_file = video_file.parent / f"{video_file.stem}_web.mp4"

        if web_file.exists():
            print(f"⏭️  Skipping (already exists): {web_file.name}")
            skipped_count += 1
            continue

        print(f"Converting: {video_file.relative_to(base_dir)}")
        if convert_to_web_compatible(video_file):
            converted_count += 1
        else:
            failed_count += 1

    print(f"\n📊 Conversion Summary:")
    print(f"✅ Successfully converted: {converted_count}")
    print(f"⏭️  Skipped (already existed): {skipped_count}")
    print(f"❌ Failed conversions: {failed_count}")
    print(f"📁 Total files processed: {len(original_files)}")


def extract_video_urls_and_download(url):
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = uc.Chrome(options=options, version_main=None)

    try:
        print("Navigating to TikTok...")
        driver.get(url)

        print(
            "Please solve any captcha if it appears. Wait for search results to load completely.Scroll down to the amount of video you want"
        )
        input(
            "Press ENTER when you have solved the captcha if available ,else videos are visible..."
        )
        print("Extracting video URLs...")
        link_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/video/']")
        print(f"Found {len(link_elements)} video links")
        video_urls = []
        video_data = []

        for i, link in enumerate(link_elements):
            try:
                video_url = link.get_attribute("href")
                if not video_url or "/video/" not in video_url:
                    continue

                video_info = {
                    "url": video_url,
                    "video_id": video_url.split("/")[-1],
                    "index": i,
                }

                username_match = re.search(r"/@([^/]+)/", video_url)
                if username_match:
                    video_info["username"] = username_match.group(1)
                else:
                    video_info["username"] = "unknown"

                try:
                    container = link
                    for _ in range(3):
                        container = container.find_element(By.XPATH, "..")
                        text_content = container.text
                        if len(text_content) > 20:
                            break

                    hashtags = re.findall(r"#\w+", text_content)
                    video_info["hashtags"] = hashtags[:5]
                    lines = text_content.split("")
                    description = None
                    for line in lines:
                        line = line.strip()
                        if (
                            line
                            and not line.startswith("#")
                            and len(line) > 10
                            and not line.isdigit()
                        ):
                            description = line[:100]
                            break
                    video_info["description"] = description

                except:
                    video_info["hashtags"] = []
                    video_info["description"] = None

                video_urls.append(video_url)
                video_data.append(video_info)

                print(
                    f"Added video {i+1}: @{video_info['username']} - {video_info['video_id'][:10]}..."
                )

            except Exception as e:
                print(f"Error processing video {i+1}: {str(e)}")
                continue

        if video_data:
            with open("full_video_data.json", "w", encoding="utf-8") as f:
                json.dump(video_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(video_data)} video URLs to 'full_video_data.json'")

            for video in video_data:
                print(f"Video {video['index'] + 1}:")
                print(f"  Username: @{video.get('username', 'N/A')}")
                print(f"  URL: {video.get('url', 'N/A')}")
                print(f"  Description: {video.get('description', 'N/A')}")
                print(f"  Hashtags: {', '.join(video.get('hashtags', []))}")

            download_choice = (
                input(f"Download these {len(video_data)} videos using yt-dlp? (y/n): ")
                .lower()
                .strip()
            )

            if download_choice in ["y", "yes"]:
                download_videos_with_ytdlp(video_data)
            else:
                print("Download skipped. Video URLs saved to JSON file.")

        else:
            print("No video URLs could be extracted")

    except KeyboardInterrupt:
        print(" Process interrupted by user")
    except Exception as e:
        print(f" Error: {str(e)}")
        driver.save_screenshot("error_full_scraper.png")
    finally:
        print(" Closing browser...")
        driver.quit()
        print(" Done!")


def download_videos_with_ytdlp(video_data):
    print(f"Starting download of {len(video_data)} videos using yt-dlp...")

    # Check if FFmpeg is available for web conversion
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg found - web format conversion will be enabled")
        ffmpeg_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  FFmpeg not found - only original format will be available")
        print("   To enable web conversion, install FFmpeg:")
        print("   Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("   macOS: brew install ffmpeg")
        ffmpeg_available = False

    base_dir = Path("videos")
    base_dir.mkdir(exist_ok=True)
    successful_downloads = 0
    failed_downloads = 0
    skipped_downloads = 0
    web_conversions = 0

    for i, video in enumerate(video_data):
        try:
            url = video.get("url")
            username = video.get("username", "unknown")
            video_id = video.get("video_id", f"video_{i+1}")

            user_dir = base_dir / username
            user_dir.mkdir(exist_ok=True)

            video_dir = user_dir / video_id
            video_dir.mkdir(exist_ok=True)

            video_filename = f"{video_id}.mp4"
            video_path = video_dir / video_filename

            if video_path.exists():
                print(
                    f" Skipping video {i+1}/{len(video_data)}: @{username} - {video_id[:10]}... (already exists)"
                )
                skipped_downloads += 1
                continue

            ydl_opts = {
                "outtmpl": str(video_dir / f"{video_id}.%(ext)s"),
                "format": "best[vcodec^=avc][height<=720]/best[ext=mp4][height<=720]/best[height<=720]/best",
                "merge_output_format": "mp4",
                "writeinfojson": True,
                "writethumbnail": True,
                "outtmpl_thumbnail": str(video_dir / f"{video_id}.img"),
                "writesubtitles": False,
                "ignoreerrors": True,
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",
                    }
                ],
                "postprocessor_args": {"ffmpeg": ["-c:v", "libx264", "-c:a", "aac"]},
            }

            print(f"Downloading video {i+1}/{len(video_data)}: @{username}")
            print(f"Video ID: {video_id[:15]}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                    print(f"Successfully downloaded: @{username}")
                    successful_downloads += 1

                    # Convert to web-compatible format after successful download
                    if ffmpeg_available and video_path.exists():
                        print(
                            f"🔄 Converting {video_filename} to web-compatible format..."
                        )
                        conversion_success = convert_to_web_compatible(video_path)
                        if conversion_success:
                            print(f"✅ Web conversion completed for @{username}")
                            web_conversions += 1
                        else:
                            print(
                                f"⚠️  Web conversion failed for @{username} (original still available)"
                            )
                    elif not ffmpeg_available:
                        print(f"⏭️  Skipping web conversion (FFmpeg not available)")
                    else:
                        print(f"⚠️  Video file not found for conversion: {video_path}")

                except Exception as e:
                    print(f"Failed to download @{username}: {str(e)}")
                    failed_downloads += 1
            time.sleep(0.3)

        except Exception as e:
            print(f"Error processing video {i+1}: {str(e)}")
            failed_downloads += 1
            continue

    print("" + "=" * 50)
    print("DOWNLOAD SUMMARY")
    print("=" * 50)
    print(f"Successful downloads: {successful_downloads}")
    print(f"Skipped (already exists): {skipped_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Web format conversions: {web_conversions}")
    print(f"Videos saved in: {base_dir}")

    if successful_downloads > 0 or skipped_downloads > 0:
        print("User folders and videos:")
        for user_folder in sorted(base_dir.iterdir()):
            if user_folder.is_dir():
                video_folders = [f for f in user_folder.iterdir() if f.is_dir()]
                if video_folders:
                    total_size = 0
                    video_count = 0
                    for video_folder in video_folders:
                        mp4_files = list(video_folder.glob("*.mp4"))
                        if mp4_files:
                            video_count += len(mp4_files)
                            total_size += sum(
                                video.stat().st_size for video in mp4_files
                            )

                    total_size_mb = total_size / (1024 * 1024)
                    print(
                        f"{user_folder.name}/ ({video_count} videos in {len(video_folders)} folders, {total_size_mb:.1f} MB total)"
                    )

                    for video_folder in sorted(video_folders):
                        mp4_files = list(video_folder.glob("*.mp4"))
                        web_files = list(video_folder.glob("*_web.mp4"))
                        img_files = list(video_folder.glob("*.img"))
                        json_files = list(video_folder.glob("*.info.json"))

                        if mp4_files:
                            # Get original file size
                            original_files = [
                                f for f in mp4_files if not f.name.endswith("_web.mp4")
                            ]
                            file_size = (
                                original_files[0].stat().st_size / (1024 * 1024)
                                if original_files
                                else 0
                            )

                            files_info = []
                            if original_files:
                                files_info.append("mp4")
                            if web_files:
                                files_info.append("web")
                            if img_files:
                                files_info.append("img")
                            if json_files:
                                files_info.append("json")

                            web_indicator = " 🌐" if web_files else ""
                            print(
                                f"  {video_folder.name}/ ({file_size:.1f} MB) - {', '.join(files_info)}{web_indicator}"
                            )


if __name__ == "__main__":
    print("🎬 TikTok Video Scraper with Web Conversion")
    print("=" * 50)

    choice = input(
        """
Choose an option:
1. Scrape new videos (with automatic web conversion)
2. Convert existing videos to web format
3. Both scrape and convert existing

Enter choice (1-3): """
    ).strip()

    if choice == "2":
        print("\n🔄 Converting existing videos...")
        convert_existing_videos()
    elif choice == "3":
        print("\n🔄 First converting existing videos...")
        convert_existing_videos()
        print("\n📱 Now proceeding to scrape new videos...")
        url = input(
            "Enter TikTok search URL (default: https://www.tiktok.com/search/video?q=%23grwm%20%23dressing%20%23boy%20%23male): "
        ).strip()
        extract_video_urls_and_download(
            url=(
                url
                if url
                else "https://www.tiktok.com/search/video?q=%23grwm%20%23dressing%20%23boy%20%23male"
            )
        )
    else:
        # Default choice 1
        print("\n📱 Scraping new videos...")
        url = input(
            "Enter TikTok search URL (default: https://www.tiktok.com/search/video?q=%23grwm%20%23dressing%20%23boy%20%23male): "
        ).strip()
        extract_video_urls_and_download(
            url=(
                url
                if url
                else "https://www.tiktok.com/search/video?q=%23grwm%20%23dressing%20%23boy%20%23male"
            )
        )
