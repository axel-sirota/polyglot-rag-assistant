/**
 * Enhanced Interruption Manager for OpenAI Realtime API
 * Handles voice interruptions with proper debouncing and state management
 */

class InterruptionManager {
    constructor(websocket) {
        this.ws = websocket;
        this.lastAudioMessageItemId = "";
        this.audioSampleCounter = 0;
        this.audioSampleCounterPlayed = 0;
        this.isProcessing = false;
        this.audioQueue = [];
        this.currentAudioSource = null;
        this.interruptionThreshold = 100; // ms
        this.lastInterruptionTime = 0;
        this.currentResponseId = null;
        this.interruptedResponses = new Set();
        
        // Audio context for playback management
        this.audioContext = null;
        this.gainNode = null;
        
        // State tracking
        this.isAssistantSpeaking = false;
        this.isUserSpeaking = false;
        this.lastUserSpeechEndTime = 0;
        
        // Debounce timers
        this.userSpeechDebounceTimer = null;
        this.assistantStopDebounceTimer = null;
    }
    
    async initialize(audioContext, gainNode) {
        this.audioContext = audioContext;
        this.gainNode = gainNode;
    }
    
    async handleSpeechStarted(event) {
        const now = Date.now();
        
        // Clear any pending debounce timers
        if (this.userSpeechDebounceTimer) {
            clearTimeout(this.userSpeechDebounceTimer);
            this.userSpeechDebounceTimer = null;
        }
        
        // Debounce rapid interruptions
        if (now - this.lastInterruptionTime < this.interruptionThreshold) {
            console.log('Ignoring rapid interruption');
            return;
        }
        
        this.lastInterruptionTime = now;
        this.isUserSpeaking = true;
        
        // Only interrupt if assistant is actually speaking
        if (this.isAssistantSpeaking && this.isProcessing) {
            console.log('User interruption detected, stopping assistant speech');
            
            // Step 1: Send response.cancel to stop server-side generation
            await this.sendCancelResponse();
            
            // Step 2: Clear all pending audio in the queue
            this.clearAudioQueue();
            
            // Step 3: Stop currently playing audio
            this.stopCurrentAudio();
            
            // Step 4: Truncate the conversation item at the exact interruption point
            if (this.lastAudioMessageItemId) {
                await this.truncateConversationItem();
            }
            
            // Step 5: Reset processing state
            this.isProcessing = false;
            this.isAssistantSpeaking = false;
            this.audioSampleCounter = 0;
            this.audioSampleCounterPlayed = 0;
            
            // Step 6: Notify UI of interruption
            this.notifyUI('interrupted');
            
            // Step 7: Mark response as interrupted
            if (this.currentResponseId) {
                this.interruptedResponses.add(this.currentResponseId);
            }
        }
        
        // Duck audio when user speaks
        if (this.gainNode) {
            this.gainNode.gain.setTargetAtTime(0.2, this.audioContext.currentTime, 0.1);
        }
    }
    
    handleSpeechEnded() {
        this.isUserSpeaking = false;
        this.lastUserSpeechEndTime = Date.now();
        
        // Restore audio level after a short delay
        if (this.userSpeechDebounceTimer) {
            clearTimeout(this.userSpeechDebounceTimer);
        }
        
        this.userSpeechDebounceTimer = setTimeout(() => {
            if (!this.isUserSpeaking && this.gainNode) {
                this.gainNode.gain.setTargetAtTime(1.0, this.audioContext.currentTime, 0.1);
            }
        }, 300);
    }
    
    async sendCancelResponse() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            await this.ws.send(JSON.stringify({
                type: "response.cancel"
            }));
            console.log('Sent response.cancel to server');
        }
    }
    
    async truncateConversationItem() {
        const truncateMs = this.samplesToMs(this.audioSampleCounterPlayed);
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            await this.ws.send(JSON.stringify({
                type: "conversation.item.truncate",
                item_id: this.lastAudioMessageItemId,
                content_index: 0,
                audio_end_ms: truncateMs
            }));
            console.log(`Truncated conversation item ${this.lastAudioMessageItemId} at ${truncateMs}ms`);
        }
    }
    
    clearAudioQueue() {
        // Clear Web Audio API queue
        if (window.audioOutputQueue) {
            while (!window.audioOutputQueue.empty()) {
                window.audioOutputQueue.get();
            }
        }
        
        // Clear internal queue
        this.audioQueue = [];
        console.log('Cleared audio queue');
    }
    
    stopCurrentAudio() {
        if (this.currentAudioSource) {
            try {
                this.currentAudioSource.stop();
                this.currentAudioSource = null;
                console.log('Stopped current audio playback');
            } catch (e) {
                // Already stopped
            }
        }
    }
    
    samplesToMs(samples) {
        // For 24kHz audio (OpenAI default)
        return Math.floor((samples / 24000) * 1000);
    }
    
    notifyUI(state) {
        // Dispatch custom event for UI updates
        window.dispatchEvent(new CustomEvent('assistantStateChange', {
            detail: { state }
        }));
    }
    
    // Track audio playback progress
    updatePlaybackProgress(samplesPlayed) {
        this.audioSampleCounterPlayed += samplesPlayed;
    }
    
    // Set current audio message item ID
    setCurrentAudioItemId(itemId) {
        this.lastAudioMessageItemId = itemId;
    }
    
    // Set processing state
    setProcessingState(isProcessing, responseId = null) {
        this.isProcessing = isProcessing;
        this.isAssistantSpeaking = isProcessing;
        
        if (responseId) {
            this.currentResponseId = responseId;
        }
        
        this.notifyUI(isProcessing ? 'speaking' : 'listening');
    }
    
    // Check if audio chunk should be played
    shouldPlayAudioChunk(responseId) {
        return !this.interruptedResponses.has(responseId) && !this.isUserSpeaking;
    }
    
    // Clean up old interrupted responses
    cleanupInterruptedResponses() {
        if (this.interruptedResponses.size > 10) {
            const arr = Array.from(this.interruptedResponses);
            this.interruptedResponses = new Set(arr.slice(-10));
            console.log(`Cleaned up interrupted responses, keeping ${this.interruptedResponses.size}`);
        }
    }
    
    // Handle response completion
    handleResponseComplete(responseId) {
        if (this.currentResponseId === responseId) {
            this.setProcessingState(false);
            this.audioSampleCounter = 0;
            this.audioSampleCounterPlayed = 0;
        }
    }
}

// Export for use in main app
window.InterruptionManager = InterruptionManager;