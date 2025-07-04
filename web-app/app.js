// Configuration
const CONFIG = {
    LIVEKIT_URL: process.env.LIVEKIT_URL || 'wss://your-project.livekit.cloud',
    API_ENDPOINT: process.env.API_ENDPOINT || '/api',
    ROOM_NAME: 'polyglot-rag-demo'
};

// Global state
let room = null;
let localAudioTrack = null;
let isRecording = false;
let currentLanguage = 'en';

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');
const voiceBtn = document.getElementById('voice-btn');
const connectionStatus = document.getElementById('connection-status');
const detectedLanguage = document.getElementById('detected-language');
const flightResultsContainer = document.getElementById('flight-results-container');

// Initialize the application
async function init() {
    try {
        // Get access token from backend
        const token = await getAccessToken();
        
        // Connect to LiveKit room
        await connectToRoom(token);
        
        // Set up event listeners
        setupEventListeners();
        
        updateConnectionStatus('connected');
        addSystemMessage('Connected to Polyglot RAG Assistant. Speak or type in any language!');
    } catch (error) {
        console.error('Initialization error:', error);
        updateConnectionStatus('disconnected');
        addSystemMessage('Failed to connect. Please refresh the page.');
    }
}

// Get access token from backend
async function getAccessToken() {
    try {
        const response = await fetch(`${CONFIG.API_ENDPOINT}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                identity: `web-user-${Date.now()}`,
                room: CONFIG.ROOM_NAME
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get access token');
        }
        
        const data = await response.json();
        return data.token;
    } catch (error) {
        console.error('Token error:', error);
        // For demo, return a mock token
        return 'mock-token';
    }
}

// Connect to LiveKit room
async function connectToRoom(token) {
    updateConnectionStatus('connecting');
    
    room = new LivekitClient.Room({
        adaptiveStream: true,
        dynacast: true,
        videoCaptureDefaults: {
            resolution: LivekitClient.VideoPresets.h720.resolution
        }
    });
    
    // Set up room event listeners
    room.on('participantConnected', (participant) => {
        console.log('Participant connected:', participant.identity);
    });
    
    room.on('trackSubscribed', (track, publication, participant) => {
        if (track.kind === 'audio') {
            // Handle incoming audio (assistant's voice)
            const audioElement = track.attach();
            document.body.appendChild(audioElement);
        }
    });
    
    room.on('dataReceived', (data, participant) => {
        // Handle data messages (transcriptions, results, etc.)
        handleDataMessage(data);
    });
    
    room.on('disconnected', () => {
        updateConnectionStatus('disconnected');
        addSystemMessage('Disconnected from server.');
    });
    
    // Connect to the room
    await room.connect(CONFIG.LIVEKIT_URL, token);
}

// Set up event listeners
function setupEventListeners() {
    // Text input
    textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendTextMessage();
        }
    });
    
    sendBtn.addEventListener('click', sendTextMessage);
    
    // Voice input
    voiceBtn.addEventListener('mousedown', startRecording);
    voiceBtn.addEventListener('mouseup', stopRecording);
    voiceBtn.addEventListener('mouseleave', stopRecording);
    
    // Touch events for mobile
    voiceBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startRecording();
    });
    voiceBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        stopRecording();
    });
}

// Send text message
async function sendTextMessage() {
    const message = textInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addUserMessage(message);
    textInput.value = '';
    
    // Send to backend
    try {
        const response = await fetch(`${CONFIG.API_ENDPOINT}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                language: currentLanguage
            })
        });
        
        const data = await response.json();
        
        // Update language if detected
        if (data.language) {
            updateDetectedLanguage(data.language);
        }
        
        // Add assistant response
        addAssistantMessage(data.response);
        
        // Update flight results if any
        if (data.flightResults) {
            displayFlightResults(data.flightResults);
        }
    } catch (error) {
        console.error('Chat error:', error);
        addAssistantMessage('Sorry, I encountered an error. Please try again.');
    }
}

// Start voice recording
async function startRecording() {
    if (isRecording) return;
    
    try {
        isRecording = true;
        voiceBtn.classList.add('recording');
        voiceBtn.querySelector('span').textContent = 'Recording...';
        
        // Request microphone permission
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Create audio track
        localAudioTrack = await LivekitClient.createLocalAudioTrack({
            mediaStreamTrack: stream.getAudioTracks()[0]
        });
        
        // Publish to room
        await room.localParticipant.publishTrack(localAudioTrack);
        
    } catch (error) {
        console.error('Recording error:', error);
        stopRecording();
        addSystemMessage('Microphone access denied. Please enable microphone permissions.');
    }
}

// Stop voice recording
async function stopRecording() {
    if (!isRecording) return;
    
    isRecording = false;
    voiceBtn.classList.remove('recording');
    voiceBtn.querySelector('span').textContent = 'Hold to Talk';
    
    if (localAudioTrack) {
        // Stop and unpublish track
        room.localParticipant.unpublishTrack(localAudioTrack);
        localAudioTrack.stop();
        localAudioTrack = null;
    }
}

// Handle data messages from LiveKit
function handleDataMessage(data) {
    try {
        const message = JSON.parse(new TextDecoder().decode(data));
        
        switch (message.type) {
            case 'transcription':
                // Show user's transcribed speech
                addUserMessage(message.text);
                break;
                
            case 'response':
                // Show assistant's response
                addAssistantMessage(message.text);
                if (message.language) {
                    updateDetectedLanguage(message.language);
                }
                break;
                
            case 'flightResults':
                // Display flight results
                displayFlightResults(message.results);
                break;
                
            case 'error':
                addSystemMessage(`Error: ${message.message}`);
                break;
        }
    } catch (error) {
        console.error('Data message error:', error);
    }
}

// Add user message to chat
function addUserMessage(text) {
    const messageEl = createMessageElement(text, 'user');
    chatMessages.appendChild(messageEl);
    scrollToBottom();
}

// Add assistant message to chat
function addAssistantMessage(text) {
    const messageEl = createMessageElement(text, 'assistant');
    chatMessages.appendChild(messageEl);
    scrollToBottom();
}

// Add system message to chat
function addSystemMessage(text) {
    const messageEl = createMessageElement(text, 'system');
    chatMessages.appendChild(messageEl);
    scrollToBottom();
}

// Create message element
function createMessageElement(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = type === 'user' ? '👤' : type === 'assistant' ? '🤖' : 'ℹ️';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString();
    contentDiv.appendChild(timeDiv);
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    return messageDiv;
}

// Update connection status
function updateConnectionStatus(status) {
    connectionStatus.className = `status ${status}`;
    const statusText = connectionStatus.querySelector('.status-text');
    
    switch (status) {
        case 'connected':
            statusText.textContent = 'Connected';
            break;
        case 'connecting':
            statusText.textContent = 'Connecting...';
            break;
        case 'disconnected':
            statusText.textContent = 'Disconnected';
            break;
    }
}

// Update detected language
function updateDetectedLanguage(language) {
    currentLanguage = language;
    const languages = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ja': 'Japanese',
        'zh': 'Chinese',
        'ko': 'Korean',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'ru': 'Russian'
    };
    
    detectedLanguage.textContent = languages[language] || language.toUpperCase();
}

// Display flight results
function displayFlightResults(results) {
    if (!results || results.length === 0) {
        flightResultsContainer.innerHTML = '<p class="no-results">No flights found</p>';
        return;
    }
    
    flightResultsContainer.innerHTML = '';
    
    results.slice(0, 5).forEach((flight, index) => {
        const flightCard = document.createElement('div');
        flightCard.className = 'flight-card';
        
        flightCard.innerHTML = `
            <h4>${flight.airline} - ${flight.flight_number}</h4>
            <div class="flight-details">
                <div>🛫 ${formatTime(flight.departure_time)}</div>
                <div>🛬 ${formatTime(flight.arrival_time)}</div>
                <div>⏱️ ${flight.duration}</div>
                <div>🔄 ${flight.stops} stops</div>
            </div>
            <div class="flight-price">${flight.price}</div>
        `;
        
        flightResultsContainer.appendChild(flightCard);
    });
}

// Format time for display
function formatTime(isoTime) {
    try {
        const date = new Date(isoTime);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return isoTime;
    }
}

// Scroll chat to bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);