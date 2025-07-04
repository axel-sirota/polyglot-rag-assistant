/**
 * Real-time Voice Assistant with VAD
 * No hold-to-talk, automatic speech detection
 */

class RealtimeVoiceAssistant {
    constructor() {
        this.ws = null;
        this.audioContext = null;
        this.mediaStream = null;
        this.processor = null;
        this.isRecording = false;
        this.audioQueue = [];
        this.isPlaying = false;
        
        // Managers
        this.interruptionManager = null;
        this.conversationManager = null;
        this.feedbackManager = null;
        
        // Audio handling
        this.currentSource = null;
        this.gainNode = null;
        
        // UI elements
        this.statusEl = document.getElementById('status');
        this.transcriptEl = document.getElementById('user-transcript');
        this.messagesEl = document.getElementById('messages');
        this.startBtn = document.getElementById('start-btn');
        this.stopBtn = document.getElementById('stop-btn');
        
        // Audio format matching Realtime API requirements
        this.sampleRate = 24000;
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        this.startBtn?.addEventListener('click', () => this.start());
        this.stopBtn?.addEventListener('click', () => this.stop());
        
        // Listen for assistant state changes from interruption manager
        window.addEventListener('assistantStateChange', (event) => {
            const state = event.detail.state;
            console.log(`Assistant state changed to: ${state}`);
            
            // Update UI based on state
            if (state === 'interrupted') {
                this.updateStatus('Interrupted - listening...');
            } else if (state === 'speaking') {
                this.updateStatus('Assistant is speaking...');
            } else if (state === 'listening') {
                this.updateStatus('Listening... (Speak naturally)');
            }
        });
    }
    
    async start() {
        try {
            this.updateStatus('Connecting...');
            
            // Initialize feedback manager
            this.feedbackManager = new UserFeedbackManager();
            await this.feedbackManager.initialize();
            this.feedbackManager.showState('connecting');
            
            // Connect WebSocket first
            await this.connectWebSocket();
            
            // Then start audio
            await this.startAudioCapture();
            
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.updateStatus('Listening... (Speak naturally, no need to hold any button)');
            this.feedbackManager.showState('listening');
            
        } catch (error) {
            console.error('Failed to start:', error);
            this.updateStatus(`Error: ${error.message}`);
            if (this.feedbackManager) {
                this.feedbackManager.showState('error', error.message);
            }
        }
    }
    
    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket('ws://localhost:8000/ws');
            
            // Initialize managers
            this.interruptionManager = new InterruptionManager(this.ws);
            this.conversationManager = new ConversationManager();
            this.conversationManager.initialize(this.messagesEl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                // Send config to enable continuous mode
                this.ws.send(JSON.stringify({
                    type: 'config',
                    continuous: true,
                    language: 'auto'
                }));
                resolve();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
            
            this.ws.onmessage = async (event) => {
                const data = JSON.parse(event.data);
                await this.handleServerMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateStatus('Disconnected');
                this.stop();
            };
        });
    }
    
    async startAudioCapture() {
        // Request microphone with enhanced echo cancellation
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: { ideal: this.sampleRate }
            }
        });
        
        // Create audio context with correct sample rate
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: this.sampleRate
        });
        
        // Create gain node for audio ducking and echo reduction
        this.gainNode = this.audioContext.createGain();
        this.gainNode.gain.value = 0.5; // Reduce volume significantly to prevent echo
        this.gainNode.connect(this.audioContext.destination);
        
        // Initialize interruption manager with audio context
        if (this.interruptionManager) {
            await this.interruptionManager.initialize(this.audioContext, this.gainNode);
        }
        
        // Resume audio context if suspended (required for some browsers)
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
            console.log('Audio context resumed');
        }
        
        const source = this.audioContext.createMediaStreamSource(this.mediaStream);
        
        // Use ScriptProcessor for now (AudioWorklet requires HTTPS in some browsers)
        this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
        
        this.processor.onaudioprocess = (e) => {
            if (!this.isRecording) return;
            
            // Skip processing if assistant is speaking to prevent echo
            if (this.interruptionManager && this.interruptionManager.isAssistantSpeaking && this.isPlaying) {
                return;
            }
            
            const inputData = e.inputBuffer.getChannelData(0);
            // Convert Float32 to PCM16 for Realtime API
            const pcm16 = this.float32ToPCM16(inputData);
            
            // Send audio data to server
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                // Convert to base64
                const base64 = this.arrayBufferToBase64(pcm16.buffer);
                this.ws.send(JSON.stringify({
                    type: 'audio',
                    audio: base64,
                    continuous: true
                }));
            }
        };
        
        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);
        this.isRecording = true;
    }
    
    float32ToPCM16(float32Array) {
        const pcm16 = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            // Convert float32 (-1.0 to 1.0) to int16 (-32768 to 32767)
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return pcm16;
    }
    
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }
    
    base64ToArrayBuffer(base64) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }
    
    async handleServerMessage(data) {
        switch (data.type) {
            case 'user_transcript_delta':
                // Show real-time transcription as user speaks
                this.updateTranscript(data.delta);
                // Notify interruption manager of user speech
                if (this.interruptionManager) {
                    await this.interruptionManager.handleSpeechStarted(data);
                }
                break;
                
            case 'user_transcript':
                // Final user transcript
                if (this.conversationManager) {
                    this.conversationManager.addUserMessage(data.text);
                } else {
                    this.addUserMessage(data.text);
                }
                this.clearTranscript();
                // Notify interruption manager that user speech ended
                if (this.interruptionManager) {
                    this.interruptionManager.handleSpeechEnded();
                }
                break;
                
            case 'transcript_delta':
                // Assistant's response transcription
                if (this.conversationManager) {
                    await this.conversationManager.handleConversationUpdate({
                        item: {
                            id: data.item_id || data.response_id || `assistant-${Date.now()}`,
                            type: 'message',
                            role: 'assistant'
                        },
                        delta: { text: data.delta }
                    });
                } else {
                    this.updateAssistantTranscript(data.delta);
                }
                // Track response ID and notify interruption manager
                if (data.response_id || data.item_id) {
                    const responseId = data.response_id || data.item_id;
                    if (this.interruptionManager) {
                        this.interruptionManager.setProcessingState(true, responseId);
                        this.interruptionManager.setCurrentAudioItemId(data.item_id || responseId);
                    }
                }
                break;
                
            case 'audio_delta':
                // Check if this audio should be played
                const responseId = data.response_id || data.item_id;
                if (this.interruptionManager && !this.interruptionManager.shouldPlayAudioChunk(responseId)) {
                    console.log(`Discarding audio from interrupted response: ${responseId}`);
                    break;
                }
                
                // Double-check user is not speaking
                if (this.interruptionManager && this.interruptionManager.isUserSpeaking) {
                    console.log('Discarding audio because user is speaking');
                    break;
                }
                
                // Queue audio for playback
                if (data.audio) {
                    console.log('Audio delta received:', typeof data.audio, data.audio.substring(0, 50) + '...');
                    const audioData = this.base64ToArrayBuffer(data.audio);
                    this.audioQueue.push({
                        data: audioData,
                        responseId: responseId
                    });
                    console.log(`Audio chunk received, queue size: ${this.audioQueue.length}`);
                    if (!this.isPlaying) {
                        this.playAudioQueue();
                    }
                }
                break;
                
            case 'response_complete':
                // Complete response
                const completeId = data.response_id || data.item_id;
                if (this.conversationManager && completeId) {
                    this.conversationManager.completeItem(completeId);
                }
                if (data.text && !this.conversationManager) {
                    this.addAssistantMessage(data.text);
                }
                // Notify interruption manager
                if (this.interruptionManager) {
                    this.interruptionManager.handleResponseComplete(completeId);
                }
                break;
                
            case 'interrupted':
                console.log('Assistant was interrupted');
                // Clear audio queue and stop playback
                if (this.interruptionManager) {
                    this.interruptionManager.handleInterruption(data.item_id);
                }
                // Clear the entire audio queue
                this.audioQueue = [];
                this.isPlaying = false;
                // Stop current audio immediately
                if (this.currentSource) {
                    try {
                        this.currentSource.stop();
                    } catch (e) {
                        // Already stopped
                    }
                    this.currentSource = null;
                }
                // Cancel any pending audio playback
                if (this.audioPlaybackTimer) {
                    clearTimeout(this.audioPlaybackTimer);
                    this.audioPlaybackTimer = null;
                }
                break;
                
            case 'user_speech_started':
                // User started speaking - prepare for interruption
                if (this.interruptionManager) {
                    this.interruptionManager.handleSpeechStarted({});
                }
                break;
                
            case 'user_speech_stopped':
                // User stopped speaking
                if (this.interruptionManager) {
                    this.interruptionManager.handleSpeechEnded();
                }
                break;
                
            case 'error':
                console.error('Server error:', data.error);
                this.updateStatus(`Error: ${data.error}`);
                break;
        }
    }
    
    updateTranscript(text) {
        if (this.transcriptEl) {
            this.transcriptEl.textContent += text;
            this.transcriptEl.style.display = 'block';
        }
    }
    
    clearTranscript() {
        if (this.transcriptEl) {
            this.transcriptEl.textContent = '';
            this.transcriptEl.style.display = 'none';
        }
    }
    
    updateAssistantTranscript(text) {
        // Find or create the latest assistant message element
        let assistantMsg = this.messagesEl?.querySelector('.assistant-message:last-child .message-text');
        if (!assistantMsg) {
            this.addAssistantMessage('');
            assistantMsg = this.messagesEl?.querySelector('.assistant-message:last-child .message-text');
        }
        if (assistantMsg) {
            assistantMsg.textContent += text;
            // Scroll to show new content
            this.scrollToBottom();
        }
    }
    
    async playAudioQueue() {
        // Check if interrupted before starting
        if (this.interruptionManager && this.interruptionManager.isUserSpeaking) {
            console.log('User is speaking, stopping audio queue');
            this.audioQueue = [];
            this.isPlaying = false;
            return;
        }
        
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }
        
        this.isPlaying = true;
        const audioChunk = this.audioQueue.shift();
        
        // Check if this audio should be played
        if (this.interruptionManager && audioChunk.responseId && 
            !this.interruptionManager.shouldPlayAudioChunk(audioChunk.responseId)) {
            console.log(`Skipping playback of interrupted audio: ${audioChunk.responseId}`);
            // Clear remaining chunks from the same response
            this.audioQueue = this.audioQueue.filter(chunk => 
                chunk.responseId !== audioChunk.responseId
            );
            // Continue with next chunk if available
            if (this.audioQueue.length > 0) {
                this.playAudioQueue();
            } else {
                this.isPlaying = false;
            }
            return;
        }
        
        const audioData = audioChunk.data || audioChunk; // Handle both old and new format
        
        try {
            // Ensure audio context is running
            if (this.audioContext && this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
                console.log('Audio context resumed for playback');
            }
            // Convert PCM16 to Float32 for Web Audio
            const pcm16 = new Int16Array(audioData);
            const float32 = new Float32Array(pcm16.length);
            
            for (let i = 0; i < pcm16.length; i++) {
                float32[i] = pcm16[i] / (pcm16[i] < 0 ? 0x8000 : 0x7FFF);
            }
            
            // Create audio buffer
            const audioBuffer = this.audioContext.createBuffer(1, float32.length, this.sampleRate);
            audioBuffer.getChannelData(0).set(float32);
            
            // Play the audio
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.gainNode); // Connect through gain node for ducking
            
            // Keep reference to current source for interruption
            this.currentSource = source;
            if (this.interruptionManager) {
                this.interruptionManager.currentAudioSource = source;
            }
            
            source.onended = () => {
                this.currentSource = null;
                if (this.interruptionManager) {
                    this.interruptionManager.currentAudioSource = null;
                    // Update playback progress
                    const samplesPlayed = audioBuffer.length;
                    this.interruptionManager.updatePlaybackProgress(samplesPlayed);
                }
                // Check if we should continue playing
                if (!this.interruptionManager || !this.interruptionManager.isUserSpeaking) {
                    // Play next chunk in queue with a small delay
                    this.audioPlaybackTimer = setTimeout(() => {
                        this.playAudioQueue();
                    }, 10);
                } else {
                    this.isPlaying = false;
                    console.log('User is speaking, stopping audio playback');
                }
            };
            
            source.start();
            console.log(`Playing audio chunk, ${this.audioQueue.length} chunks remaining`);
            
        } catch (error) {
            console.error('Audio playback error:', error);
            this.isPlaying = false;
        }
    }
    
    addUserMessage(text) {
        if (!text || !this.messagesEl) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        
        const label = document.createElement('div');
        label.className = 'message-label';
        label.textContent = 'You:';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = text;
        
        messageDiv.appendChild(label);
        messageDiv.appendChild(textDiv);
        this.messagesEl.appendChild(messageDiv);
        
        // Scroll to bottom - use parent container for better scrolling
        this.scrollToBottom();
    }
    
    addAssistantMessage(text) {
        if (!this.messagesEl) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        
        const label = document.createElement('div');
        label.className = 'message-label';
        label.textContent = 'Assistant:';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = text || '';
        
        messageDiv.appendChild(label);
        messageDiv.appendChild(textDiv);
        this.messagesEl.appendChild(messageDiv);
        
        // Scroll to bottom - use parent container for better scrolling
        this.scrollToBottom();
    }
    
    updateStatus(status) {
        if (this.statusEl) {
            this.statusEl.textContent = status;
        }
    }
    
    async stop() {
        this.isRecording = false;
        
        // Stop audio
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }
        
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
        }
        
        // Close WebSocket
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        // Reset UI
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.updateStatus('Stopped');
        this.clearTranscript();
    }
    
    scrollToBottom() {
        // Find the chat container parent
        const chatContainer = this.messagesEl.closest('.chat-container');
        if (chatContainer) {
            // Force scroll to bottom with a small delay
            setTimeout(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }, 100);
        }
    }
    
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.app = new RealtimeVoiceAssistant();
    window.voiceAssistant = window.app; // For compatibility
});