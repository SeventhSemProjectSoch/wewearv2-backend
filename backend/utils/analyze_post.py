import base64
import json
import sys
from pathlib import Path

import requests
from project.env import ENV

_PROMPT = """"Analyze the provided image. Your response MUST be a valid JSON object, and ONLY a JSON object, adhering strictly to the following structure. If your output deviates from this JSON structure in any way—even a single extra character, space, or invalid comma—it will be considered a critical failure.

{
    \"image_description\": \"Describe the person's body type (choose one from: lean, skinny, athletic, chubby, plus-size) and clothing theme (choose one from: formal, informal, sportswear, office, casual, vintage, streetwear, etc.). write about 1-2 sentence, it should make searching easy for backend. Also write in a way that it describs the outfit, the style\",
    \"image_hashtags\": \"Provide 5 to 10 relevant hashtags, separated by spaces. Each hashtag MUST start with '#' (e.g., #fashion #style). Ensure they are highly searchable and pertinent to the image's content.\"
}

and, 

Failure to produce a perfect, parsable JSON object will result in an immediate cessation of subsequent tasks and a flag for review. Do not include any conversational text, explanations, extra newlines, or characters outside the exact JSON structure. Your output must begin with '{' and end with '}'.
"""


def analyze_image_with_gemini(
    image_path: str, prompt: str = _PROMPT
) -> dict[str, str] | None:
    try:
        api_key = ENV.GEMINI_API_KEY
        if not api_key:
            print("Error: GEMINI_API_KEY not set")
            return None

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"

        headers = {"Content-Type": "application/json"}

        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/png", "data": image_data}},
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.1, "topP": 1, "topK": 1},
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            print(f"Error from Gemini API: {response.status_code} - {response.text}")
            return None

        result = response.json()
        content = result["candidates"][0]["content"]["parts"][0]["text"]
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        analysis = json.loads(content)
        return analysis

    except Exception as e:
        print(f"Error analyzing image with Gemini: {str(e)}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <image_path>")
        sys.exit(1)

    img_path = Path(sys.argv[1])
    if not img_path.is_file():
        print(f"Error: File '{img_path}' does not exist.")
        sys.exit(1)

    result = analyze_image_with_gemini(str(img_path))
    print(json.dumps(result, indent=4))
