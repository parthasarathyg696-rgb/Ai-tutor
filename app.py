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

def is_educational_content(message: str) -> bool:
    """Check if the message is educational/academic content"""
    non_educational_keywords = [
        'joke', 'funny', 'entertainment', 'movie', 'game', 'sport', 'gossip',
        'celebrity', 'dating', 'relationship', 'personal', 'private', 'hack',
        'illegal', 'violence', 'weapon', 'drug', 'adult', 'inappropriate',
        'password', 'credit card', 'money', 'investment', 'trading', 'crypto',
        'political', 'religion', 'controversial', 'offensive'
    ]
    
    educational_keywords = [
        'learn', 'study', 'explain', 'teach', 'understand', 'concept', 'theory',
        'formula', 'equation', 'definition', 'example', 'homework', 'assignment',
        'exam', 'test', 'quiz', 'subject', 'topic', 'lesson', 'tutorial',
        'mathematics', 'science', 'history', 'geography', 'literature', 'language',
        'physics', 'chemistry', 'biology', 'computer', 'programming', 'technology',
        'engineering', 'medicine', 'law', 'economics', 'psychology', 'philosophy',
        'art', 'music', 'education', 'academic', 'research', 'analysis'
    ]
    
    message_lower = message.lower()
    
    # Check for non-educational content
    for keyword in non_educational_keywords:
        if keyword in message_lower:
            return False
    
    # Check for educational content
    for keyword in educational_keywords:
        if keyword in message_lower:
            return True
    
    # If no clear indicators, assume educational (to be safe)
    return True

# Main route - serves the complete HTML page
@app.route("/")
def index():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>AI Education Tutor</title>
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

    .notice {
      background: #e3f2fd;
      color: #1565c0;
      padding: 10px;
      font-size: 12px;
      text-align: center;
      border-bottom: 1px solid #ddd;
    }

    #chatWindow {
      height: 350px;
      overflow-y: auto;
      border: 1px solid #ccc;
      padding: 10px;
      display: flex;
      flex-direction: column;
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
    <div class="header">📚 AI Education Tutor</div>
    <div class="notice">This AI tutor only answers educational and academic questions</div>
    <div id="chatWindow"></div>

    <div class="footer">
      <select id="levelSelect">
        <option value="beginner">Beginner Level</option>
        <option value="advanced">Advanced Level</option>
      </select>
      <input id="questionInput" type="text" placeholder="Ask an educational question..." />
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
      addMessage('AI Tutor is analyzing your question...', false);

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
          addMessage(data.reply.content || "I apologize, but I can only help with educational topics.", false);
        }
      } catch (error) {
        removeTypingMessage();
        addMessage('Error connecting to tutor. Please try again.', false);
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
        if (lastMsg.textContent === 'AI Tutor is analyzing your question...') {
          chatWindow.removeChild(lastMsg);
        }
      }
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !sendBtn.disabled) sendMessage();
    });

    // Add initial welcome message
    window.onload = function() {
      addMessage('Welcome! I am your AI Education Tutor. I can help you with academic subjects like Mathematics, Science, History, Literature, Languages, and more. Please ask me educational questions only.', false);
    };
  </script>
</body>
</html>
    '''

# Chat endpoint with educational content filtering
@app.route("/chat", methods=["POST"])
def chat() -> tuple:
    data = request.get_json(silent=True) or {}
    user_message: str | None = data.get("message")
    level: str = data.get("level", "beginner").lower()
    chat_id: str = data.get("chat_id") or new_id()

    if not user_message:
        return jsonify({"error": "Please provide a message"}), 400

    # Check if the message is educational content
    if not is_educational_content(user_message):
        return jsonify({
            "chat_id": chat_id,
            "reply": {
                "message_id": new_id(),
                "content": "I'm sorry, but I can only help with educational and academic topics. Please ask me questions related to subjects like Mathematics, Science, History, Literature, Languages, Computer Science, or other academic fields."
            }
        }), 200

    chat_histories.setdefault(chat_id, []).append(
        {"role": "user", "content": user_message, "message_id": new_id()}
    )

    # Enhanced system prompts with strict educational focus
    if level == "beginner":
        system_prompt = """You are an AI Education Tutor designed exclusively for educational purposes. You MUST follow these rules:

STRICT CONTENT RULES:
- ONLY answer questions related to academic subjects: Mathematics, Science, History, Geography, Literature, Languages, Computer Science, Arts, Music, Philosophy, Psychology, Economics, Medicine, Engineering, Law, and other educational topics
- REFUSE to answer questions about: entertainment, jokes, personal advice, relationships, politics, religion, controversial topics, illegal activities, violence, adult content, or non-educational topics
- If asked non-educational questions, politely redirect to educational content

EDUCATIONAL APPROACH - BEGINNER LEVEL:
- Explain concepts in very simple, beginner-friendly terms
- Use everyday examples and analogies
- Break down complex topics into small, digestible parts
- Encourage questions and curiosity
- Provide step-by-step explanations

FORMATTING RULES:
- Do NOT use markdown formatting (**bold**, *italic*, etc.)
- Use plain text only
- Start with clear headings followed by colons
- Use numbered lists (1, 2, 3) or bullet points with hyphens (-)
- Separate sections with blank lines
- Keep explanations clear and structured

RESPONSE STRUCTURE:
Topic: [Clear topic name]
Simple Explanation: [Easy-to-understand definition]
Key Points: [Main concepts broken down]
Example: [Real-world example if helpful]
Why It Matters: [Educational significance]

Remember: You are here to educate and inspire learning in academic subjects only."""

    else:  # advanced level
        system_prompt = """You are an AI Education Tutor designed exclusively for educational purposes. You MUST follow these rules:

STRICT CONTENT RULES:
- ONLY answer questions related to academic subjects: Mathematics, Science, History, Geography, Literature, Languages, Computer Science, Arts, Music, Philosophy, Psychology, Economics, Medicine, Engineering, Law, and other educational topics
- REFUSE to answer questions about: entertainment, jokes, personal advice, relationships, politics, religion, controversial topics, illegal activities, violence, adult content, or non-educational topics
- If asked non-educational questions, politely redirect to educational content

EDUCATIONAL APPROACH - ADVANCED LEVEL:
- Provide detailed, comprehensive explanations
- Include technical terminology and precise definitions
- Discuss underlying principles and theories
- Make connections between different concepts
- Encourage critical thinking and analysis
- Reference established academic sources when relevant

FORMATTING RULES:
- Do NOT use markdown formatting (**bold**, *italic*, etc.)
- Use plain text only
- Start with comprehensive headings followed by colons
- Use numbered lists (1, 2, 3) for complex processes
- Use bullet points with hyphens (-) for related concepts
- Organize information into clear sections
- Include relevant formulas, equations, or technical details

RESPONSE STRUCTURE:
Advanced Topic Analysis: [Comprehensive topic overview]
Theoretical Foundation: [Underlying principles and theories]
Key Components: [Detailed breakdown of main elements]
Applications: [How the concept is used or applied]
Connections: [Links to related academic concepts]
Further Study: [Suggestions for deeper learning]

Remember: You are here to provide rigorous academic education in scholarly subjects only."""

    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in chat_histories[chat_id]
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,  # Lower temperature for more focused, educational responses
            max_tokens=600,   # Increased for detailed educational explanations
            presence_penalty=0.1,  # Slight penalty to avoid repetitive responses
            frequency_penalty=0.1  # Slight penalty for varied vocabulary
        )
        bot_reply = response.choices[0].message.content.strip()
        
        # Additional safety check - if response seems non-educational, provide fallback
        if not is_educational_content(bot_reply):
            bot_reply = "I apologize, but I can only provide assistance with educational and academic topics. Please ask me about subjects like Mathematics, Science, History, Literature, or other academic fields, and I'll be happy to help you learn!"

    except OpenAIError as e:
        return jsonify({"error": f"Unable to process your educational query at this time: {str(e)}"}), 502

    assistant_msg = {"role": "assistant", "content": bot_reply, "message_id": new_id()}
    chat_histories[chat_id].append(assistant_msg)

    return jsonify({
        "chat_id": chat_id,
        "reply": {
            "message_id": assistant_msg["message_id"],
            "content": bot_reply,
        },
    }), 200

# Health check endpoint
@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "AI Education Tutor"}), 200

# Get port from environment variable
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)
