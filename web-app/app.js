/**
 * Voice Assistant Web Application
 * Uses WebSocket for real-time voice interaction with the backend
 */

class VoiceAssistant {
    constructor() {
        this.socket = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isConnected = false;
        this.audioContext = null;
        this.currentLanguage = 'auto';
        
        // WebSocket URL - adjust based on your deployment
        this.wsUrl = window.location.hostname === 'localhost' 
            ? 'ws://localhost:8000/ws'
            : `wss://${window.location.hostname}/ws`;
        
        // UI Elements
        this.elements = {
            connectionStatus: document.getElementById('connection-status'),
            statusText: document.querySelector('.status-text'),
            chatMessages: document.getElementById('chat-messages'),
            textInput: document.getElementById('text-input'),
            sendBtn: document.getElementById('send-btn'),
            voiceBtn: document.getElementById('voice-btn'),
            detectedLanguage: document.getElementById('detected-language'),
            flightResults: document.getElementById('flight-results-container')
        };
        
        this.init();
    }
    
    async init() {
        // Initialize WebSocket connection
        await this.connectWebSocket();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Request microphone permissions
        await this.requestMicrophonePermission();
        
        // Initialize audio context
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    async connectWebSocket() {
        try {
            this.socket = new WebSocket(this.wsUrl);
            
            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus('connected');
                
                // Send initial configuration
                this.socket.send(JSON.stringify({
                    type: 'config',
                    language: this.currentLanguage
                }));
                
                this.addSystemMessage('Connected to Flight Assistant. Speak or type in any language!');
            };
            
            this.socket.onmessage = async (event) => {
                const data = JSON.parse(event.data);
                await this.handleServerMessage(data);
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error');
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus('disconnected');
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.connectWebSocket();
                    }
                }, 3000);
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus('error');
        }
    }
    
    async handleServerMessage(data) {
        switch (data.type) {
            case 'user_transcript':
                // Show what the user said
                this.addUserMessage(data.text);
                if (data.language) {
                    this.updateDetectedLanguage(data.language);
                }
                break;
                
            case 'transcript_delta':
                // Real-time assistant transcript update
                this.updateTranscript(data.text);
                break;
                
            case 'audio_delta':
                // Real-time audio response
                if (data.audio) {
                    await this.playAudioChunk(data.audio);
                }
                break;
                
            case 'response_complete':
                // Complete response received
                if (data.text) {
                    this.addAssistantMessage(data.text);
                }
                if (data.audio) {
                    await this.playAudio(data.audio);
                }
                if (data.language) {
                    this.updateDetectedLanguage(data.language);
                }
                // Parse for flight results
                if (data.text && data.text.includes('flight')) {
                    this.parseAndDisplayFlights(data.text);
                }
                break;
                
            case 'error':
                console.error('Server error:', data.error);
                this.addSystemMessage(`Error: ${data.error}`);
                break;
                
            case 'config_updated':
                console.log('Configuration updated:', data.config);
                break;
                
            case 'pong':
                // Heartbeat response
                break;
        }
    }
    
    setupEventListeners() {
        // Voice button - hold to record
        this.elements.voiceBtn.addEventListener('mousedown', () => this.startRecording());
        this.elements.voiceBtn.addEventListener('mouseup', () => this.stopRecording());
        this.elements.voiceBtn.addEventListener('mouseleave', () => this.stopRecording());
        
        // Touch events for mobile
        this.elements.voiceBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        this.elements.voiceBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopRecording();
        });
        
        // Text input
        this.elements.sendBtn.addEventListener('click', () => this.sendTextMessage());
        this.elements.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendTextMessage();
            }
        });
        
        // Heartbeat to keep connection alive
        setInterval(() => {
            if (this.isConnected) {
                this.socket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    }
    
    async requestMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            console.log('Microphone permission granted');
        } catch (error) {
            console.error('Microphone permission denied:', error);
            this.addSystemMessage('Microphone access is required for voice input.');
        }
    }
    
    async startRecording() {
        if (!this.isConnected) {
            this.addSystemMessage('Not connected to server. Please wait...');
            return;
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                }
            });
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm'
            });
            
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                await this.sendAudioData(audioBlob);
                
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            this.elements.voiceBtn.classList.add('recording');
            this.elements.voiceBtn.querySelector('span').textContent = 'Recording...';
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.addSystemMessage('Failed to start recording. Please check your microphone.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Update UI
            this.elements.voiceBtn.classList.remove('recording');
            this.elements.voiceBtn.querySelector('span').textContent = 'Hold to Talk';
        }
    }
    
    async sendAudioData(audioBlob) {
        // Convert audio blob to base64
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];
            
            // Send to server
            this.socket.send(JSON.stringify({
                type: 'audio',
                audio: base64Audio,
                language: this.currentLanguage
            }));
            
            // Don't add message here - wait for server to send transcript
        };
        reader.readAsDataURL(audioBlob);
    }
    
    sendTextMessage() {
        const text = this.elements.textInput.value.trim();
        if (!text) return;
        
        if (!this.isConnected) {
            this.addSystemMessage('Not connected to server. Please wait...');
            return;
        }
        
        // For now, create a simple text-to-audio flow
        // In production, you might want a dedicated text endpoint
        this.addUserMessage(text);
        this.elements.textInput.value = '';
        
        // Send as text message (server should handle this)
        // For demo, we'll use the audio endpoint with TTS
        this.processTextQuery(text);
    }
    
    async processTextQuery(text) {
        try {
            // First, convert text to speech using Web Speech API or send to backend
            // For now, let's send it to the backend's process_audio endpoint
            // after converting to a simple audio format
            
            // Add the user's message immediately
            this.addUserMessage(text);
            
            // Send to backend for processing
            const response = await fetch('http://localhost:8000/process_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    language: this.currentLanguage
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // For now, show a processing message
                // In a full implementation, this would trigger the voice pipeline
                this.addAssistantMessage(data.message || "I understand you want to: " + text + ". Please use voice for flight searches.");
            }
        } catch (error) {
            console.error('Text query error:', error);
            this.addSystemMessage('Failed to process text query.');
        }
    }
    
    addMessage(role, content, className = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        
        const timestamp = new Date().toLocaleTimeString();
        const roleEmoji = role === 'user' ? '👤' : role === 'assistant' ? '🤖' : 'ℹ️';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${roleEmoji}</div>
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(content)}</div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }
    
    addUserMessage(content) {
        this.addMessage('user', content, 'user');
    }
    
    addAssistantMessage(content) {
        this.addMessage('assistant', content, 'assistant');
    }
    
    addSystemMessage(content) {
        this.addMessage('system', content, 'system');
    }
    
    updateTranscript(text) {
        // Find the last assistant message and update it
        const messages = this.elements.chatMessages.querySelectorAll('.message.assistant');
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            const contentDiv = lastMessage.querySelector('.message-text');
            contentDiv.textContent += text;
        } else {
            // Create new assistant message
            this.addAssistantMessage(text);
        }
    }
    
    async playAudio(base64Audio) {
        try {
            // Decode base64 to blob
            const byteCharacters = atob(base64Audio);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            
            // Create blob with proper MIME type
            const blob = new Blob([byteArray], { type: 'audio/mpeg' });
            const audioUrl = URL.createObjectURL(blob);
            
            // Create and play audio
            const audio = new Audio(audioUrl);
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
            };
            
            await audio.play();
        } catch (error) {
            console.error('Failed to play audio:', error);
            // Try alternative method
            try {
                const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`);
                await audio.play();
            } catch (e) {
                console.error('Alternative audio playback failed:', e);
            }
        }
    }
    
    async playAudioChunk(base64Audio) {
        // For streaming audio, you might want to queue chunks
        // This is a simplified version
        await this.playAudio(base64Audio);
    }
    
    updateConnectionStatus(status) {
        const statusElement = this.elements.connectionStatus;
        statusElement.className = `status ${status}`;
        
        const statusTexts = {
            connected: 'Connected',
            disconnected: 'Disconnected',
            error: 'Connection Error'
        };
        
        this.elements.statusText.textContent = statusTexts[status] || 'Unknown';
    }
    
    updateDetectedLanguage(language) {
        const languageNames = {
            en: 'English',
            es: 'Spanish',
            fr: 'French',
            de: 'German',
            it: 'Italian',
            pt: 'Portuguese',
            zh: 'Chinese',
            ja: 'Japanese',
            ko: 'Korean',
            ar: 'Arabic',
            hi: 'Hindi',
            ru: 'Russian'
        };
        
        this.elements.detectedLanguage.textContent = languageNames[language] || language;
    }
    
    parseAndDisplayFlights(text) {
        // Simple parsing for demo - in production, flights would come structured
        if (text.toLowerCase().includes('found') && text.includes('flight')) {
            const flightCard = document.createElement('div');
            flightCard.className = 'flight-card';
            flightCard.innerHTML = `
                <h4>Flight Results</h4>
                <p>${text}</p>
            `;
            this.elements.flightResults.innerHTML = '';
            this.elements.flightResults.appendChild(flightCard);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the voice assistant when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.voiceAssistant = new VoiceAssistant();
});