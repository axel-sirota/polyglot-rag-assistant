/**
 * Conversation Manager for proper message ordering
 * Ensures user messages always appear before assistant responses
 */

class ConversationManager {
    constructor() {
        this.items = new Map();
        this.displayOrder = [];
        this.pendingUpdates = new Map();
        this.messageQueue = [];
        this.isProcessingQueue = false;
        
        // UI element reference
        this.messagesContainer = null;
        
        // Timing control
        this.messageDelayMs = 100;
        this.lastMessageTime = 0;
    }
    
    initialize(messagesContainer) {
        this.messagesContainer = messagesContainer;
    }
    
    async handleConversationUpdate(event) {
        const { item, delta } = event;
        
        // Queue the update
        this.messageQueue.push({ 
            type: 'update', 
            item, 
            delta, 
            timestamp: Date.now() 
        });
        
        // Process queue if not already processing
        if (!this.isProcessingQueue) {
            await this.processMessageQueue();
        }
    }
    
    async processMessageQueue() {
        this.isProcessingQueue = true;
        
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            
            // Add small delay between messages for natural flow
            const timeSinceLastMessage = Date.now() - this.lastMessageTime;
            if (timeSinceLastMessage < this.messageDelayMs) {
                await this.sleep(this.messageDelayMs - timeSinceLastMessage);
            }
            
            switch (message.type) {
                case 'update':
                    await this.processUpdate(message);
                    break;
                case 'user_message':
                    await this.processUserMessage(message);
                    break;
                case 'assistant_message':
                    await this.processAssistantMessage(message);
                    break;
            }
            
            this.lastMessageTime = Date.now();
        }
        
        this.isProcessingQueue = false;
    }
    
    async processUpdate(message) {
        const { item, delta } = message;
        
        // Initialize item if new
        if (!this.items.has(item.id)) {
            this.items.set(item.id, {
                id: item.id,
                type: item.type,
                role: item.role,
                content: [],
                status: 'in_progress',
                timestamp: Date.now(),
                displayTimestamp: null,
                element: null
            });
            
            // Don't add to display order yet - wait for content
            this.pendingUpdates.set(item.id, item);
        }
        
        // Update content
        const existingItem = this.items.get(item.id);
        
        if (delta) {
            if (delta.text) {
                existingItem.content.push({ type: 'text', text: delta.text });
            }
            if (delta.audio) {
                existingItem.content.push({ type: 'audio', audio: delta.audio });
            }
        }
        
        // Check if item should be displayed
        if (existingItem.content.length > 0 && this.pendingUpdates.has(item.id)) {
            await this.addToDisplayOrder(item.id, existingItem.role);
            this.pendingUpdates.delete(item.id);
        } else if (existingItem.element) {
            // Update existing element
            this.updateItemDisplay(existingItem);
        }
    }
    
    async addToDisplayOrder(itemId, role) {
        const item = this.items.get(itemId);
        item.displayTimestamp = Date.now();
        
        if (role === 'user') {
            // User messages always go at the end
            this.displayOrder.push(itemId);
            this.createMessageElement(item);
        } else if (role === 'assistant') {
            // Find the correct position for assistant message
            let insertIndex = this.displayOrder.length;
            
            // Look for the most recent user message
            for (let i = this.displayOrder.length - 1; i >= 0; i--) {
                const displayItem = this.items.get(this.displayOrder[i]);
                if (displayItem && displayItem.role === 'user') {
                    // Insert after this user message
                    insertIndex = i + 1;
                    break;
                }
            }
            
            // Check if there's a pending user message that should come first
            const pendingUserMessages = Array.from(this.pendingUpdates.values())
                .filter(pending => pending.role === 'user')
                .sort((a, b) => a.timestamp - b.timestamp);
            
            if (pendingUserMessages.length > 0) {
                // Wait for user message to complete
                await this.sleep(150);
                // Re-check after wait
                this.messageQueue.unshift({ 
                    type: 'update', 
                    item, 
                    delta: null, 
                    timestamp: Date.now() 
                });
                return;
            }
            
            this.displayOrder.splice(insertIndex, 0, itemId);
            this.createMessageElement(item, insertIndex);
        }
    }
    
    createMessageElement(item, insertAtIndex = null) {
        if (!this.messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${item.role}-message`;
        messageDiv.id = `message-${item.id}`;
        
        const label = document.createElement('div');
        label.className = 'message-label';
        label.textContent = item.role === 'user' ? 'You:' : 'Assistant:';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = this.formatContent(item.content);
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTimestamp(item.displayTimestamp);
        
        messageDiv.appendChild(label);
        messageDiv.appendChild(textDiv);
        messageDiv.appendChild(timeDiv);
        
        // Store reference to element
        item.element = messageDiv;
        
        // Insert at correct position
        if (insertAtIndex !== null && insertAtIndex < this.messagesContainer.children.length) {
            const referenceNode = this.messagesContainer.children[insertAtIndex];
            this.messagesContainer.insertBefore(messageDiv, referenceNode);
        } else {
            this.messagesContainer.appendChild(messageDiv);
        }
        
        // Animate in
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(10px)';
        
        requestAnimationFrame(() => {
            messageDiv.style.transition = 'opacity 0.3s, transform 0.3s';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        });
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    updateItemDisplay(item) {
        if (!item.element) return;
        
        const textDiv = item.element.querySelector('.message-text');
        if (textDiv) {
            textDiv.textContent = this.formatContent(item.content);
        }
    }
    
    formatContent(contentArray) {
        return contentArray
            .filter(content => content.type === 'text')
            .map(content => content.text)
            .join('');
    }
    
    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        return new Intl.DateTimeFormat('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        }).format(new Date(timestamp));
    }
    
    scrollToBottom() {
        if (this.messagesContainer) {
            const chatContainer = this.messagesContainer.closest('.chat-container');
            if (chatContainer) {
                requestAnimationFrame(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
            }
        }
    }
    
    // Mark item as completed
    completeItem(itemId) {
        const item = this.items.get(itemId);
        if (item) {
            item.status = 'completed';
            if (item.element) {
                item.element.classList.add('completed');
            }
        }
    }
    
    // Add a complete user message
    addUserMessage(text, id = null) {
        const itemId = id || `user-${Date.now()}`;
        
        this.items.set(itemId, {
            id: itemId,
            type: 'message',
            role: 'user',
            content: [{ type: 'text', text }],
            status: 'completed',
            timestamp: Date.now(),
            displayTimestamp: Date.now(),
            element: null
        });
        
        this.displayOrder.push(itemId);
        this.createMessageElement(this.items.get(itemId));
    }
    
    // Add a complete assistant message
    addAssistantMessage(text, id = null) {
        const itemId = id || `assistant-${Date.now()}`;
        
        this.messageQueue.push({
            type: 'assistant_message',
            text,
            id: itemId,
            timestamp: Date.now()
        });
        
        if (!this.isProcessingQueue) {
            this.processMessageQueue();
        }
    }
    
    async processAssistantMessage(message) {
        const { text, id } = message;
        const itemId = id || `assistant-${Date.now()}`;
        
        this.items.set(itemId, {
            id: itemId,
            type: 'message',
            role: 'assistant',
            content: [{ type: 'text', text }],
            status: 'completed',
            timestamp: Date.now(),
            displayTimestamp: Date.now(),
            element: null
        });
        
        await this.addToDisplayOrder(itemId, 'assistant');
    }
    
    // Clear all messages
    clear() {
        this.items.clear();
        this.displayOrder = [];
        this.pendingUpdates.clear();
        this.messageQueue = [];
        
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = '';
        }
    }
    
    // Utility sleep function
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for use in main app
window.ConversationManager = ConversationManager;