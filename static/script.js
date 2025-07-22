document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const permissionModal = document.getElementById('permission-modal');
    const allowWebSearchBtn = document.getElementById('allow-web-search');
    const denyWebSearchBtn = document.getElementById('deny-web-search');
    let pendingWebQuestion = null;
    let lastBotMessage = null;
    let lastUserQuestion = null;

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    function addMessage(content, isUser, source) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        let html;
        if (!isUser) {
            html = window.marked ? window.marked.parse(content) : content.replace(/\n/g, '<br>');
        } else {
            html = content.replace(/\n/g, '<br>');
        }
        if (!isUser && source) {
            html += ` <span class="source-label">[${source}]</span>`;
        }
        messageDiv.innerHTML = html;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }

    function addFeedbackButtons(messageDiv, question, answer) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-buttons';
        const upBtn = document.createElement('button');
        upBtn.className = 'feedback-btn up';
        upBtn.innerHTML = '👍';
        const downBtn = document.createElement('button');
        downBtn.className = 'feedback-btn down';
        downBtn.innerHTML = '👎';
        feedbackDiv.appendChild(upBtn);
        feedbackDiv.appendChild(downBtn);
        messageDiv.appendChild(feedbackDiv);
        upBtn.addEventListener('click', function() {
            sendFeedback(question, answer, 'up');
            upBtn.classList.add('selected');
            downBtn.classList.remove('selected');
        });
        downBtn.addEventListener('click', function() {
            sendFeedback(question, answer, 'down');
            downBtn.classList.add('selected');
            upBtn.classList.remove('selected');
        });
    }

    function sendFeedback(question, answer, feedback) {
        fetch('/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `question=${encodeURIComponent(question)}&answer=${encodeURIComponent(answer)}&feedback=${feedback}`
        });
    }

    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const question = userInput.value.trim();
        if (!question) return;
        addMessage(question, true);
        lastUserQuestion = question;
        userInput.value = '';
        showTypingIndicator();
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `question=${encodeURIComponent(question)}`
            });
            hideTypingIndicator();
            if (response.ok) {
                const data = await response.json();
                if (data.permission_required) {
                    pendingWebQuestion = data.question;
                    document.getElementById('permission-message').textContent = data.message;
                    permissionModal.style.display = 'flex';
                } else {
                    lastBotMessage = addMessage(data.response, false, detectSource(data.response));
                    addFeedbackButtons(lastBotMessage, lastUserQuestion, data.response);
                }
            } else {
                throw new Error('Server error');
            }
        } catch (error) {
            hideTypingIndicator();
            addMessage("Sorry, I encountered an error. Please try again.", false);
            console.error('Error:', error);
        }
    });

    allowWebSearchBtn.addEventListener('click', async function() {
        permissionModal.style.display = 'none';
        if (!pendingWebQuestion) return;
        showTypingIndicator();
        try {
            const response = await fetch('/web_search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `question=${encodeURIComponent(pendingWebQuestion)}`
            });
            hideTypingIndicator();
            if (response.ok) {
                const data = await response.json();
                lastBotMessage = addMessage(data.response, false, 'Web');
                addFeedbackButtons(lastBotMessage, pendingWebQuestion, data.response);
            } else {
                throw new Error('Web search error');
            }
        } catch (error) {
            hideTypingIndicator();
            addMessage("Sorry, I couldn't find an answer online.", false);
        }
        pendingWebQuestion = null;
    });
    denyWebSearchBtn.addEventListener('click', function() {
        permissionModal.style.display = 'none';
        addMessage("No problem! Please try rephrasing your question or ask another math question.", false);
        pendingWebQuestion = null;
    });

    const aboutIcon = document.getElementById('about-icon');
    const contactIcon = document.getElementById('contact-icon');
    const aboutModal = document.getElementById('about-modal');
    const contactModal = document.getElementById('contact-modal');

    if (aboutIcon && aboutModal) {
        aboutIcon.addEventListener('click', function() {
            aboutModal.style.display = 'flex';
        });
    }
    if (contactIcon && contactModal) {
        contactIcon.addEventListener('click', function() {
            contactModal.style.display = 'flex';
        });
    }
    window.addEventListener('click', function(event) {
        if (event.target === aboutModal) {
            aboutModal.style.display = 'none';
        }
        if (event.target === contactModal) {
            contactModal.style.display = 'none';
        }
    });

    userInput.focus();

    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    function detectSource(response) {
        if (response.includes('Direct LLM')) return 'LLM';
        if (response.includes('Knowledge Base')) return 'RAG';
        if (response.includes('Internet Source')) return 'WEB';
        return '';
    }
});