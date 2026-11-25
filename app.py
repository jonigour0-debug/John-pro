"""Hasi Ghar - AI joke maker website (Flask + Claude API)."""
import json
import os
import random

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

try:
    import anthropic
except ImportError:  # app phir bhi chalegi, bas backup jokes ke saath
    anthropic = None

app = Flask(__name__)

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=API_KEY) if (anthropic and API_KEY) else None

LANGUAGES = {
    "hinglish": "Hinglish (Hindi in Roman script, jaise dost aapas mein baat karte hain)",
    "hindi": "Hindi (Devanagari script)",
    "english": "English",
}
STYLES = {
    "funny": "light-hearted aur sabko hasane wale",
    "pun": "wordplay aur puns wale",
    "desi": "desi, roz-marra ki zindagi wale (chai, exam, shaadi, traffic, mummy-papa)",
    "oneliner": "ek line ke sharp one-liners",
    "dad": "dad-joke style, thode cheesy",
}

# API key na ho ya API fail ho jaye to ye jokes dikhenge
BACKUP_JOKES = [
    "Teacher: Tum late kyun aaye? Student: Sir, sign board pe likha tha 'School ahead, go slow'.",
    "Mera WiFi aur meri kismat ek jaise hain, dono ko pata hai kab dhokha dena hai.",
    "Doctor: Aapko aaram ki zaroorat hai. Patient: Wo to Sunday ko bhi nahi milta, doctor sahab.",
    "Exam se pehle: 'Sab aata hai.' Exam ke baad: 'Question paper out of syllabus tha.'",
    "Chai aur deadline mein ek cheez common hai: dono ke bina subah shuru nahi hoti.",
    "Biryani aur main ek jaise hain: dono mein 'aloo' hone ka shak hamesha rehta hai.",
]


def build_prompt(topic, language, style, count):
    return f"""Tum ek mazedaar comedy writer ho. {count} bilkul alag jokes likho.

Topic: {topic or 'koi bhi random topic'}
Bhasha: {LANGUAGES[language]}
Style: {STYLES[style]}

Rules:
- Joke clean ho. Kisi dharm, jaati, ling, rang, ya community ka mazaak nahi.
- Har joke chhota ho (maximum 3 line).
- Jokes ek dusre se different hon.
- Sirf ek JSON array do, jaise: ["joke 1", "joke 2"]. Koi aur text ya backticks nahi."""


def parse_jokes(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    jokes = json.loads(text.strip())
    return [str(j).strip() for j in jokes if str(j).strip()]


@app.route("/")
def index():
    return render_template("index.html", ai_on=client is not None)


@app.route("/api/jokes", methods=["POST"])
def make_jokes():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()[:60]
    language = data.get("language", "hinglish")
    style = data.get("style", "funny")
    try:
        count = max(1, min(int(data.get("count", 3)), 5))
    except (TypeError, ValueError):
        count = 3

    if language not in LANGUAGES or style not in STYLES:
        return jsonify(error="Language ya style galat hai. Page refresh karke dobara try karo."), 400

    if client is None:
        jokes = random.sample(BACKUP_JOKES, min(count, len(BACKUP_JOKES)))
        return jsonify(jokes=jokes, source="backup")

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": build_prompt(topic, language, style, count)}],
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        jokes = parse_jokes(text)
        if not jokes:
            raise ValueError("empty")
        return jsonify(jokes=jokes[:count], source="ai")
    except Exception as exc:  # noqa: BLE001
        app.logger.error("Joke generation failed: %s", exc)
        jokes = random.sample(BACKUP_JOKES, min(count, len(BACKUP_JOKES)))
        return jsonify(jokes=jokes, source="backup",
                       notice="AI abhi jawab nahi de raha, isliye ye ready-made jokes hain.")


if __name__ == "__main__":
    app.run(debug=True)
