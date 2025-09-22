from __future__ import annotations

import os
import uuid
from typing import Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI, OpenAIError

# Load environment variables
load_dotenv()
api_key: str | None = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY missing – add it to .env or env vars")

client = OpenAI(api_key=api_key)

# Flask app setup
app = Flask(__name__)
CORS(app)

# In-memory chat store
chat_histories: Dict[str, List[dict]] = {}

def new_id() -> str:
    return str(uuid.uuid4())

# ✅ MAIN ROUTE - Serves the complete HTML page with embedded CSS and JavaScript
@app.route("/")
def index():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>AI Tutor Chatbot</title>
  <style>
    body {
      font-family: "Segoe UI", Tahoma, sans-serif;
      background: #f4f6fb;
      margin: 0;
      padding: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
    }

    .chat-container {
      width: 500px;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.1);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .header {
      background: #4a90e2;
      color: #fff;
      padding: 15px;
      font-size: 18px;
      text-align: center;
    }

    #chatWindow {
      height: 400px;
      overflow-y: auto;
      border: 1px solid #ccc;
      padding: 10px;
      display: flex;
      flex-direction: column;
    }

    .message {
      margin-bottom: 12px;
      line-height: 1.4;
      padding: 10px 14px;
      border-radius: 10px;
      max-width: 80%;
    }

    .user-message {
      background: #e1f5fe;
      align-self: flex-end;
      text-align: right;
    }

    .bot-message {
      background: #f1f1f1;
      align-self: flex-start;
    }

    .footer {
      display: flex;
      gap: 8px;
      padding: 12px;
      border-top: 1px solid #ddd;
      background: #fafafa;
    }

    #questionInput {
      flex: 1;
      padding: 10px;
      border-radius: 8px;
      border: 1px solid #ccc;
      font-size: 14px;
    }

    #levelSelect {
      padding: 8px;
      border-radius: 8px;
      border: 1px solid #ccc;
      font-size: 14px;
    }

    #sendBtn {
      padding: 10px 16px;
      background: #4a90e2;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      transition: background 0.2s;
    }

    #sendBtn:disabled {
      background: #ccc;
      cursor: not-allowed;
    }

    #sendBtn:hover:enabled {
      background: #357ABD;
    }
  </style>
</head>
<body>
  <div class="chat-container">
    <div class="header">🤖 AI Tutor Chatbot</div>
    <div id="chatWindow"></div>

    <div class="footer">
      <select id="levelSelect">
        <option value="beginner">Beginner</option>
        <option value="advanced">Advanced</option>
      </select>
      <input id="questionInput" type="text" placeholder="Ask your question here..." />
      <button id="sendBtn" disabled>Send</button>
    </div>
  </div>

  <script>
    const chatWindow = document.getElementById('chatWindow');
    const input = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    const levelSelect = document.getElementById('levelSelect');

    let currentChatId = null;

    input.addEventListener('input', () => sendBtn.disabled = !input.value.trim());

    function stripMarkdown(text) {
      return text
        .replace(/\\*\\*(.+?)\\*\\*/g, '$1')
        .replace(/__(.+?)__/g, '$1')
        .replace(/\\*(.+?)\\*/g, '$1')
        .replace(/_(.+?)_/g, '$1')
        .replace(/~~(.+?)~~/g, '$1')
        .replace(/`(.+?)`/g, '$1')
        .replace(/^#{1,6}\\s+(.+)$/gm, '$1')
        .replace(/\\[(.+?)\\]\\(.+?\\)/g, '$1')
        .replace(/[*_]/g, '');
    }

    async function sendMessage() {
      const question = input.value.trim();
      if (!question) return;
      addMessage(question, true);
      input.value = '';
      sendBtn.disabled = true;

      const level = levelSelect.value;
      addMessage('AI Tutor is typing...', false);

      try {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            message: question,
            level: level,
            chat_id: currentChatId
          })
        });
        
        const data = await res.json();
        removeTypingMessage();
        
        if (data.error) {
          addMessage(`Error: ${data.error}`, false);
        } else {
          currentChatId = data.chat_id;
          addMessage(data.reply.content || "Sorry, I didn't get that.", false);
        }
      } catch (error) {
        removeTypingMessage();
        addMessage('Error reaching server.', false);
      }
    }

    function addMessage(text, isUser) {
      const msg = document.createElement('div');
      msg.style.padding = '8px';
      msg.style.margin = '4px';
      msg.style.backgroundColor = isUser ? '#0078d7' : '#e0e0e0';
      msg.style.color = isUser ? 'white' : 'black';
      msg.style.borderRadius = '10px';
      msg.style.maxWidth = '80%';
      
      if (!isUser) {
        const cleanText = stripMarkdown(text);
        msg.innerHTML = cleanText.replace(/\\n/g, '<br>');
        msg.style.whiteSpace = 'normal';
        msg.style.lineHeight = '1.4';
      } else {
        msg.textContent = text;
      }

      msg.style.alignSelf = isUser ? 'flex-end' : 'flex-start';
      chatWindow.appendChild(msg);

      const isAtBottom = chatWindow.scrollHeight - chatWindow.scrollTop <= chatWindow.clientHeight + 50;
      if (isAtBottom) {
        chatWindow.scrollTop = chatWindow.scrollHeight;
      }
    }

    function removeTypingMessage() {
      const msgs = chatWindow.childNodes;
      if (msgs.length) {
        const lastMsg = msgs[msgs.length - 1];
        if (lastMsg.textContent === 'AI Tutor is typing...') {
          chatWindow.removeChild(lastMsg);
        }
      }
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !sendBtn.disabled) sendMessage();
    });
  </script>
</body>
</html>
    '''

# Your existing chat route
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
- Use bullet points with hyphens (-) or numbers (1, 2, 3) when helpful"""
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
- Structure with bullet points using hyphens (-) or numbered lists (1, 2, 3)"""

    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in chat_histories[chat_id]
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        bot_reply = response.choices[0].message.content.strip()
    except OpenAIError as e:
        return jsonify({"error": f"OpenAI API error: {e}"}), 502

    assistant_msg = {"role": "assistant", "content": bot_reply, "message_id": new_id()}
    chat_histories[chat_id].append(assistant_msg)

    return jsonify({
        "chat_id": chat_id,
        "reply": {
            "message_id": assistant_msg["message_id"],
            "content": bot_reply,
        },
    }), 200

# Get port from environment variable
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)
