# 🍽️ MenuMate

> **Don't just translate — visualize.**

MenuMate is an AI-powered menu scanner that helps travelers decode foreign menus instantly. Point your camera at any menu — Italian, Japanese, French, Arabic — and get dish photos, plain-language descriptions, taste tags, calorie estimates, and allergen alerts in your language.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange?logo=google)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Demo

| Scan | Result Card |
|------|-------------|
| Upload or snap a photo of any menu | Get translated dish cards with allergen alerts |

---

## Features

| Priority | Feature | Description |
|----------|---------|-------------|
| P0 | **Live camera / upload** | Snap or upload a menu photo in any language |
| P0 | **Auto language detection** | Gemini identifies the menu language automatically |
| P0 | **AI dish cards** | Original name · translation · pronunciation guide · 1-sentence description |
| P0 | **Real dish image search** | One-click link to real photos from the web |
| P0 | **User profile** | Set your target language, flavor preferences, allergens, and dietary restrictions |
| P1 | **Allergen alerts** | Dishes containing your flagged ingredients are highlighted in red |
| P1 | **Taste tags & calories** | Spicy / Sweet / Savory / Creamy tags + rough calorie estimate |
| P1 | **Personalized recommendations** | Dishes matching your flavor profile are highlighted in green |
| P2 | **Pronunciation guide** | Phonetic guide so you can order confidently |

---

## Getting Started

### Prerequisites

- Python 3.10+
- A free [Gemini API key](https://aistudio.google.com/apikey)

### Installation

```bash
git clone https://github.com/tanshuai2008/MenuMate.git
cd MenuMate
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Open `.env` and fill in your key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Optionally, add Google Custom Search credentials to embed real dish photos inline (otherwise the app links to Google Image Search):

```env
GOOGLE_CSE_API_KEY=your_google_custom_search_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id_here
```

### Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## User Flow

```
Open App
   │
   ▼
[Profile Sidebar]  ── set language, allergens, flavor prefs
   │
   ▼
[Scan / Upload]  ── live camera snap  or  upload a photo
   │
   ▼
[Recognize]  ── Gemini 2.5 Flash reads the menu, detects language
   │
   ▼
[Result Cards]  ── translated name · pronunciation · description
                   taste tags · calories · ⚠️ allergen alert · 🔍 photo link
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| AI / OCR | Google Gemini 2.5 Flash (multimodal) |
| Image search | Google Custom Search API *(optional)* / Google Image Search links |
| Config | python-dotenv |

---

## Security

- API keys are loaded from `.env` (gitignored) or environment variables — **never hardcoded**
- `.env.example` provides a safe key template for contributors
- `.streamlit/secrets.toml` is also gitignored

---

## Roadmap

- [ ] Bounding-box overlay on the menu image (highlight detected dish names)
- [ ] Text-to-speech pronunciation playback (TTS)
- [ ] Location-aware image search (pull photos from Yelp / Google Reviews for the current restaurant)
- [ ] Flutter mobile app for native camera experience
- [ ] Offline mode / cached results

---

## License

MIT
