import base64
import io
import json
import os
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

app = FastAPI(title="MenuMate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

def _image_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()

def _build_prompt() -> str:
    # MVP Simplified prompt without extra parameters like language or allergens for now,
    # as we just want the core "Capture Image -> Recognize" loop to work.
    return """You are a Michelin-star food critic and linguistic expert helping a traveler decode a foreign menu.

Task: Analyze the menu image and identify every dish name visible.
For EACH dish return a JSON object with these exact keys:

- "original_name"        : string — name exactly as printed on the menu
- "translated_name"      : string — name translated into English
- "pronunciation_guide"  : string — phonetic guide for the original name (e.g. "ri-ZOT-toh al-la MIL-a-nay-zeh")
- "description"          : string — 1-2 sentences in English describing taste, texture, cooking style. Be specific and appetizing.
- "main_ingredients"     : array of strings — top 4-6 ingredients
- "taste_tags"           : array — pick applicable: ["Spicy","Sweet","Sour","Savory","Mild","Rich/Creamy","Bitter","Umami"]
- "calories_estimate"    : string or null — rough range e.g. "450-600 kcal"
- "price"                : string or null — price as printed, or null

Return ONLY a valid JSON array containing these objects. No markdown fences, no explanation.
"""

@app.post("/api/v1/analyze")
async def analyze_menu(file: UploadFile = File(...)):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing in backend")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        if image.mode != "RGB":
            image = image.convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    payload = {
        "contents": [{
            "parts": [
                {"text": _build_prompt()},
                {"inline_data": {"mime_type": "image/jpeg", "data": _image_to_b64(image)}},
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192},
    }

    try:
        resp = requests.post(
            GEMINI_API_URL,
            params={"key": api_key},
            json=payload,
            timeout=45,
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Gemini request timed out")
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Network error to Gemini: {exc}")

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {resp.text[:300]}")

    try:
        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected API response structure from Gemini.")

    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
        raw_text = raw_text.rsplit("```", 1)[0].strip()

    try:
        dishes = json.loads(raw_text)
        return {"dishes": dishes}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Could not parse AI response: {exc}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
