from selenium import webdriver
from selenium.webdriver.common.by import By
from tiktok_downloader import TikTokDownloader
import os
import time
import re
import json
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Body type categories
MALE_BODY_TYPES = [
    "Lean",
    "Muscular",
    "Chubby",
    "Fit",
    "Bulked",
    "Skinny",
    "Stocky",
]

FEMALE_BODY_TYPES = [
    "Slim",
    "Curvy",
    "Chubby",
    "Thick",
    "Petite",
    "Fit",
    "Athletic",
]


class TikTokVideoScraper:
    def __init__(self, base_videos_dir: str = "videos"):
        self.base_videos_dir = base_videos_dir
        self.downloader = TikTokDownloader()
        self.driver = None

    def setup_folder_structure(
        self, gender: str, body_type: str, user_id: str, video_id: str
    ) -> str:
        """
        Create folder structure: videos/boy|girl/body_type/user_id/video_id
        Returns the full path to the video_id folder.
        """
        path = os.path.join(
            self.base_videos_dir, gender.lower(), body_type, user_id, video_id
        )
        os.makedirs(path, exist_ok=True)
        return path

    def build_search_url(self, gender: str, body_type: str) -> str:
        """
        Build TikTok search URL with base hashtags plus gender and body type.
        Base: http://www.tiktok.com/search/video?q=%23grwm%20%23dressing

        For boy + Lean: adds %23boy%23male%23lean
        For girl + Slim: adds %23girl%23female%23slim
        """
        # Base URL with grwm and dressing hashtags
        base_query = "%23grwm%20%23dressing"

        # Add gender-specific hashtags
        if gender == "boy":
            gender_tags = "%23boy%23male"
        else:  # girl
            gender_tags = "%23girl%23female"

        # Add body type (convert to lowercase for consistency)
        body_type_tag = f"%23{body_type.lower()}"

        # Combine all parts
        full_query = f"{base_query}{gender_tags}{body_type_tag}"

        return f"http://www.tiktok.com/search/video?q={full_query}"

    def get_gender_selection(self) -> str:
        """Prompt user to select gender."""
        print("\n" + "=" * 50)
        print("STEP 1: Select Gender")
        print("=" * 50)
        print("1. Boy")
        print("2. Girl")

        while True:
            choice = input("\nEnter your choice (1 or 2): ").strip()
            if choice == "1":
                return "boy"
            elif choice == "2":
                return "girl"
            else:
                print("Invalid choice! Please enter 1 or 2.")

    def get_body_type_selection(self, gender: str) -> str:
        """Prompt user to select body type based on gender."""
        print("\n" + "=" * 50)
        print("STEP 2: Select Body Type")
        print("=" * 50)

        body_types = MALE_BODY_TYPES if gender == "boy" else FEMALE_BODY_TYPES

        for i, body_type in enumerate(body_types, 1):
            print(f"{i}. {body_type}")

        while True:
            try:
                choice = int(
                    input(
                        f"\nEnter your choice (1-{len(body_types)}): "
                    ).strip()
                )
                if 1 <= choice <= len(body_types):
                    return body_types[choice - 1]
                else:
                    print(
                        "Invalid choice! Please enter a number between 1 and"
                        f" {len(body_types)}."
                    )
            except ValueError:
                print("Invalid input! Please enter a number.")

    def extract_video_info(self, video_url: str) -> Dict[str, str]:
        """
        Extract user_id and video_id from TikTok video URL.
        Example: https://www.tiktok.com/@username/video/1234567890
        Returns: {"user_id": "username", "video_id": "1234567890"}
        """
        pattern = r"https://www\.tiktok\.com/@([\w\.-]+)/video/(\d+)"
        match = re.match(pattern, video_url)
        if match:
            return {"user_id": match.group(1), "video_id": match.group(2)}
        return {"user_id": "unknown", "video_id": "unknown"}

    def extract_video_data(self) -> List[Dict]:
        """
        Extract all TikTok video data from the current page using reference scraper approach.
        Returns list of video data dictionaries with url, username, video_id, hashtags, description.
        """
        try:
            print("\nExtracting video data from page...")

            # Use CSS selector from reference: a[href*='/video/']
            link_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "a[href*='/video/']"
            )
            print(f"Found {len(link_elements)} video links")

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

                    # Extract username from URL using regex (from reference)
                    username_match = re.search(r"/@([^/]+)/", video_url)
                    if username_match:
                        video_info["username"] = username_match.group(1)
                    else:
                        video_info["username"] = "unknown"

                    # Extract hashtags and description from container (from reference)
                    try:
                        container = link
                        # Go up 3 parent elements to get the container with text
                        for _ in range(3):
                            container = container.find_element(By.XPATH, "..")
                            text_content = container.text
                            if len(text_content) > 20:
                                break

                        # Extract hashtags
                        hashtags = re.findall(r"#\w+", text_content)
                        video_info["hashtags"] = hashtags[
                            :5
                        ]  # Limit to 5 hashtags

                        # Extract description (non-hashtag text)
                        lines = text_content.split("\n")
                        description = None
                        for line in lines:
                            line = line.strip()
                            if (
                                line
                                and not line.startswith("#")
                                and len(line) > 10
                                and not line.isdigit()
                            ):
                                description = line[
                                    :100
                                ]  # Limit description length
                                break
                        video_info["description"] = description

                    except:
                        video_info["hashtags"] = []
                        video_info["description"] = None

                    video_data.append(video_info)
                    print(
                        f"Added video {i+1}: @{video_info['username']} -"
                        f" {video_info['video_id'][:10]}..."
                    )

                except Exception as e:
                    print(f"Error processing video {i+1}: {str(e)}")
                    continue

            print(
                f"Successfully extracted {len(video_data)} videos with"
                " metadata"
            )
            return video_data

        except Exception as e:
            print(f"Error extracting video data: {str(e)}")
            return []

    def download_videos(
        self, video_data: List[Dict], gender: str, body_type: str
    ) -> None:
        """
        Download all videos with organized folder structure.
        Each video goes to: videos/gender/body_type/username/video_id/
        """
        total_videos = len(video_data)
        print(f"\n{'='*50}")
        print(f"Starting download of {total_videos} videos")
        print(f"{'='*50}\n")

        successful_downloads = 0
        failed_downloads = 0
        skipped_downloads = 0

        for i, video in enumerate(video_data, 1):
            try:
                url = video.get("url")
                username = video.get("username", "unknown")
                video_id = video.get("video_id", f"video_{i}")

                # Create folder structure: videos/gender/body_type/username/video_id/
                video_dir = self.setup_folder_structure(
                    gender=gender,
                    body_type=body_type,
                    user_id=username,
                    video_id=video_id,
                )

                video_path = os.path.join(video_dir, f"{video_id}.mp4")

                # Skip if already exists
                if os.path.exists(video_path):
                    print(
                        f" [{i}/{total_videos}] Skipping @{username} -"
                        f" {video_id[:10]}... (already exists)"
                    )
                    skipped_downloads += 1
                    continue

                print(f"\n[{i}/{total_videos}] Downloading: @{username}")
                print(f"  Video ID: {video_id[:15]}...")
                print(f"  Description: {video.get('description', 'N/A')}")
                print(f"  Hashtags: {', '.join(video.get('hashtags', []))}")

                # Download video with metadata and frames
                result = self.downloader.download_video(
                    video_url=url, output_dir=video_dir
                )

                if result:
                    print(f"✓ Successfully downloaded: @{username}")
                    successful_downloads += 1
                else:
                    print(f"✗ Failed to download: @{username}")
                    failed_downloads += 1

            except Exception as e:
                print(
                    f"✗ Error downloading video {i}/{total_videos}: {str(e)}"
                )
                failed_downloads += 1

            # Small delay between downloads
            time.sleep(2)

        print(f"\n{'='*50}")
        print("DOWNLOAD SUMMARY")
        print(f"{'='*50}")
        print(f"Successful downloads: {successful_downloads}")
        print(f" Skipped (already exists): {skipped_downloads}")
        print(f"Failed downloads: {failed_downloads}")
        print(
            "Videos saved in:"
            f" {self.base_videos_dir}/{gender.lower()}/{body_type}/"
        )
        print(f"{'='*50}\n")


def scrape_tiktok_videos():
    scraper = TikTokVideoScraper()
    try:
        gender = scraper.get_gender_selection()
        print(f"\nSelected gender: {gender.capitalize()}")
        body_type = scraper.get_body_type_selection(gender)
        print(f"Selected body type: {body_type}")
        search_url = scraper.build_search_url(gender, body_type)
        print(f"\n{'='*50}")
        print("STEP 3: Browser Interaction")
        print(f"{'='*50}")
        print(f"Opening browser with URL: {search_url}")

        scraper.driver = webdriver.Chrome()
        scraper.driver.get(search_url)

        print("\n" + "=" * 50)
        print("INSTRUCTIONS:")
        print("1. Solve the CAPTCHA if prompted")
        print("2. Scroll down to load all desired videos")
        print("3. Press ENTER when ready to start extraction")
        print("=" * 50)
        input("\nPress ENTER to continue...")
        video_data = scraper.extract_video_data()
        if not video_data:
            print("\n⚠ No videos found! Please check the page and try again.")
            return
        json_filename = f"scraped_videos_{gender}_{body_type}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(video_data, f, indent=2, ensure_ascii=False)
        print(f"\nSaved video data to: {json_filename}")
        print(f"\n{'='*50}")
        print(f"Found {len(video_data)} videos:")
        print(f"{'='*50}")
        for video in video_data[:5]:  # Show first 5
            print(
                f"  @{video.get('username', 'N/A')} -"
                f" {video.get('video_id', 'N/A')[:10]}..."
            )
            print(f"    Description: {video.get('description', 'N/A')}")
            print(f"    Hashtags: {', '.join(video.get('hashtags', []))}\n")
        if len(video_data) > 5:
            print(f"  ... and {len(video_data) - 5} more videos")

        print(f"\n{'='*50}")
        print(f"Ready to download {len(video_data)} videos")
        print(
            f"Destination: videos/{gender}/{body_type}/[username]/[video_id]/"
        )
        print(f"{'='*50}")
        confirm = input("\nProceed with download? (yes/no): ").strip().lower()

        if confirm in ["yes", "y"]:
            scraper.download_videos(video_data, gender, body_type)
        else:
            print("\nDownload cancelled by user.")
            print(f"Video data saved in: {json_filename}")

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper.driver:
            scraper.driver.quit()
            print("\nBrowser closed.")


if __name__ == "__main__":
    scrape_tiktok_videos()
