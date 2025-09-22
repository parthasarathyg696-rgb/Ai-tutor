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

# Main route - serves the complete HTML page with attractive UI
@app.route("/")
def index():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>EduBot - AI Education Tutor</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 20px;
      position: relative;
      overflow-x: hidden;
    }

    body::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" patternUnits="userSpaceOnUse" width="100" height="100"><circle cx="25" cy="25" r="1" fill="%23ffffff" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="%23ffffff" opacity="0.05"/><circle cx="50" cy="10" r="0.5" fill="%23ffffff" opacity="0.08"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>') repeat;
      pointer-events: none;
    }

    .chat-container {
      width: 100%;
      max-width: 800px;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(20px);
      border-radius: 24px;
      box-shadow: 
        0 32px 64px rgba(0, 0, 0, 0.15),
        0 16px 32px rgba(0, 0, 0, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.8);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.2);
      position: relative;
    }

    .chat-container::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
      animation: shimmer 3s ease-in-out infinite;
    }

    @keyframes shimmer {
      0%, 100% { opacity: 0.6; }
      50% { opacity: 1; }
    }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #ffffff;
      padding: 24px 32px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }

    .header::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
      animation: rotate 20s linear infinite;
    }

    @keyframes rotate {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    .header-content {
      position: relative;
      z-index: 2;
    }

    .header h1 {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
    }

    .header .subtitle {
      font-size: 14px;
      opacity: 0.9;
      font-weight: 400;
      letter-spacing: 0.5px;
    }

    .logo-icon {
      width: 40px;
      height: 40px;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      backdrop-filter: blur(10px);
    }

    .notice {
      background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
      color: #1565c0;
      padding: 16px 24px;
      font-size: 13px;
      text-align: center;
      border-bottom: 1px solid rgba(0, 0, 0, 0.05);
      font-weight: 500;
      position: relative;
    }

    .notice i {
      margin-right: 8px;
      color: #667eea;
    }

    #chatWindow {
      height: 450px;
      overflow-y: auto;
      padding: 24px;
      background: #fafafa;
      position: relative;
      scroll-behavior: smooth;
    }

    #chatWindow::-webkit-scrollbar {
      width: 6px;
    }

    #chatWindow::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.05);
      border-radius: 3px;
    }

    #chatWindow::-webkit-scrollbar-thumb {
      background: linear-gradient(135deg, #667eea, #764ba2);
      border-radius: 3px;
    }

    .message {
      margin-bottom: 20px;
      display: flex;
      align-items: flex-end;
      gap: 12px;
      animation: slideIn 0.3s ease-out;
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .message.user {
      flex-direction: row-reverse;
    }

    .message-content {
      max-width: 75%;
      padding: 16px 20px;
      border-radius: 20px;
      font-size: 14px;
      line-height: 1.6;
      position: relative;
      word-wrap: break-word;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .message.user .message-content {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-bottom-right-radius: 6px;
    }

    .message.bot .message-content {
      background: white;
      color: #333;
      border: 1px solid rgba(0, 0, 0, 0.08);
      border-bottom-left-radius: 6px;
    }

    .message-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      font-weight: 600;
      flex-shrink: 0;
    }

    .message.user .message-avatar {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      color: white;
    }

    .message.bot .message-avatar {
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      color: white;
    }

    .typing-indicator {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 12px 16px;
    }

    .typing-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #667eea;
      animation: typing 1.4s infinite ease-in-out;
    }

    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }

    @keyframes typing {
      0%, 60%, 100% {
        transform: scale(1);
        opacity: 0.7;
      }
      30% {
        transform: scale(1.3);
        opacity: 1;
      }
    }

    .input-area {
      padding: 24px;
      background: white;
      border-top: 1px solid rgba(0, 0, 0, 0.06);
      position: relative;
    }

    .input-row {
      display: flex;
      gap: 12px;
      align-items: flex-end;
      margin-bottom: 16px;
    }

    .level-selector {
      position: relative;
    }

    #levelSelect {
      padding: 12px 16px;
      border: 2px solid rgba(0, 0, 0, 0.1);
      border-radius: 12px;
      font-size: 14px;
      font-weight: 500;
      background: white;
      cursor: pointer;
      transition: all 0.2s ease;
      min-width: 140px;
    }

    #levelSelect:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .input-container {
      flex: 1;
      position: relative;
    }

    #questionInput {
      width: 100%;
      padding: 16px 60px 16px 20px;
      border: 2px solid rgba(0, 0, 0, 0.1);
      border-radius: 16px;
      font-size: 14px;
      font-family: inherit;
      resize: none;
      transition: all 0.2s ease;
      background: rgba(255, 255, 255, 0.8);
    }

    #questionInput:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
      background: white;
    }

    #questionInput::placeholder {
      color: #888;
      font-weight: 400;
    }

    #sendBtn {
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;
      border-radius: 12px;
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      transition: all 0.2s ease;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    #sendBtn:hover:not(:disabled) {
      transform: translateY(-50%) scale(1.05);
      box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }

    #sendBtn:disabled {
      background: linear-gradient(135deg, #ccc 0%, #999 100%);
      cursor: not-allowed;
      box-shadow: none;
      transform: translateY(-50%) scale(1);
    }

    .features {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .feature-tag {
      padding: 6px 12px;
      background: rgba(102, 126, 234, 0.1);
      color: #667eea;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
      border: 1px solid rgba(102, 126, 234, 0.2);
    }

    @media (max-width: 768px) {
      body {
        padding: 10px;
      }

      .chat-container {
        max-width: 100%;
        border-radius: 16px;
      }

      .header {
        padding: 20px;
      }

      .header h1 {
        font-size: 24px;
      }

      #chatWindow {
        height: 350px;
        padding: 16px;
      }

      .input-area {
        padding: 16px;
      }

      .input-row {
        flex-direction: column;
        align-items: stretch;
      }

      .message-content {
        max-width: 85%;
      }
    }

    .welcome-message {
      text-align: center;
      padding: 40px 20px;
      color: #666;
    }

    .welcome-message .icon {
      font-size: 48px;
      color: #667eea;
      margin-bottom: 16px;
    }

    .welcome-message h3 {
      font-size: 20px;
      color: #333;
      margin-bottom: 12px;
      font-weight: 600;
    }

    .welcome-message p {
      font-size: 14px;
      line-height: 1.6;
      max-width: 400px;
      margin: 0 auto;
    }
  </style>
</head>
<body>
  <div class="chat-container">
    <div class="header">
      <div class="header-content">
        <h1>
          <div class="logo-icon">
            <i class="fas fa-graduation-cap"></i>
          </div>
          EduBot
        </h1>
        <div class="subtitle">Your Personal AI Education Tutor</div>
      </div>
    </div>
    
    <div class="notice">
      <i class="fas fa-info-circle"></i>
      Specialized in Mathematics, Science, History, Literature, and all academic subjects
    </div>
    
    <div id="chatWindow">
      <div class="welcome-message">
        <div class="icon">🎓</div>
        <h3>Welcome to EduBot!</h3>
        <p>I'm here to help you learn and understand academic concepts. Ask me questions about any educational topic, and I'll provide clear, detailed explanations tailored to your level.</p>
      </div>
    </div>

    <div class="input-area">
      <div class="input-row">
        <div class="level-selector">
          <select id="levelSelect">
            <option value="beginner">📚 Beginner</option>
            <option value="advanced">🎯 Advanced</option>
          </select>
        </div>
        
        <div class="input-container">
          <input id="questionInput" type="text" placeholder="Ask me about any academic topic..." autocomplete="off" />
          <button id="sendBtn" disabled>
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
      
      <div class="features">
        <span class="feature-tag">Mathematics</span>
        <span class="feature-tag">Sciences</span>
        <span class="feature-tag">History</span>
        <span class="feature-tag">Literature</span>
        <span class="feature-tag">Languages</span>
        <span class="feature-tag">Computer Science</span>
      </div>
    </div>
  </div>

  <script>
    const chatWindow = document.getElementById('chatWindow');
    const input = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    const levelSelect = document.getElementById('levelSelect');

    let currentChatId = null;

    input.addEventListener('input', () => {
      sendBtn.disabled = !input.value.trim();
    });

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

    function clearWelcome() {
      const welcome = chatWindow.querySelector('.welcome-message');
      if (welcome) {
        welcome.remove();
      }
    }

    async function sendMessage() {
      const question = input.value.trim();
      if (!question) return;
      
      clearWelcome();
      addMessage(question, true);
      input.value = '';
      sendBtn.disabled = true;

      const level = levelSelect.value;
      addTypingIndicator();

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
        removeTypingIndicator();
        
        if (data.error) {
          addMessage(`I apologize, but I encountered an error: ${data.error}`, false);
        } else {
          currentChatId = data.chat_id;
          addMessage(data.reply.content || "I apologize, but I can only help with educational topics.", false);
        }
      } catch (error) {
        removeTypingIndicator();
        addMessage('I apologize, but I\\'m having trouble connecting right now. Please try again in a moment.', false);
      }
    }

    function addMessage(text, isUser) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
      
      const avatar = document.createElement('div');
      avatar.className = 'message-avatar';
      avatar.textContent = isUser ? '👤' : '🤖';
      
      const content = document.createElement('div');
      content.className = 'message-content';
      
      if (!isUser) {
        const cleanText = stripMarkdown(text);
        content.innerHTML = cleanText.replace(/\\n/g, '<br>');
      } else {
        content.textContent = text;
      }
      
      messageDiv.appendChild(avatar);
      messageDiv.appendChild(content);
      chatWindow.appendChild(messageDiv);
      
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function addTypingIndicator() {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'message bot typing-message';
      messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
          </div>
        </div>
      `;
      chatWindow.appendChild(messageDiv);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function removeTypingIndicator() {
      const typingMsg = chatWindow.querySelector('.typing-message');
      if (typingMsg) {
        typingMsg.remove();
      }
    }

    sendBtn.addEventListener('click', sendMessage);
    
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !sendBtn.disabled) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-focus input
    input.focus();
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
        system_prompt = """You are EduBot, an AI Education Tutor designed exclusively for educational purposes. You MUST follow these rules:

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
        system_prompt = """You are EduBot, an AI Education Tutor designed exclusively for educational purposes. You MUST follow these rules:

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
    return jsonify({"status": "healthy", "service": "EduBot - AI Education Tutor"}), 200

# Get port from environment variable
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)
