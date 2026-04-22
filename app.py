"""
MenuMate — Don't just translate, visualize.
Helps travelers understand foreign menus via AI-powered scanning.

User Flow: Home → Profile (sidebar) → Scan/Upload → Recognize → Result Card
"""

import base64
import io
import json
import os
import urllib.parse

import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "menu_context" not in st.session_state:
    st.session_state.menu_context = None
# ── Constants ─────────────────────────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

LANGUAGE_OPTIONS = [
    "English",
    "Chinese (Simplified)",
    "Chinese (Traditional)",
    "Japanese",
    "Korean",
    "Spanish",
    "French",
    "German",
    "Portuguese",
    "Arabic",
]

ALLERGEN_OPTIONS = [
    "Peanuts",
    "Tree Nuts",
    "Gluten / Wheat",
    "Dairy / Lactose",
    "Eggs",
    "Shellfish",
    "Fish / Seafood",
    "Soy",
    "Sesame",
    "Cilantro / Coriander",
    "Mushrooms",
    "Pork",
]

FLAVOR_OPTIONS = ["Spicy", "Sweet", "Sour", "Savory / Umami", "Mild", "Rich / Creamy", "Bitter"]

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MenuMate",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
/* Global */
[data-testid="stAppViewContainer"] { background: #fafaf9; }
[data-testid="stSidebar"] { background: #1c1917; color: #fafaf9; }
[data-testid="stSidebar"] * { color: #fafaf9 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stTextInput label { color: #d6d3d1 !important; }

/* Dish card */
.dish-card {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 1rem;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s;
}
.dish-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); }
.dish-card.has-warning { border-left: 4px solid #ef4444; }
.dish-card.recommended { border-left: 4px solid #22c55e; }

.dish-original  { font-size: 1.15rem; font-weight: 700; color: #1c1917; }
.dish-translated { font-size: 0.85rem; color: #ea580c; font-weight: 600;
                   text-transform: uppercase; letter-spacing: 0.04em; }
.dish-pronunciation { font-size: 0.82rem; color: #78716c; font-style: italic; }
.dish-desc { color: #44403c; font-size: 0.95rem; line-height: 1.55; margin: 0.5rem 0; }

.tag {
    display: inline-block;
    background: #f5f5f4;
    color: #57534e;
    border-radius: 9999px;
    padding: 0.15rem 0.65rem;
    font-size: 0.78rem;
    margin: 0.1rem 0.1rem 0.1rem 0;
}
.warning-tag { background: #fee2e2; color: #dc2626; }
.recommend-tag { background: #dcfce7; color: #16a34a; }
.price-tag { font-weight: 700; color: #1c1917; }

.section-title {
    font-size: 1.1rem; font-weight: 700; color: #1c1917;
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.35rem;
    border-bottom: 2px solid #ea580c;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Step 2 — PROFILE (Sidebar) ────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🍽️ MenuMate")
    st.caption("Don't just translate, visualize.")
    st.markdown("---")

    # API Key — prefer environment variable, fall back to manual input
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        api_key = env_key
        st.success("✓ API key loaded")
    else:
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Free key at aistudio.google.com/apikey",
        ).strip()

    st.markdown("---")
    st.markdown("### Your Profile")

    target_lang = st.selectbox("🌐 Translate menu into", LANGUAGE_OPTIONS, index=0)

    flavor_prefs = st.multiselect(
        "😋 Flavor preferences",
        FLAVOR_OPTIONS,
        help="Dishes matching these will be highlighted.",
    )

    allergens = st.multiselect(
        "⚠️ Allergens / foods to avoid",
        ALLERGEN_OPTIONS,
        help="Dishes containing these will show a red alert.",
    )

    dietary_notes = st.text_input(
        "🚫 Other restrictions",
        placeholder="e.g. vegetarian, no pork, halal…",
    )

    st.markdown("---")
    st.caption("v0.1 · MVP · Powered by Gemini 2.5 Flash")

# ── Helpers ───────────────────────────────────────────────────────────────────


def _image_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()

def _audio_to_b64(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode()

def _build_prompt(lang: str, allergens: list, flavors: list, dietary: str) -> str:
    allergen_str = ", ".join(allergens) or "none"
    flavor_str = ", ".join(flavors) or "no specific preference"
    dietary_str = dietary.strip() or "none"
    return f"""You are a Michelin-star food critic and linguistic expert helping a traveler decode a foreign menu.

User profile:
- Target language for output: {lang}
- Flavor preferences: {flavor_str}
- Allergens / foods to avoid: {allergen_str}
- Other dietary restrictions: {dietary_str}

Task: Analyze the menu image and identify every dish name visible.
For EACH dish return a JSON object with these exact keys:

- "original_name"        : string — name exactly as printed on the menu
- "translated_name"      : string — name translated into {lang}
- "pronunciation_guide"  : string — phonetic guide for the original name (e.g. "ri-ZOT-toh al-la MIL-a-nay-zeh")
- "description"          : string — 1-2 sentences in {lang} describing taste, texture, cooking style. Be specific and appetizing.
- "main_ingredients"     : array of strings — top 4-6 ingredients
- "taste_tags"           : array — pick applicable: ["Spicy","Sweet","Sour","Savory","Mild","Rich/Creamy","Bitter","Umami"]
- "calories_estimate"    : string or null — rough range e.g. "450-600 kcal"
- "allergen_warnings"    : array — list ONLY allergens from [{allergen_str}] that ARE present or highly likely in this dish. Empty array if none.
- "recommended"          : boolean — true if this dish strongly matches the flavor preferences [{flavor_str}]
- "price"                : string or null — price as printed, or null
- "image_search_keyword" : string — precise English keyword to find a real photo of this dish

Return ONLY a valid JSON array containing these objects. No markdown fences, no explanation.
"""


def call_gemini(img: Image.Image, api_key: str, lang: str, allergens: list,
                flavors: list, dietary: str):
    """Call Gemini multimodal API and return (dishes_list, error_str)."""
    payload = {
        "contents": [{
            "parts": [
                {"text": _build_prompt(lang, allergens, flavors, dietary)},
                {"inline_data": {"mime_type": "image/jpeg", "data": _image_to_b64(img)}},
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
        return None, "Request timed out. Check your network and try again."
    except requests.exceptions.RequestException as exc:
        return None, f"Network error: {exc}"

    if resp.status_code != 200:
        return None, f"Gemini API error {resp.status_code}: {resp.text[:300]}"

    try:
        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        return None, "Unexpected API response structure."

    # Strip markdown code fences if Gemini wraps output anyway
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
        raw_text = raw_text.rsplit("```", 1)[0].strip()

    try:
        dishes = json.loads(raw_text)
        if not isinstance(dishes, list):
            return None, "API returned unexpected format (expected a list)."
        return dishes, None
    except json.JSONDecodeError as exc:
        return None, f"Could not parse AI response: {exc}\n\nRaw snippet:\n{raw_text[:400]}"

def call_gemini_chat(audio_bytes, api_key: str, menu_context: list, history: list):
    """Call Gemini API for the audio chat feature."""
    audio_b64 = _audio_to_b64(audio_bytes)
    
    contents = []
    
    context_str = json.dumps(menu_context, indent=2)
    system_prompt = f"You are MenuMate, an AI assistant helping a user understand a foreign menu. Here is the menu data we extracted:\n{context_str}\n\nPlease answer the user's spoken questions concisely and helpfully based on this menu. Keep answers short and conversational. If the question is unrelated to the menu or food, politely steer them back."
    
    for msg in history:
        contents.append({
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]
        })
        
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": contents + [{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}
            ]
        }],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
    }
    
    try:
        resp = requests.post(
            GEMINI_API_URL,
            params={"key": api_key},
            json=payload,
            timeout=30,
        )
    except requests.exceptions.Timeout:
        return None, "Request timed out. Check your network and try again."
    except requests.exceptions.RequestException as exc:
        return None, f"Network error: {exc}"

    if resp.status_code != 200:
        return None, f"Gemini API error {resp.status_code}: {resp.text[:300]}"

    try:
        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return raw_text, None
    except (KeyError, IndexError):
        return None, "Unexpected API response structure."

def google_image_url(keyword: str) -> str:
    return "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote(keyword)


def fetch_cse_image(keyword: str) -> str | None:
    """Optional: fetch a real image URL via Google Custom Search API."""
    cse_key = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
    cse_id = os.getenv("GOOGLE_CSE_ID", "").strip()
    if not (cse_key and cse_id):
        return None
    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": cse_key, "cx": cse_id, "q": keyword,
                    "searchType": "image", "num": 1},
            timeout=10,
        )
        items = resp.json().get("items", [])
        return items[0]["link"] if items else None
    except Exception:
        return None


# ── Step 5 — RESULT card renderer ─────────────────────────────────────────────


def render_dish_card(dish: dict, idx: int) -> None:
    has_warning = bool(dish.get("allergen_warnings"))
    is_recommended = dish.get("recommended", False) and not has_warning
    card_class = "dish-card" + (" has-warning" if has_warning else " recommended" if is_recommended else "")

    price_html = (
        f'<span class="price-tag">{dish["price"]}</span>' if dish.get("price") else ""
    )

    tags_html = "".join(
        f'<span class="tag">{t}</span>' for t in dish.get("taste_tags", [])
    )
    if is_recommended:
        tags_html += '<span class="tag recommend-tag">✓ Matches your taste</span>'

    allergen_html = ""
    if has_warning:
        allergen_html = (
            '<div style="margin-top:0.5rem">'
            + "".join(
                f'<span class="tag warning-tag">⚠ {a}</span>'
                for a in dish["allergen_warnings"]
            )
            + "</div>"
        )

    calories_html = (
        f'<div style="font-size:0.8rem;color:#78716c;margin-top:0.25rem">'
        f'~{dish["calories_estimate"]}</div>'
        if dish.get("calories_estimate")
        else ""
    )

    ingredients = ", ".join(dish.get("main_ingredients", []))

    search_url = google_image_url(dish.get("image_search_keyword", dish["original_name"]))

    st.markdown(
        f"""
<div class="{card_class}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div class="dish-translated">{dish.get("translated_name","")}</div>
      <div class="dish-original">{dish.get("original_name","")}</div>
      <div class="dish-pronunciation">🗣 {dish.get("pronunciation_guide","")}</div>
    </div>
    {price_html}
  </div>
  <div class="dish-desc">{dish.get("description","")}</div>
  <div style="font-size:0.82rem;color:#78716c;margin-bottom:0.4rem">
    🧂 {ingredients}
  </div>
  <div>{tags_html}</div>
  {calories_html}
  {allergen_html}
  <div style="margin-top:0.75rem">
    <a href="{search_url}" target="_blank"
       style="color:#ea580c;font-weight:600;font-size:0.88rem;text-decoration:none">
      🔍 See what it looks like →
    </a>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # If Google CSE is configured, try to embed a real photo inline
    img_url = fetch_cse_image(dish.get("image_search_keyword", dish["original_name"]))
    if img_url:
        st.image(img_url, width=280)


# ── Step 1 — HOME + Steps 3/4 — SCAN / RECOGNIZE ─────────────────────────────

st.markdown("## 🍽️ MenuMate")
st.markdown("#### *Don't just translate — visualize.*")
st.markdown("---")

tab_cam, tab_upload = st.tabs(["📸 Live Camera", "📂 Upload Photo"])

image_data: Image.Image | None = None

with tab_cam:
    cam_input = st.camera_input("Point at a menu and snap")
    if cam_input:
        image_data = Image.open(cam_input)

with tab_upload:
    file_input = st.file_uploader(
        "Upload a menu photo",
        type=["jpg", "jpeg", "png", "webp"],
        help="Works with printed menus, chalkboards, digital screens.",
    )
    if file_input:
        image_data = Image.open(file_input)

if image_data:
    st.image(image_data, caption="Menu Preview", use_container_width=True)

    if not api_key:
        st.warning("Enter your Gemini API key in the sidebar to continue.")
    else:
        if st.button("✨ Analyze Menu", type="primary", use_container_width=True):
            with st.spinner("👨‍🍳 Reading the menu — this takes ~10 seconds…"):
                dishes, error = call_gemini(
                    image_data, api_key, target_lang, allergens, flavor_prefs, dietary_notes
                )

            if error:
                st.error(f"Error: {error}")

            elif dishes:
                # Save to session state for chat context
                st.session_state.menu_context = dishes
                # Clear chat history when a new menu is analyzed
                st.session_state.chat_history = []
                
                # ── Summary metrics ───────────────────────────────────────────
                warned = [d for d in dishes if d.get("allergen_warnings")]
                safe_recommended = [
                    d for d in dishes if d.get("recommended") and not d.get("allergen_warnings")
                ]

                c1, c2, c3 = st.columns(3)
                c1.metric("Dishes found", len(dishes))
                c2.metric("⚠️ Allergen alerts", len(warned))
                c3.metric("✓ Recommended", len(safe_recommended))

                # ── Step 5 — RESULT cards ─────────────────────────────────────
                if warned:
                    st.markdown(
                        '<div class="section-title">⚠️ Allergen Alerts — Approach with Caution</div>',
                        unsafe_allow_html=True,
                    )
                    for i, dish in enumerate(warned):
                        render_dish_card(dish, i)

                if safe_recommended:
                    st.markdown(
                        '<div class="section-title">✓ Recommended for You</div>',
                        unsafe_allow_html=True,
                    )
                    for i, dish in enumerate(safe_recommended):
                        render_dish_card(dish, i)

                remaining = [
                    d for d in dishes
                    if not d.get("allergen_warnings") and not d.get("recommended")
                ]
                if remaining:
                    st.markdown(
                        '<div class="section-title">📋 All Other Dishes</div>',
                        unsafe_allow_html=True,
                    )
                    for i, dish in enumerate(remaining):
                        render_dish_card(dish, i)

# ── Step 6 — AUDIO CHAT ───────────────────────────────────────────────────────

if st.session_state.menu_context:
    st.markdown("---")
    st.markdown("### 💬 Chat with MenuMate")
    st.caption("Ask questions about the menu you just scanned using your voice.")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Audio input for new question
    audio_val = st.audio_input("Record your question")
    
    if audio_val and api_key:
        with st.spinner("MenuMate is thinking..."):
            audio_bytes = audio_val.getvalue()
            # Send to Gemini
            response, chat_error = call_gemini_chat(
                audio_bytes,
                api_key,
                st.session_state.menu_context,
                st.session_state.chat_history
            )
            
            if chat_error:
                st.error(f"Error: {chat_error}")
            elif response:
                # Add to history
                # We can't easily display the user's audio back as text in the history unless we transcribe it.
                # For now, we'll just show an indicator that the user asked an audio question.
                st.session_state.chat_history.append({"role": "user", "content": "*(Audio Question)*"})
                st.session_state.chat_history.append({"role": "model", "content": response})
                
                st.rerun()

else:
    # Default empty state
    st.markdown(
        """
        <div style="text-align:center;padding:3rem 1rem;color:#78716c">
            <div style="font-size:4rem">📷</div>
            <div style="font-size:1.1rem;margin-top:0.5rem">
                Take a photo or upload a menu image to get started
            </div>
            <div style="font-size:0.88rem;margin-top:0.75rem">
                Works with any language — Italian, Japanese, French, Arabic, and more
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
