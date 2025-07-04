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
    }
    
    async start() {
        try {
            this.updateStatus('Connecting...');
            
            // Connect WebSocket first
            await this.connectWebSocket();
            
            // Then start audio
            await this.startAudioCapture();
            
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.updateStatus('Listening... (Speak naturally, no need to hold any button)');
            
        } catch (error) {
            console.error('Failed to start:', error);
            this.updateStatus(`Error: ${error.message}`);
        }
    }
    
    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket('ws://localhost:8000/ws');
            
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
        // Request microphone with specific constraints
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: this.sampleRate
            }
        });
        
        // Create audio context with correct sample rate
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: this.sampleRate
        });
        
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
                break;
                
            case 'user_transcript':
                // Final user transcript
                this.addUserMessage(data.text);
                this.clearTranscript();
                break;
                
            case 'transcript_delta':
                // Assistant's response transcription
                this.updateAssistantTranscript(data.delta);
                break;
                
            case 'audio_delta':
                // Queue audio for playback
                if (data.audio) {
                    console.log('Audio delta received:', typeof data.audio, data.audio.substring(0, 50) + '...');
                    const audioData = this.base64ToArrayBuffer(data.audio);
                    this.audioQueue.push(audioData);
                    console.log(`Audio chunk received, queue size: ${this.audioQueue.length}`);
                    if (!this.isPlaying) {
                        this.playAudioQueue();
                    }
                }
                break;
                
            case 'response_complete':
                // Complete response
                if (data.text) {
                    this.addAssistantMessage(data.text);
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
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }
        
        this.isPlaying = true;
        const audioData = this.audioQueue.shift();
        
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
            source.connect(this.audioContext.destination);
            
            source.onended = () => {
                // Play next chunk in queue
                this.playAudioQueue();
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
            // Smooth scroll to bottom
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.voiceAssistant = new RealtimeVoiceAssistant();
});