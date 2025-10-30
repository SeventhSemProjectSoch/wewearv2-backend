import os
import json
import sys
import base64
from pathlib import Path
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field
from typing import Literal

load_dotenv()
Gender = Literal["boy", "girl", "man", "woman", "person"]


class GrwmAnalysis(BaseModel):
    """Schema for the Get-Ready-With-Me photo analysis."""

    identity: Gender = Field(
        description=(
            "The most certain identity (boy, girl, man, woman, or person if"
            " uncertain)."
        )
    )
    description: str = Field(
        description=(
            "ONLY describe what the person is wearing. Format: 'wearing a"
            " [color] [item] and [color] [item] with [accessories]'. Focus"
            " only on clothing and accessories, nothing else."
        )
    )
    hashtags: list[str] = Field(
        description=(
            "A list of relevant hashtags for the photo, such as #OOTD, #GRWM,"
            " #streetstyle, etc."
        )
    )
    guessed_age: int = Field(
        description=(
            "A guess of the person's age as a single integer number (e.g., 20,"
            " not '20 years old')."
        )
    )
    guessed_height_cm: int = Field(
        description=(
            "A guess of the person's height in centimeters as an integer"
            " (e.g., 178, not '178 cm'). Height is in centimeters."
        )
    )
    guessed_weight_kg: int = Field(
        description=(
            "A guess of the person's weight in kilograms as an integer (e.g.,"
            " 70, not '70 kg'). Weight is in kilograms."
        )
    )
    notes: str = Field(
        description="Any interesting observation or note about the photo."
    )


def analyze_grwm_photo(image_path: str, save_json: bool = True) -> dict:
    """
    Analyzes a local image file using the OpenRouter API and returns a structured JSON.

    Args:
        image_path: The file path to the PNG image.
        save_json: If True, saves the result as a JSON file in the same folder as the image.

    Returns:
        Dictionary containing the analysis result, or None if an error occurred.
    """
    # Convert to Path object for easier manipulation
    image_path = Path(image_path)

    if not image_path.exists():
        print(f"Error: Image file not found at {image_path}")
        return None

    # Check if API key is set
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        print("Error: OPEN_ROUTER_API_KEY not found in environment variables.")
        print(
            "   Make sure your .env file contains:"
            " OPEN_ROUTER_API_KEY=your_key_here"
        )
        return None

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    except Exception as e:
        print(f"Error reading image file: {e}")
        return None

    # Encode image to base64
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = """Analyze this 'Get Ready With Me' photo. 

IMPORTANT INSTRUCTIONS:
1. For 'description': ONLY describe what the person is wearing in this exact format: "wearing a [color] [clothing item] and [color] [clothing item] with [accessories]"
   - Do NOT describe the room, background, or pose
   - Do NOT include introductory phrases
   - Example: "wearing a black t-shirt and olive green cargo pants with a bracelet"

2. For 'guessed_age': Provide ONLY the number (e.g., 20, not "20 years old")

3. For 'guessed_height_cm': Provide ONLY the number in centimeters (e.g., 178, not "178 cm")

4. For 'guessed_weight_kg': Provide ONLY the number in kilograms (e.g., 70, not "70 kg")

5. For 'guessed_cloth_theme': Provide only one from this which best fits the clothing style or similar to these : ["casual", "formal", "sporty", "bohemian", "chic", "vintage", "streetwear", "business casual", "athleisure", "preppy","gothic"]

The output MUST be a JSON object with these fields:
- identity: one of "boy", "girl", "man", "woman", "person"
- description: clothing description
- hashtags: array of relevant hashtags
- guessed_age: integer
- guessed_height_cm: integer
- guessed_weight_kg: integer
- guessed_cloth_theme : string
- notes: any interesting observations

Return ONLY valid JSON, no other text."""

    print(
        f"Sending request to OpenRouter for analysis of: {image_path.name}..."
    )
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": (
                    "https://wewear.app"
                ),  # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": (
                    "WeWear"
                ),  # Optional. Site title for rankings on openrouter.ai.
            },
            data=json.dumps(
                {
                    "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": (
                                            f"data:image/png;base64,{image_base64}"
                                        )
                                    },
                                },
                            ],
                        }
                    ],
                }
            ),
        )

        response.raise_for_status()
        response_data = response.json()

        # Extract the JSON from the response
        content = response_data["choices"][0]["message"]["content"]

        # Try to parse the content as JSON
        # Some models might wrap the JSON in markdown code blocks
        if content.strip().startswith("```"):
            # Remove markdown code blocks
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        result = json.loads(content)

        if save_json:
            json_path = image_path.parent / f"{image_path.stem}_analysis.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            print(f"Analysis saved to: {json_path}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API call: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(
            f"Response content: {content if 'content' in locals() else 'N/A'}"
        )
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("Usage: python photo_descriptor.py <path_to_image>")
        print("Example:")
        print(
            "  python photo_descriptor.py"
            " videos/boy/Lean/alvaritobarras/7331026579012767009/video_last_frame.png"
        )
        print("\nTrying with example path...")
        image_path = "videos/boy/Lean/alvaritobarras/7331026579012767009/video_last_frame.png"

    analysis_result = analyze_grwm_photo(image_path, save_json=True)
    if analysis_result:
        print(json.dumps(analysis_result, indent=4))
