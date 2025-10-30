import threading
from pathlib import Path

import cv2
from content.models import Post
from utils.analyze_post import analyze_image_with_gemini


def extract_frames(
    video_path: str, output_dir: str, image_name: str = "last_frame.png"
):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return None

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0

        if duration < 4:
            print(f"Warning: Video duration ({duration:.2f}s) is less than 4 seconds")
            target_time = duration / 2
        else:
            target_time = duration - 2
        target_frame = int(target_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        frame_path = None

        if ret:
            frame_path = Path(output_dir) / image_name
            cv2.imwrite(str(frame_path), frame)
            print(f"Saved frame from {target_time:.2f}s: {frame_path}")
        else:
            print("Error: Could not read frame")

        cap.release()
        return frame_path
    except Exception as e:
        print(f"Error extracting frame: {str(e)}")
        return None


def process_post_image_analysis(post: Post, frame_path: Path):
    try:
        if not post.media_file:
            return

        if not frame_path.exists():
            print(f"Frame not found for post {post.id}")
            return

        analysis = analyze_image_with_gemini(str(frame_path))
        if not analysis:
            return

        user_caption = post.caption or ""
        ai_content = (
            f"\n\n(AI: {analysis['image_description']} {analysis['image_hashtags']})"
        )

        post.caption = user_caption + ai_content
        post.ai_captioned = True
        post.save(update_fields=["caption", "ai_captioned"])

        print(f"Successfully analyzed and updated post {post.id}")

    except Exception as e:
        print(f"Error processing image analysis for post {post.id}: {str(e)}")


def process_post_video(post: Post):
    try:
        if not post.media_file:
            return

        video_path = post.media_file.path
        if not video_path.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".webm")):
            return

        output_dir = Path(video_path).parent
        image_path = extract_frames(video_path, str(output_dir), "last_frame.png")
        if image_path:
            process_post_image_analysis(post, image_path)

    except Exception as e:
        print(f"Error processing video for post {post.id}: {str(e)}")


def process_post_video_async(post: Post):
    thread = threading.Thread(target=process_post_video, args=(post,), daemon=True)
    thread.start()
