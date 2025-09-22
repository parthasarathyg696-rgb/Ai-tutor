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
    """Check if the message is educational/academic content for school or college"""
    
    # Strictly non-educational content that should be blocked
    blocked_keywords = [
        'porn', 'sex', 'nude', 'explicit', 'adult content', 
        'violence', 'kill', 'murder', 'weapon', 'bomb', 'terrorist',
        'drug dealer', 'illegal drugs', 'cocaine', 'heroin',
        'hack bank', 'steal money', 'credit card fraud',
        'suicide', 'self harm', 'racist', 'hate speech'
    ]
    
    # Educational topics for ALL school standards and college branches
    educational_topics = [
        # Core School Subjects (All Standards 1-12)
        'mathematics', 'math', 'algebra', 'geometry', 'calculus', 'trigonometry', 'statistics',
        'physics', 'chemistry', 'biology', 'science', 'botany', 'zoology',
        'history', 'geography', 'civics', 'political science', 'social studies',
        'english', 'literature', 'grammar', 'writing', 'reading', 'poetry',
        'hindi', 'sanskrit', 'language', 'linguistics',
        'economics', 'commerce', 'accounting', 'business studies',
        'philosophy', 'psychology', 'sociology', 'anthropology',
        'art', 'music', 'dance', 'drama', 'theater', 'fine arts',
        'physical education', 'sports', 'health', 'nutrition',
        
        # College Degree Branches - Engineering
        'engineering', 'mechanical engineering', 'civil engineering', 'electrical engineering',
        'computer science', 'information technology', 'software engineering',
        'electronics', 'chemical engineering', 'aerospace engineering',
        'automobile engineering', 'biotechnology engineering',
        
        # College Degree Branches - Medical
        'medicine', 'mbbs', 'anatomy', 'physiology', 'pharmacology',
        'pathology', 'microbiology', 'biochemistry', 'surgery',
        'dentistry', 'nursing', 'pharmacy', 'physiotherapy',
        'veterinary', 'medical science', 'neurology', 'cardiology',
        
        # College Degree Branches - Science
        'bsc', 'msc', 'mathematics', 'physics', 'chemistry', 'biology',
        'environmental science', 'geology', 'astronomy', 'astrophysics',
        'marine biology', 'genetics', 'molecular biology',
        
        # College Degree Branches - Arts & Humanities
        'ba', 'ma', 'english literature', 'history', 'political science',
        'philosophy', 'psychology', 'sociology', 'anthropology',
        'journalism', 'mass communication', 'linguistics',
        'archaeology', 'museum studies', 'library science',
        
        # College Degree Branches - Commerce & Management
        'bcom', 'mcom', 'bba', 'mba', 'accounting', 'finance',
        'marketing', 'human resources', 'operations management',
        'business administration', 'chartered accountancy',
        'cost accounting', 'taxation', 'banking', 'insurance',
        
        # College Degree Branches - Law
        'law', 'llb', 'llm', 'constitutional law', 'criminal law',
        'civil law', 'corporate law', 'international law',
        'human rights', 'intellectual property',
        
        # College Degree Branches - Education
        'bed', 'med', 'education', 'pedagogy', 'child psychology',
        'educational psychology', 'curriculum development',
        
        # College Degree Branches - Technology & Computer Science
        'computer science', 'information technology', 'software engineering',
        'artificial intelligence', 'ai', 'machine learning', 'data science',
        'cybersecurity', 'network security', 'database management',
        'web development', 'mobile app development', 'programming',
        'python', 'java', 'c++', 'javascript', 'html', 'css',
        'algorithms', 'data structures', 'operating systems',
        'computer networks', 'cloud computing', 'blockchain',
        
        # College Degree Branches - Architecture & Design
        'architecture', 'interior design', 'graphic design',
        'fashion design', 'product design', 'urban planning',
        
        # College Degree Branches - Agriculture
        'agriculture', 'agricultural engineering', 'horticulture',
        'forestry', 'animal husbandry', 'dairy science',
        'food technology', 'agricultural economics',
        
        # College Degree Branches - Others
        'hotel management', 'tourism', 'aviation', 'maritime studies',
        'film studies', 'animation', 'photography',
        'social work', 'public administration',
        
        # General Academic Terms
        'study', 'learn', 'education', 'academic', 'school', 'college',
        'university', 'degree', 'diploma', 'course', 'subject',
        'exam', 'test', 'assignment', 'homework', 'project',
        'research', 'thesis', 'dissertation', 'analysis',
        'theory', 'concept', 'principle', 'formula', 'equation',
        'definition', 'explanation', 'example', 'solution',
        'problem solving', 'critical thinking', 'reasoning'
    ]
    
    # Simple greetings and conversational starters
    greetings = ['hi', 'hello', 'hey', 'hii', 'hello there', 'good morning', 
                'good afternoon', 'good evening', 'namaste', 'greetings']
    
    message_lower = message.lower().strip()
    
    # Block only strictly inappropriate content
    for blocked in blocked_keywords:
        if blocked in message_lower:
            return False
    
    # Allow greetings
    if any(greeting in message_lower for greeting in greetings):
        return True
    
    # Allow educational content
    for topic in educational_topics:
        if topic in message_lower:
            return True
    
    # For ambiguous content, check if it seems academic
    academic_indicators = ['what is', 'explain', 'how to', 'define', 'solve', 'calculate', 
                          'difference between', 'types of', 'examples of', 'formula for',
                          'meaning of', 'understand', 'learn about', 'tell me about']
    
    if any(indicator in message_lower for indicator in academic_indicators):
        return True
    
    # Be permissive for short questions that might be educational
    if len(message.split()) <= 5:
        return True
    
    # Default to allowing content (educational focus)
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
  <title>EduBot - Academic Tutor for Schools & Colleges</title>
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
      max-width: 500px;
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
        <div class="subtitle">Academic Tutor for All School & College Students</div>
      </div>
    </div>
    
    <div class="notice">
      <i class="fas fa-university"></i>
      Supporting All School Standards (1-12) & College Degrees (Engineering, Medical, Arts, Commerce, Law, etc.)
    </div>
    
    <div id="chatWindow">
      <div class="welcome-message">
        <div class="icon">🎓</div>
        <h3>Welcome to EduBot - Your Academic Companion!</h3>
        <p>I'm designed to help students from all school standards (Class 1-12) and college degree programs. Whether you're studying Mathematics, Science, Engineering, Medicine, Arts, Commerce, Law, or any other academic field - I'm here to provide clear explanations and help you understand concepts better.</p>
        <br>
        <p><strong>Ask me about:</strong> Your homework, assignments, exam preparation, concept explanations, problem solving, or any academic topic from your curriculum!</p>
      </div>
    </div>

    <div class="input-area">
      <div class="input-row">
        <div class="level-selector">
          <select id="levelSelect">
            <option value="school">🏫 School Student</option>
            <option value="college">🎓 College Student</option>
          </select>
        </div>
        
        <div class="input-container">
          <input id="questionInput" type="text" placeholder="Ask about any subject from your curriculum..." autocomplete="off" />
          <button id="sendBtn" disabled>
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
      
      <div class="features">
        <span class="feature-tag">All School Subjects</span>
        <span class="feature-tag">Engineering</span>
        <span class="feature-tag">Medical</span>
        <span class="feature-tag">Arts & Humanities</span>
        <span class="feature-tag">Commerce</span>
        <span class="feature-tag">Law</span>
        <span class="feature-tag">Computer Science</span>
        <span class="feature-tag">Research Help</span>
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

# Chat endpoint with proper educational content handling
@app.route("/chat", methods=["POST"])
def chat() -> tuple:
    data = request.get_json(silent=True) or {}
    user_message: str | None = data.get("message")
    level: str = data.get("level", "school").lower()
    chat_id: str = data.get("chat_id") or new_id()

    if not user_message:
        return jsonify({"error": "Please provide a message"}), 400

    # Handle simple greetings
    greetings = ['hi', 'hello', 'hey', 'hii', 'greetings', 'good morning', 'good afternoon', 'good evening', 'namaste']
    if user_message.lower().strip() in greetings:
        return jsonify({
            "chat_id": chat_id,
            "reply": {
                "message_id": new_id(),
                "content": "Hello! I'm EduBot, your academic tutor for all school and college subjects. I can help you with questions from any standard (Class 1-12) or college degree program including Engineering, Medical, Arts, Commerce, Law, Computer Science, and more. What would you like to learn about today?"
            }
        }), 200

    # Check if the message is educational content
    if not is_educational_content(user_message):
        return jsonify({
            "chat_id": chat_id,
            "reply": {
                "message_id": new_id(),
                "content": "I'm designed to help with academic and educational topics for school and college students. Please ask me questions related to your curriculum, homework, assignments, or any subject you're studying. I'm here to help you learn!"
            }
        }), 200

    chat_histories.setdefault(chat_id, []).append(
        {"role": "user", "content": user_message, "message_id": new_id()}
    )

    # Enhanced system prompts for school and college students
    if level == "school":
        system_prompt = """You are EduBot, an AI academic tutor designed to help school students from Class 1 to Class 12. You MUST follow these rules:

ACADEMIC FOCUS:
- Help with ALL school subjects: Mathematics, Science (Physics, Chemistry, Biology), Social Studies (History, Geography, Civics), Languages (English, Hindi, Regional), Computer Science, Arts, Physical Education
- Support ALL educational boards: CBSE, ICSE, State Boards, International Boards
- Assist with homework, assignments, exam preparation, concept understanding
- Provide age-appropriate explanations based on the student's class level

TEACHING APPROACH:
- Use simple, clear language appropriate for school students
- Provide step-by-step explanations
- Use examples and analogies that students can relate to
- Encourage learning and curiosity
- Break down complex topics into smaller parts
- Offer practice problems when relevant

RESPONSE FORMAT:
- Start with the topic name
- Give a clear, simple explanation
- Provide examples if helpful
- Add step-by-step solutions for problems
- End with encouragement to ask more questions

Remember: You are helping school students learn and understand their curriculum better."""

    else:  # college level
        system_prompt = """You are EduBot, an AI academic tutor designed to help college students across all degree programs. You MUST follow these rules:

ACADEMIC FOCUS:
- Support ALL college degrees: Engineering (all branches), Medical (MBBS, BDS, Pharmacy, Nursing), Arts & Humanities, Commerce & Management, Law, Computer Science, Architecture, Agriculture, and more
- Assist with coursework, assignments, projects, research, exam preparation
- Help with both undergraduate and postgraduate studies
- Provide detailed explanations of complex academic concepts

TEACHING APPROACH:
- Use appropriate technical terminology and detailed explanations
- Provide comprehensive analysis of topics
- Include theoretical background and practical applications
- Reference academic principles and established theories
- Encourage critical thinking and deeper understanding
- Connect concepts across different subjects when relevant

RESPONSE FORMAT:
- Start with comprehensive topic overview
- Provide detailed theoretical explanation
- Include practical applications and examples
- Add relevant formulas, equations, or technical details
- Suggest further reading or research directions when appropriate

Remember: You are helping college students master advanced academic concepts in their chosen fields of study."""

    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in chat_histories[chat_id]
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,  # Lower temperature for accurate educational content
            max_tokens=700,   # Increased for detailed explanations
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        bot_reply = response.choices[0].message.content.strip()

    except OpenAIError as e:
        return jsonify({"error": f"Unable to process your academic query at this time. Please try again."}), 502

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
    return jsonify({"status": "healthy", "service": "EduBot - Academic Tutor"}), 200

# Get port from environment variable
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)
