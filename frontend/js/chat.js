/**
 * LearnMate AI — AI Chat Module
 */
const Chat = {
    useDocuments: false,

    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        if (!message) return;

        const messagesContainer = document.getElementById('chatMessages');
        const useDocs = this.useDocuments;

        // Add user message
        messagesContainer.innerHTML +=
            '<div class="chat-message user">' +
                '<div class="message-avatar">You</div>' +
                '<div class="message-content">' + escapeHtml(message) + '</div>' +
            '</div>';

        input.value = '';
        input.style.height = 'auto';

        // Typing indicator
        const typingId = 'typing-' + Date.now();
        messagesContainer.innerHTML +=
            '<div class="chat-message assistant" id="' + typingId + '">' +
                '<div class="message-avatar">AI</div>' +
                '<div class="message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>' +
            '</div>';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const result = await Api.chatAsk(message, App.chatSessionId, useDocs);
            const typingEl = document.getElementById(typingId);

            if (typingEl) {
                let responseHtml = formatMessage(result.response);
                if (result.sources && result.sources.length > 0) {
                    responseHtml += '<div class="message-sources">Sources: ' +
                        result.sources.map(function(s) { return '<span>' + escapeHtml(s.source) + '</span>'; }).join('') +
                        '</div>';
                }
                typingEl.querySelector('.message-content').innerHTML = responseHtml;
            }

            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } catch (error) {
            const typingEl = document.getElementById(typingId);
            if (typingEl) {
                typingEl.querySelector('.message-content').innerHTML =
                    '<p style="color:var(--danger);">Sorry, something went wrong: ' + escapeHtml(error.message) + '</p>';
            }
            showToast('Failed to send message. Check your API key.', 'error');
        }
    },

    async loadHistory() {
        try {
            const result = await Api.chatHistory(App.chatSessionId);
            const messagesContainer = document.getElementById('chatMessages');

            if (result.messages && result.messages.length > 1) {
                messagesContainer.innerHTML = '';
                result.messages.forEach(function(msg) {
                    if (msg.role === 'user') {
                        messagesContainer.innerHTML +=
                            '<div class="chat-message user">' +
                                '<div class="message-avatar">You</div>' +
                                '<div class="message-content">' + escapeHtml(msg.content) + '</div>' +
                            '</div>';
                    } else {
                        let responseHtml = formatMessage(msg.content);
                        if (msg.sources && msg.sources.length > 0) {
                            responseHtml += '<div class="message-sources">Sources: ' +
                                msg.sources.map(function(s) { return '<span>' + escapeHtml(s.source) + '</span>'; }).join('') +
                                '</div>';
                        }
                        messagesContainer.innerHTML +=
                            '<div class="chat-message assistant">' +
                                '<div class="message-avatar">AI</div>' +
                                '<div class="message-content">' + responseHtml + '</div>' +
                            '</div>';
                    }
                });
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        } catch (error) {
            // First visit, show welcome message
        }
    },

    toggleMode() {
        this.useDocuments = !this.useDocuments;
        const btn = document.getElementById('chatModeBtn');
        if (btn) {
            btn.textContent = this.useDocuments ? 'Mode: Documents' : 'Mode: General';
            btn.classList.toggle('active', this.useDocuments);
        }
    },

    async clearHistory() {
        try {
            await Api.chatClear(App.chatSessionId);
            document.getElementById('chatMessages').innerHTML =
                '<div class="chat-message assistant">' +
                    '<div class="message-avatar">AI</div>' +
                    '<div class="message-content"><p>Chat cleared! How can I help you?</p></div>' +
                '</div>';
            showToast('Chat history cleared', 'info');
        } catch (error) {
            showToast('Failed to clear chat', 'error');
        }
    }
};

// Format AI response with basic markdown
function formatMessage(text) {
    if (!text) return '';

    var html = escapeHtml(text);

    // Headers
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Bullet points
    html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.+<\/li>\n?)+/g, function(match) { return '<ul>' + match + '</ul>'; });

    // Numbered lists
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    // Wrap in paragraph
    if (!html.startsWith('<')) {
        html = '<p>' + html + '</p>';
    }

    return html;
}

function sendMessage() {
    Chat.sendMessage();
}
