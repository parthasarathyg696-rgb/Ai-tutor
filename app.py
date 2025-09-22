from __future__ import annotations

import os
import uuid
import logging
from typing import Dict, List
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI, OpenAIError

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key: str | None = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY missing – add it to .env or env vars")

client = OpenAI(api_key=api_key)

# Flask app setup
app = Flask(__name__)
CORS(app, origins=["*"])

# Enhanced in-memory chat store with cleanup
chat_histories: Dict[str, Dict] = {}
CHAT_CLEANUP_HOURS = 24  # Clean up chats older than 24 hours

def new_id() -> str:
    return str(uuid.uuid4())

def cleanup_old_chats():
    """Clean up chat histories older than specified hours"""
    current_time = datetime.now()
    expired_chats = []
    
    for chat_id, chat_data in chat_histories.items():
        if current_time - chat_data.get('created_at', current_time) > timedelta(hours=CHAT_CLEANUP_HOURS):
            expired_chats.append(chat_id)
    
    for chat_id in expired_chats:
        del chat_histories[chat_id]
    
    if expired_chats:
        logger.info(f"Cleaned up {len(expired_chats)} expired chat sessions")

def is_educational_content(message: str) -> bool:
    """Enhanced educational content detection for production"""
    
    # Strictly blocked content
    blocked_keywords = [
        'porn', 'sex', 'nude', 'explicit', 'adult content', 'sexual',
        'violence', 'kill', 'murder', 'weapon', 'bomb', 'terrorist', 'hate',
        'drug dealer', 'illegal drugs', 'cocaine', 'heroin', 'marijuana sale',
        'hack bank', 'steal money', 'credit card fraud', 'illegal activity',
        'suicide', 'self harm', 'racist', 'hate speech', 'discrimination'
    ]
    
    # Comprehensive educational topics
    educational_topics = [
        # Core Academic Subjects
        'mathematics', 'math', 'algebra', 'geometry', 'calculus', 'trigonometry', 'statistics',
        'physics', 'chemistry', 'biology', 'science', 'botany', 'zoology', 'ecology',
        'history', 'geography', 'civics', 'political science', 'social studies',
        'english', 'literature', 'grammar', 'writing', 'reading', 'poetry', 'linguistics',
        'economics', 'commerce', 'accounting', 'business studies', 'finance',
        'philosophy', 'psychology', 'sociology', 'anthropology', 'archaeology',
        'art', 'music', 'dance', 'drama', 'theater', 'fine arts', 'design',
        
        # STEM Fields
        'computer science', 'programming', 'software engineering', 'data science',
        'artificial intelligence', 'ai', 'machine learning', 'deep learning',
        'algorithms', 'data structures', 'databases', 'networks', 'cybersecurity',
        'engineering', 'mechanical', 'electrical', 'civil', 'chemical', 'aerospace',
        'biotechnology', 'nanotechnology', 'robotics', 'automation',
        
        # Medical & Health Sciences
        'medicine', 'anatomy', 'physiology', 'pharmacology', 'pathology',
        'dentistry', 'nursing', 'public health', 'nutrition', 'psychology',
        'human body', 'organs', 'bones', 'muscles', 'blood', 'cells',
        
        # Languages & Communication
        'languages', 'spanish', 'french', 'german', 'chinese', 'japanese',
        'communication', 'public speaking', 'debate', 'journalism',
        
        # Research & Academic Skills
        'research', 'thesis', 'dissertation', 'analysis', 'methodology',
        'statistics', 'data analysis', 'academic writing', 'citations',
        
        # General Academic Terms
        'study', 'learn', 'education', 'academic', 'school', 'college', 'university',
        'exam', 'test', 'assignment', 'homework', 'project', 'quiz',
        'concept', 'theory', 'principle', 'formula', 'equation', 'definition',
        'explanation', 'example', 'solution', 'problem solving'
    ]
    
    # Question indicators
    academic_indicators = [
        'what is', 'what are', 'explain', 'how to', 'how do', 'how does',
        'define', 'definition of', 'meaning of', 'solve', 'calculate',
        'difference between', 'compare', 'contrast', 'types of', 'kinds of',
        'examples of', 'formula for', 'understand', 'learn about',
        'tell me about', 'describe', 'which is', 'which are',
        'where is', 'when was', 'when did', 'why is', 'why does',
        'how many', 'how much', 'who is', 'who was', 'help me'
    ]
    
    # Greetings
    greetings = [
        'hi', 'hello', 'hey', 'hii', 'hello there', 'good morning',
        'good afternoon', 'good evening', 'namaste', 'greetings'
    ]
    
    message_lower = message.lower().strip()
    
    # Block inappropriate content
    for blocked in blocked_keywords:
        if blocked in message_lower:
            return False
    
    # Allow greetings
    if any(greeting == message_lower for greeting in greetings):
        return True
    
    # Allow educational content
    for topic in educational_topics:
        if topic in message_lower:
            return True
    
    # Check for academic question patterns
    for indicator in academic_indicators:
        if indicator in message_lower:
            return True
    
    # Allow short questions (likely educational)
    if len(message.split()) <= 10 and '?' in message:
        return True
    
    # Default to allowing (educational bias)
    return True

# Production-level HTML with enhanced features
@app.route("/")
def index():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>EduBot - AI Academic Tutor</title>
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
      overflow-x: hidden;
    }

    .chat-container {
      width: 100%;
      max-width: 900px;
      background: rgba(255, 255, 255, 0.98);
      backdrop-filter: blur(25px);
      border-radius: 24px;
      box-shadow: 
        0 40px 80px rgba(0, 0, 0, 0.12),
        0 20px 40px rgba(0, 0, 0, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.9);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.3);
      position: relative;
    }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #ffffff;
      padding: 28px 36px;
      text-align: center;
      position: relative;
    }

    .header h1 {
      font-size: 32px;
      font-weight: 700;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 14px;
    }

    .header .subtitle {
      font-size: 15px;
      opacity: 0.92;
      font-weight: 400;
    }

    .logo-icon {
      width: 42px;
      height: 42px;
      background: rgba(255, 255, 255, 0.25);
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      backdrop-filter: blur(15px);
    }

    .notice {
      background: linear-gradient(135deg, #e8f4fd 0%, #f8f0ff 100%);
      color: #1565c0;
      padding: 18px 28px;
      font-size: 14px;
      text-align: center;
      font-weight: 500;
      border-bottom: 1px solid rgba(0, 0, 0, 0.04);
    }

    .notice i {
      margin-right: 10px;
      color: #667eea;
    }

    #chatWindow {
      height: 480px;
      overflow-y: auto;
      padding: 28px;
      background: #fafbfc;
      position: relative;
      scroll-behavior: smooth;
    }

    #chatWindow::-webkit-scrollbar {
      width: 8px;
    }

    #chatWindow::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.04);
      border-radius: 4px;
    }

    #chatWindow::-webkit-scrollbar-thumb {
      background: linear-gradient(135deg, #667eea, #764ba2);
      border-radius: 4px;
    }

    .message {
      margin-bottom: 24px;
      display: flex;
      align-items: flex-end;
      gap: 14px;
      animation: slideIn 0.4s ease-out;
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(24px);
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
      max-width: 78%;
      padding: 18px 22px;
      border-radius: 22px;
      font-size: 15px;
      line-height: 1.6;
      word-wrap: break-word;
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
      position: relative;
    }

    .message.user .message-content {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-bottom-right-radius: 8px;
    }

    .message.bot .message-content {
      background: white;
      color: #2d3748;
      border: 1px solid rgba(0, 0, 0, 0.06);
      border-bottom-left-radius: 8px;
    }

    .message-avatar {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 15px;
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
      gap: 6px;
      padding: 14px 18px;
    }

    .typing-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #667eea;
      animation: typing 1.5s infinite ease-in-out;
    }

    .typing-dot:nth-child(2) { animation-delay: 0.3s; }
    .typing-dot:nth-child(3) { animation-delay: 0.6s; }

    @keyframes typing {
      0%, 60%, 100% {
        transform: scale(1);
        opacity: 0.7;
      }
      30% {
        transform: scale(1.4);
        opacity: 1;
      }
    }

    .input-area {
      padding: 28px;
      background: white;
      border-top: 1px solid rgba(0, 0, 0, 0.04);
    }

    .input-row {
      display: flex;
      gap: 14px;
      align-items: flex-end;
      margin-bottom: 18px;
    }

    #levelSelect {
      padding: 14px 18px;
      border: 2px solid rgba(0, 0, 0, 0.08);
      border-radius: 14px;
      font-size: 15px;
      font-weight: 500;
      background: white;
      cursor: pointer;
      transition: all 0.3s ease;
      min-width: 160px;
    }

    #levelSelect:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.12);
    }

    .input-container {
      flex: 1;
      position: relative;
    }

    #questionInput {
      width: 100%;
      padding: 18px 70px 18px 22px;
      border: 2px solid rgba(0, 0, 0, 0.08);
      border-radius: 18px;
      font-size: 15px;
      font-family: inherit;
      background: rgba(255, 255, 255, 0.9);
      transition: all 0.3s ease;
    }

    #questionInput:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.12);
      background: white;
    }

    #questionInput::placeholder {
      color: #a0a0a0;
    }

    #sendBtn {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      width: 44px;
      height: 44px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;
      border-radius: 14px;
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      transition: all 0.3s ease;
      box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
    }

    #sendBtn:hover:not(:disabled) {
      transform: translateY(-50%) scale(1.05);
      box-shadow: 0 6px 18px rgba(102, 126, 234, 0.45);
    }

    #sendBtn:disabled {
      background: #d1d5db;
      cursor: not-allowed;
      box-shadow: none;
      transform: translateY(-50%);
    }

    .features {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }

    .feature-tag {
      padding: 8px 14px;
      background: rgba(102, 126, 234, 0.08);
      color: #667eea;
      border-radius: 22px;
      font-size: 13px;
      font-weight: 500;
      border: 1px solid rgba(102, 126, 234, 0.15);
    }

    .welcome-message {
      text-align: center;
      padding: 48px 24px;
      color: #6b7280;
    }

    .welcome-message .icon {
      font-size: 56px;
      color: #667eea;
      margin-bottom: 20px;
    }

    .welcome-message h3 {
      font-size: 24px;
      color: #1f2937;
      margin-bottom: 16px;
      font-weight: 600;
    }

    .welcome-message p {
      font-size: 16px;
      line-height: 1.7;
      max-width: 520px;
      margin: 0 auto;
    }

    .typing-effect {
      animation: typing-cursor 1.2s infinite;
    }

    @keyframes typing-cursor {
      0%, 50% { border-right: 2px solid transparent; }
      51%, 100% { border-right: 2px solid #667eea; }
    }

    .follow-up-suggestions {
      margin-top: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .follow-up-btn {
      padding: 6px 12px;
      background: rgba(102, 126, 234, 0.06);
      border: 1px solid rgba(102, 126, 234, 0.2);
      border-radius: 16px;
      font-size: 13px;
      color: #667eea;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .follow-up-btn:hover {
      background: rgba(102, 126, 234, 0.12);
      border-color: rgba(102, 126, 234, 0.3);
    }

    @media (max-width: 768px) {
      body { padding: 12px; }
      .chat-container { border-radius: 18px; }
      .header { padding: 24px; }
      .header h1 { font-size: 26px; }
      #chatWindow { height: 380px; padding: 20px; }
      .input-area { padding: 20px; }
      .input-row { flex-direction: column; align-items: stretch; }
      .message-content { max-width: 88%; }
    }

    .connection-status {
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
      display: none;
    }

    .connection-status.connecting {
      background: #fbbf24;
      color: #92400e;
      display: block;
    }

    .connection-status.error {
      background: #f87171;
      color: #991b1b;
      display: block;
    }
  </style>
</head>
<body>
  <div class="connection-status" id="connectionStatus"></div>
  
  <div class="chat-container">
    <div class="header">
      <h1>
        <div class="logo-icon">
          <i class="fas fa-graduation-cap"></i>
        </div>
        EduBot
      </h1>
      <div class="subtitle">Professional AI Academic Tutor</div>
    </div>
    
    <div class="notice">
      <i class="fas fa-university"></i>
      Advanced AI tutor for all academic subjects - Ask questions and get detailed follow-up assistance
    </div>
    
    <div id="chatWindow">
      <div class="welcome-message">
        <div class="icon">🎓</div>
        <h3>Welcome to EduBot!</h3>
        <p>I'm your professional AI academic tutor with advanced capabilities. I provide comprehensive answers and can handle follow-up questions to deepen your understanding. Ask me anything about any academic subject!</p>
      </div>
    </div>

    <div class="input-area">
      <div class="input-row">
        <select id="levelSelect">
          <option value="school">School Student</option>
          <option value="college">College Student</option>
          <option value="research">Research Level</option>
        </select>
        
        <div class="input-container">
          <input id="questionInput" type="text" placeholder="Ask your academic question..." autocomplete="off" />
          <button id="sendBtn" disabled>
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
      
      <div class="features">
        <span class="feature-tag">Mathematics & Statistics</span>
        <span class="feature-tag">Sciences & Engineering</span>
        <span class="feature-tag">Languages & Literature</span>
        <span class="feature-tag">History & Social Studies</span>
        <span class="feature-tag">Computer Science & AI</span>
        <span class="feature-tag">Follow-up Questions</span>
      </div>
    </div>
  </div>

  <script>
    // Production-level JavaScript with enhanced features
    class EduBotChat {
      constructor() {
        this.chatWindow = document.getElementById('chatWindow');
        this.input = document.getElementById('questionInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.levelSelect = document.getElementById('levelSelect');
        this.connectionStatus = document.getElementById('connectionStatus');
        
        this.currentChatId = null;
        this.isTyping = false;
        this.retryAttempts = 0;
        this.maxRetries = 3;
        
        this.init();
      }

      init() {
        this.setupEventListeners();
        this.updateSendButton();
        this.input.focus();
        
        // Cleanup old chats periodically
        setInterval(() => this.cleanupOldMessages(), 300000); // 5 minutes
      }

      setupEventListeners() {
        this.input.addEventListener('input', () => this.updateSendButton());
        this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Handle visibility change to pause/resume
        document.addEventListener('visibilitychange', () => {
          if (!document.hidden) {
            this.updateConnectionStatus();
          }
        });
      }

      updateSendButton() {
        const hasText = this.input.value.trim().length > 0;
        this.sendBtn.disabled = !hasText || this.isTyping;
      }

      handleKeyDown(e) {
        if (e.key === 'Enter' && !this.sendBtn.disabled) {
          e.preventDefault();
          this.sendMessage();
        }
      }

      updateConnectionStatus(status = 'connected', message = '') {
        this.connectionStatus.className = `connection-status ${status}`;
        this.connectionStatus.textContent = message;
        
        if (status === 'connected') {
          setTimeout(() => {
            this.connectionStatus.style.display = 'none';
          }, 2000);
        }
      }

      clearWelcome() {
        const welcome = this.chatWindow.querySelector('.welcome-message');
        if (welcome) {
          welcome.remove();
        }
      }

      addMessage(text, isUser, followUpSuggestions = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = isUser ? 'U' : 'AI';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        if (isUser) {
          content.textContent = text;
        } else {
          this.typeMessage(content, text, () => {
            if (followUpSuggestions.length > 0) {
              this.addFollowUpSuggestions(messageDiv, followUpSuggestions);
            }
          });
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        this.chatWindow.appendChild(messageDiv);
        
        this.scrollToBottom();
      }

      typeMessage(element, text, callback = null) {
        element.innerHTML = '';
        element.classList.add('typing-effect');
        
        const words = text.split(' ');
        let currentWordIndex = 0;
        
        const typeWord = () => {
          if (currentWordIndex < words.length) {
            element.innerHTML += (currentWordIndex > 0 ? ' ' : '') + words[currentWordIndex];
            currentWordIndex++;
            setTimeout(typeWord, 50);
          } else {
            element.classList.remove('typing-effect');
            if (callback) callback();
          }
        };
        
        typeWord();
      }

      addFollowUpSuggestions(messageDiv, suggestions) {
        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'follow-up-suggestions';
        
        suggestions.forEach(suggestion => {
          const btn = document.createElement('button');
          btn.className = 'follow-up-btn';
          btn.textContent = suggestion;
          btn.addEventListener('click', () => {
            this.input.value = suggestion;
            this.updateSendButton();
            this.sendMessage();
          });
          suggestionsDiv.appendChild(btn);
        });
        
        messageDiv.appendChild(suggestionsDiv);
      }

      addTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot typing-message';
        messageDiv.innerHTML = `
          <div class="message-avatar">AI</div>
          <div class="message-content">
            <div class="typing-indicator">
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
            </div>
          </div>
        `;
        this.chatWindow.appendChild(messageDiv);
        this.scrollToBottom();
      }

      removeTypingIndicator() {
        const typingMsg = this.chatWindow.querySelector('.typing-message');
        if (typingMsg) {
          typingMsg.remove();
        }
      }

      scrollToBottom() {
        this.chatWindow.scrollTop = this.chatWindow.scrollHeight;
      }

      cleanupOldMessages() {
        const messages = this.chatWindow.querySelectorAll('.message');
        if (messages.length > 50) {
          // Keep only the latest 40 messages
          for (let i = 0; i < messages.length - 40; i++) {
            messages[i].remove();
          }
        }
      }

      async sendMessage() {
        const question = this.input.value.trim();
        if (!question || this.isTyping) return;

        this.isTyping = true;
        this.clearWelcome();
        this.addMessage(question, true);
        
        this.input.value = '';
        this.updateSendButton();
        
        const level = this.levelSelect.value;
        this.addTypingIndicator();
        this.updateConnectionStatus('connecting', 'Connecting...');

        try {
          const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: question,
              level: level,
              chat_id: this.currentChatId
            })
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const data = await response.json();
          this.removeTypingIndicator();
          
          if (data.error) {
            this.addMessage(`I apologize, but I encountered an error: ${data.error}`, false);
          } else {
            this.currentChatId = data.chat_id;
            const followUpSuggestions = data.follow_up_suggestions || [];
            this.addMessage(data.reply.content, false, followUpSuggestions);
          }
          
          this.updateConnectionStatus('connected');
          this.retryAttempts = 0;
          
        } catch (error) {
          this.removeTypingIndicator();
          
          if (this.retryAttempts < this.maxRetries) {
            this.retryAttempts++;
            this.updateConnectionStatus('connecting', `Retrying... (${this.retryAttempts}/${this.maxRetries})`);
            setTimeout(() => this.sendMessage(), 2000);
            return;
          }
          
          this.addMessage('I apologize, but I\'m having connection issues. Please try again in a moment.', false);
          this.updateConnectionStatus('error', 'Connection failed');
          this.retryAttempts = 0;
        } finally {
          this.isTyping = false;
          this.updateSendButton();
        }
      }
    }

    // Initialize the chat application
    document.addEventListener('DOMContentLoaded', () => {
      new EduBotChat();
    });
  </script>
</body>
</html>
    '''

# Production-level chat endpoint with follow-up question handling
@app.route("/chat", methods=["POST"])
def chat() -> tuple:
    try:
        cleanup_old_chats()  # Clean up old chats periodically
        
        data = request.get_json(silent=True) or {}
        user_message: str | None = data.get("message")
        level: str = data.get("level", "school").lower()
        chat_id: str = data.get("chat_id") or new_id()

        if not user_message:
            return jsonify({"error": "Please provide a message"}), 400

        logger.info(f"Received message from chat {chat_id[:8]}: {user_message[:50]}...")

        # Initialize chat history if new
        if chat_id not in chat_histories:
            chat_histories[chat_id] = {
                'messages': [],
                'created_at': datetime.now(),
                'level': level
            }

        # Handle greetings
        greetings = ['hi', 'hello', 'hey', 'hii', 'greetings', 'good morning', 
                    'good afternoon', 'good evening', 'namaste']
        if user_message.lower().strip() in greetings:
            return jsonify({
                "chat_id": chat_id,
                "reply": {
                    "message_id": new_id(),
                    "content": "Hello! I'm EduBot, your professional AI academic tutor. I can help you with any academic subject and provide detailed explanations with follow-up questions. What would you like to learn about?"
                },
                "follow_up_suggestions": [
                    "What subjects do you specialize in?",
                    "How can you help with my studies?",
                    "Can you explain complex topics?"
                ]
            }), 200

        # Check educational content
        if not is_educational_content(user_message):
            return jsonify({
                "chat_id": chat_id,
                "reply": {
                    "message_id": new_id(),
                    "content": "I'm designed specifically for educational assistance. Please ask me about academic subjects like Mathematics, Science, Literature, History, Computer Science, or any other school or college topic."
                },
                "follow_up_suggestions": [
                    "Help me with Math",
                    "Explain a Science concept",
                    "Literature analysis help"
                ]
            }), 200

        # Add user message to history
        chat_histories[chat_id]['messages'].append({
            "role": "user", 
            "content": user_message, 
            "message_id": new_id(),
            "timestamp": datetime.now()
        })

        # Enhanced system prompts based on level
        if level == "school":
            system_prompt = """You are EduBot, a professional AI academic tutor for school students. Follow these guidelines:

CORE RESPONSIBILITIES:
- Provide accurate, educational responses for school-level topics
- Adapt explanations to appropriate grade level understanding
- Encourage learning and curiosity
- Be supportive and patient

RESPONSE STYLE:
- Clear, structured explanations
- Use examples and analogies when helpful
- Break complex topics into digestible parts
- No emojis in responses
- Professional but friendly tone

ANSWER LENGTH:
- For simple factual questions: 2-3 sentences with clear explanation
- For complex topics: Comprehensive explanation with examples
- Always ensure understanding before moving to advanced concepts

FOLLOW-UP APPROACH:
- Always consider what natural follow-up questions a student might have
- Suggest 2-3 relevant follow-up questions when appropriate
- Help students deepen their understanding progressively

Remember: You're helping students learn effectively and build strong academic foundations."""

        elif level == "college":
            system_prompt = """You are EduBot, a professional AI academic tutor for college students. Follow these guidelines:

CORE RESPONSIBILITIES:
- Provide detailed, academic-level responses
- Include technical terminology when appropriate
- Reference established theories and principles
- Support critical thinking and analysis

RESPONSE STYLE:
- Comprehensive and well-structured
- Include relevant technical details
- Make connections between concepts
- Professional academic tone without emojis
- Encourage deeper investigation

ANSWER LENGTH:
- For factual questions: Precise answer with context and implications
- For complex topics: Thorough analysis with multiple perspectives
- Include relevant examples and applications

FOLLOW-UP APPROACH:
- Suggest advanced follow-up questions
- Encourage analytical thinking
- Connect to broader academic concepts
- Support research and deeper study

Remember: You're supporting advanced learning and academic excellence."""

        else:  # research level
            system_prompt = """You are EduBot, a professional AI academic tutor for research-level inquiries. Follow these guidelines:

CORE RESPONSIBILITIES:
- Provide expert-level responses with academic rigor
- Reference current research and methodologies
- Support advanced analysis and critical evaluation
- Maintain highest standards of accuracy

RESPONSE STYLE:
- Sophisticated and comprehensive
- Include methodological considerations
- Reference relevant literature concepts
- Professional academic discourse
- No emojis - maintain formal academic tone

ANSWER LENGTH:
- Detailed responses appropriate for research context
- Include multiple perspectives and approaches
- Discuss implications and applications
- Address limitations and considerations

FOLLOW-UP APPROACH:
- Suggest research-oriented follow-up questions
- Encourage methodological thinking
- Connect to current academic discussions
- Support independent research development

Remember: You're facilitating advanced academic research and scholarly development."""

        # Build conversation context (keep last 10 exchanges for context)
        recent_messages = chat_histories[chat_id]['messages'][-20:]  # Last 10 exchanges
        messages = [{"role": "system", "content": system_prompt}] + [
            {"role": m["role"], "content": m["content"]} 
            for m in recent_messages
        ]

        # Generate response with appropriate parameters
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.4,  # Balanced creativity and accuracy
                max_tokens=400,   # Comprehensive responses
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            bot_reply = response.choices[0].message.content.strip()

            # Generate follow-up suggestions
            follow_up_suggestions = generate_follow_up_suggestions(user_message, bot_reply, level)

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return jsonify({
                "error": "I'm experiencing technical difficulties. Please try again in a moment."
            }), 502

        # Add assistant response to history
        assistant_msg = {
            "role": "assistant", 
            "content": bot_reply, 
            "message_id": new_id(),
            "timestamp": datetime.now()
        }
        chat_histories[chat_id]['messages'].append(assistant_msg)

        logger.info(f"Generated response for chat {chat_id[:8]}: {len(bot_reply)} characters")

        return jsonify({
            "chat_id": chat_id,
            "reply": {
                "message_id": assistant_msg["message_id"],
                "content": bot_reply,
            },
            "follow_up_suggestions": follow_up_suggestions
        }), 200

    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

def generate_follow_up_suggestions(user_question: str, bot_response: str, level: str) -> List[str]:
    """Generate contextual follow-up questions based on the conversation"""
    
    # Define follow-up patterns based on question types
    question_lower = user_question.lower()
    
    # Science topics
    if any(word in question_lower for word in ['physics', 'chemistry', 'biology', 'science']):
        if level == "school":
            return [
                "Can you give me a real-world example?",
                "How is this used in daily life?",
                "What are the key points to remember?"
            ]
        else:
            return [
                "What are the underlying mechanisms?",
                "How does this relate to other concepts?",
                "What are current research developments?"
            ]
    
    # Mathematics
    elif any(word in question_lower for word in ['math', 'algebra', 'geometry', 'calculus']):
        if level == "school":
            return [
                "Can you show me a step-by-step example?",
                "What are common mistakes to avoid?",
                "How do I practice this concept?"
            ]
        else:
            return [
                "What are the practical applications?",
                "How does this connect to advanced topics?",
                "What are the theoretical implications?"
            ]
    
    # History topics
    elif any(word in question_lower for word in ['history', 'historical', 'war', 'ancient']):
        return [
            "What were the causes and effects?",
            "How did this impact society?",
            "What lessons can we learn from this?"
        ]
    
    # Computer Science / Technology
    elif any(word in question_lower for word in ['computer', 'programming', 'algorithm', 'ai', 'technology']):
        if level == "school":
            return [
                "How do I get started with this?",
                "What tools do I need?",
                "Can you show me a simple example?"
            ]
        else:
            return [
                "What are the implementation challenges?",
                "How does this scale in practice?",
                "What are alternative approaches?"
            ]
    
    # Literature
    elif any(word in question_lower for word in ['literature', 'poem', 'novel', 'author', 'writing']):
        return [
            "What are the main themes?",
            "How does this reflect the time period?",
            "What techniques does the author use?"
        ]
    
    # General follow-ups based on question type
    elif question_lower.startswith(('what is', 'what are')):
        return [
            "How does this work in practice?",
            "Why is this important?",
            "Can you give me more examples?"
        ]
    elif question_lower.startswith(('how to', 'how do')):
        return [
            "What if I encounter problems?",
            "Are there alternative methods?",
            "What are the next steps?"
        ]
    elif question_lower.startswith(('why is', 'why does')):
        return [
            "What are the implications?",
            "How does this affect other areas?",
            "What would happen if this changed?"
        ]
    
    # Default follow-ups
    return [
        "Can you explain this further?",
        "How does this apply to my studies?",
        "What should I learn next?"
    ]

# Health check endpoint
@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "EduBot - Professional AI Academic Tutor",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "active_chats": len(chat_histories)
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# Get port from environment variable
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    logger.info(f"Starting EduBot server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
