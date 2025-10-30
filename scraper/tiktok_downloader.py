import yt_dlp
import os
import re
import subprocess
import json
import cv2
from typing import Optional, Dict, Any, cast
from datetime import datetime
import yt_dlp.utils
from photo_descriptor import analyze_grwm_photo


class TikTokDownloader:
    def __init__(self, save_path: str = "tiktok_videos"):
        self.save_path = save_path
        self.create_save_directory()

    def create_save_directory(self) -> None:
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    @staticmethod
    def validate_url(url: str) -> bool:
        tiktok_pattern = r"https?://((?:vm|vt|www)\.)?tiktok\.com/.*"
        return bool(re.match(tiktok_pattern, url))

    @staticmethod
    def progress_hook(d: Dict[str, Any]) -> None:
        if d["status"] == "downloading":
            progress = d.get("_percent_str", "N/A")
            speed = d.get("_speed_str", "N/A")
            eta = d.get("_eta_str", "N/A")
            print(f"Downloading: {progress} at {speed} ETA: {eta}", end="\r")
        elif d["status"] == "finished":
            print("\nDownload completed, finalizing...")

    def extract_video_id(self, video_url: str) -> Optional[str]:
        """Extract video ID from TikTok URL."""
        match = re.search(r"/video/(\d+)", video_url)
        if match:
            return match.group(1)
        return None

    def extract_frames(
        self, video_path: str, output_dir: str
    ) -> Optional[str]:
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error: Could not open video file {video_path}")
                return None

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

            if duration < 4:
                print(
                    f"Warning: Video duration ({duration:.2f}s) is less than 4"
                    " seconds"
                )
                target_time = duration / 2
            else:
                target_time = duration - 2
            target_frame = int(target_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            frame_path = None

            if ret:
                frame_path = os.path.join(output_dir, "video_last_frame.png")
                cv2.imwrite(frame_path, frame)
                print(f"Saved frame from {target_time:.2f}s: {frame_path}")
            else:
                print("Error: Could not read frame")

            cap.release()
            return frame_path
        except Exception as e:
            print(f"Error extracting frame: {str(e)}")
            return None

    def save_video_details(
        self, video_info: Dict[str, Any], output_path: str
    ) -> None:
        """Save video metadata to JSON file."""
        try:
            details = {
                "video_id": video_info.get("id", ""),
                "video_url": video_info.get("webpage_url", ""),
                "hashtags": video_info.get("tags", []),
                "title": video_info.get("title", ""),
                "uploader": video_info.get("uploader", ""),
                "uploader_id": video_info.get("uploader_id", ""),
                "duration": video_info.get("duration", 0),
                "view_count": video_info.get("view_count", 0),
                "like_count": video_info.get("like_count", 0),
                "comment_count": video_info.get("comment_count", 0),
                "download_date": datetime.now().isoformat(),
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(details, f, indent=2, ensure_ascii=False)
            print(f"Saved video details: {output_path}")
        except Exception as e:
            print(f"Error saving video details: {str(e)}")

    def convert_to_h264(self, input_path: str) -> bool:
        """Convert video to H.264 codec for better compatibility."""
        temp_path = input_path.replace(".mp4", "_temp.mp4")

        try:
            print("Converting video to H.264 for better compatibility...")
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    input_path,
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-y",
                    temp_path,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                os.replace(temp_path, input_path)
                print("Video conversion completed successfully!")
                return True
            else:
                print(f"Conversion failed: {result.stderr}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return False
        except Exception as e:
            print(f"Error during conversion: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def download_video(
        self, video_url: str, output_dir: str, video_id: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Download TikTok video with metadata and frames.

        Args:
            video_url: TikTok video URL
            output_dir: Directory to save the video and metadata
            video_id: Optional video ID (will be extracted from URL if not provided)

        Returns:
            Dictionary with paths to downloaded files or None on failure
        """
        if not self.validate_url(video_url):
            print("Error: Invalid TikTok URL")
            return None

        if not video_id:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                video_id = (
                    f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )

        os.makedirs(output_dir, exist_ok=True)

        video_filename = f"{video_id}.mp4"
        video_path = os.path.join(output_dir, video_filename)

        ydl_opts = {
            "outtmpl": video_path,
            "format": "best",
            "noplaylist": True,
            "quiet": False,
            "progress_hooks": [self.progress_hook],
            "cookiesfrombrowser": ("chrome",),
            "extractor_args": {"tiktok": {"webpage_download": True}},
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    " AppleWebKit/537.36 (KHTML, like Gecko)"
                    " Chrome/91.0.4472.124 Safari/537.36"
                )
            },
        }

        try:
            with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
                info = ydl.extract_info(video_url, download=True)
                print(f"\nVideo successfully downloaded: {video_path}")

                self.convert_to_h264(video_path)

                details_path = os.path.join(output_dir, "video_details.json")
                self.save_video_details(info, details_path)

                frame_path = self.extract_frames(video_path, output_dir)

                # Analyze frame with Gemini AI and save as geminie_description.json
                gemini_analysis_path = None
                print("Analyzing image with Gemini AI...")
                try:
                    analysis = analyze_grwm_photo(frame_path, save_json=False)
                    if analysis:
                        gemini_analysis_path = os.path.join(
                            output_dir, "geminie_description.json"
                        )
                        with open(
                            gemini_analysis_path, "w", encoding="utf-8"
                        ) as f:
                            json.dump(
                                analysis, f, indent=4, ensure_ascii=False
                            )
                        print(
                            f" Gemini analysis saved to:"
                            f" geminie_description.json"
                        )
                    else:
                        print(" Gemini analysis failed")
                except Exception as e:
                    print(f" Error during Gemini analysis: {e}")

                return {
                    "video_path": video_path,
                    "details_path": details_path,
                    "frame_path": frame_path or "",
                    "gemini_analysis_path": gemini_analysis_path or "",
                }

        except yt_dlp.utils.DownloadError as e:
            print(f"Error downloading video: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
        return None


if __name__ == "__main__":
    downloader = TikTokDownloader(save_path="downloaded_tiktoks")
    video_url = "https://www.tiktok.com/@zachking/video/6768504823336815877"
    result = downloader.download_video(
        video_url=video_url, output_dir="downloaded_tiktoks/test_video"
    )

    if result:
        print(f"\nAll files saved:")
        for key, path in result.items():
            print(f"  {key}: {path}")
