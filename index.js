const chatWindow = document.getElementById('chatWindow');
const input = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const levelSelect = document.getElementById('levelSelect');

// Store chat_id for conversation continuity
let currentChatId = null;

input.addEventListener('input', () => sendBtn.disabled = !input.value.trim());

// ✅ Function to remove any remaining markdown formatting
function stripMarkdown(text) {
  return text
    // Remove bold formatting **text** and __text__
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/__(.+?)__/g, '$1')
    // Remove italic formatting *text* and _text_
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    // Remove strikethrough ~~text~~
    .replace(/~~(.+?)~~/g, '$1')
    // Remove inline code `text`
    .replace(/`(.+?)`/g, '$1')
    // Remove headers ### text
    .replace(/^#{1,6}\s+(.+)$/gm, '$1')
    // Remove links [text](url) - keep just the text
    .replace(/\[(.+?)\]\(.+?\)/g, '$1')
    // Clean up any remaining asterisks or underscores
    .replace(/[\*_]/g, '');
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
    const res = await fetch('http://localhost:5000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        message: question,        // ✅ Changed from 'question' to 'message'
        level: level,
        chat_id: currentChatId    // ✅ Added chat_id for conversation history
      })
    });
    
    const data = await res.json();
    removeTypingMessage();
    
    // ✅ Handle both success and error responses
    if (data.error) {
      addMessage(`Error: ${data.error}`, false);
    } else {
      // ✅ Update chat_id for future messages
      currentChatId = data.chat_id;
      // ✅ Changed from 'data.answer' to 'data.reply.content'
      addMessage(data.reply.content || "Sorry, I didn't get that.", false);
    }
  } catch (error) {
    removeTypingMessage();
    addMessage('Error reaching server.', false);
  }
}

// ✅ Updated addMessage function with formatting and markdown removal
function addMessage(text, isUser) {
  const msg = document.createElement('div');
  msg.style.padding = '8px';
  msg.style.margin = '4px';
  msg.style.backgroundColor = isUser ? '#0078d7' : '#e0e0e0';
  msg.style.color = isUser ? 'white' : 'black';
  msg.style.borderRadius = '10px';
  msg.style.maxWidth = '80%';
  
  // ✅ Handle line breaks and strip markdown formatting from AI responses
  if (!isUser) {
    // Strip any remaining markdown formatting and convert newlines to HTML breaks
    const cleanText = stripMarkdown(text);
    msg.innerHTML = cleanText.replace(/\n/g, '<br>');
    msg.style.whiteSpace = 'normal';
    msg.style.lineHeight = '1.4';
  } else {
    // For user messages, keep as plain text
    msg.textContent = text;
  }

  // Align user messages to the right, bot messages to the left
  msg.style.alignSelf = isUser ? 'flex-end' : 'flex-start';

  chatWindow.appendChild(msg);

  // ✅ Only auto-scroll if user is near bottom already
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
