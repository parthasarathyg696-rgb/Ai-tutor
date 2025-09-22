from __future__ import annotations

import os
import uuid
from typing import Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI, OpenAIError

# ------------------------------------------------------------------
# 1.  Load secrets from .env (OPENAI_API_KEY must be set there)
# ------------------------------------------------------------------
load_dotenv()  # looks for .env in current or parent folders
api_key: str | None = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY missing – add it to .env or env vars")

client = OpenAI(api_key=api_key)

# ------------------------------------------------------------------
# 2.  Basic Flask app + CORS
# ------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# ------------------------------------------------------------------
# 3.  In-memory chat store
# ------------------------------------------------------------------
chat_histories: Dict[str, List[dict]] = {}

def new_id() -> str:
    return str(uuid.uuid4())

# ------------------------------------------------------------------
# 4.  Routes
# ------------------------------------------------------------------
@app.route("/chat", methods=["POST"])
def chat() -> tuple:
    data = request.get_json(silent=True) or {}
    user_message: str | None = data.get("message")
    level: str = data.get("level", "beginner").lower()
    chat_id: str = data.get("chat_id") or new_id()

    if not user_message:
        return jsonify({"error": "field 'message' is required"}), 400

    chat_histories.setdefault(chat_id, []).append(
        {"role": "user", "content": user_message, "message_id": new_id()}
    )

    # ✅ Enhanced system prompt with formatting instructions and no markdown
    if level == "beginner":
        system_prompt = """You are an AI tutor. Always explain concepts in very simple, beginner-friendly terms.

IMPORTANT FORMATTING RULES:
- Do NOT use any markdown formatting like **bold**, *italic*, or __underline__
- Do NOT use asterisks (*) or underscores (_) for emphasis
- Use plain text only
- Start with a clear heading or definition followed by a colon
- Put the main content on the next line after the heading
- Use one blank line between different sections or topics
- Write in short, clear paragraphs
- Use bullet points with hyphens (-) or numbers (1, 2, 3) when helpful

Example format:
Definition of Photosynthesis:
Photosynthesis is the process plants use to make food from sunlight.

How it works:
1. Plants collect sunlight through their leaves
2. They combine sunlight with water and carbon dioxide
3. This creates sugar (food) and oxygen

Why it matters:
This process is important because it gives us the oxygen we breathe."""
    else:
        system_prompt = """You are an AI tutor. Provide advanced, detailed, structured explanations.

IMPORTANT FORMATTING RULES:
- Do NOT use any markdown formatting like **bold**, *italic*, or __underline__
- Do NOT use asterisks (*) or underscores (_) for emphasis
- Use plain text only
- Start with a comprehensive definition or overview followed by a colon
- Organize information into clear sections with headings followed by colons
- Use one blank line between different sections
- Include technical details and examples
- Structure with bullet points using hyphens (-) or numbered lists (1, 2, 3)

Example format:
Cellular Respiration - Advanced Overview:
Cellular respiration is a multi-stage biochemical process that converts glucose into ATP.

The Three Main Stages:
1. Glycolysis - occurs in the cytoplasm
2. Krebs Cycle - occurs in the mitochondrial matrix  
3. Electron Transport Chain - occurs on the inner mitochondrial membrane

Chemical Equation:
C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + ATP

Significance in Metabolism:
This process is fundamental to all aerobic life forms as it provides the primary energy currency for cellular processes."""

    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in chat_histories[chat_id]
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500,  # ✅ Increased token limit for better formatting
        )
        bot_reply = response.choices[0].message.content.strip()
    except OpenAIError as e:
        return jsonify({"error": f"OpenAI API error: {e}"}), 502

    assistant_msg = {"role": "assistant", "content": bot_reply, "message_id": new_id()}
    chat_histories[chat_id].append(assistant_msg)

    return (
        jsonify(
            {
                "chat_id": chat_id,
                "reply": {
                    "message_id": assistant_msg["message_id"],
                    "content": bot_reply,
                },
            }
        ),
        200,
    )

# ------------------------------------------------------------------
# 5.  Entry-point
# ------------------------------------------------------------------
# Get port from environment variable (Render sets this automatically)
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)
