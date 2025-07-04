/**
 * User Feedback Manager
 * Provides real-time visual and audio feedback for user actions
 */

class UserFeedbackManager {
    constructor() {
        this.feedbackElement = null;
        this.audioContext = null;
        this.audioBuffers = new Map();
        this.visualFeedback = new VisualFeedbackRenderer();
        
        this.states = {
            idle: { 
                text: "Ready to help", 
                audio: null, 
                color: '#4CAF50',
                animation: 'pulse',
                icon: '✓'
            },
            listening: { 
                text: "Listening...", 
                audio: null, 
                color: '#2196F3',
                animation: 'wave',
                icon: '🎤'
            },
            processing: { 
                text: "Processing your request...", 
                audio: null, 
                color: '#FF9800',
                animation: 'spin',
                icon: '⚙️'
            },
            thinking: { 
                text: "Thinking...", 
                audio: null, 
                color: '#9C27B0',
                animation: 'dots',
                icon: '🤔'
            },
            searching: { 
                text: "Searching for flights...", 
                audio: null, 
                color: '#00BCD4',
                animation: 'scan',
                icon: '✈️'
            },
            speaking: { 
                text: "Speaking...", 
                audio: null, 
                color: '#4CAF50',
                animation: 'wave',
                icon: '🔊'
            },
            interrupted: { 
                text: "Interrupted", 
                audio: null, 
                color: '#FFC107',
                animation: 'fade',
                icon: '⚡'
            },
            error: { 
                text: "Something went wrong", 
                audio: null, 
                color: '#F44336',
                animation: 'shake',
                icon: '❌'
            },
            connecting: { 
                text: "Connecting...", 
                audio: null, 
                color: '#607D8B',
                animation: 'pulse',
                icon: '🔌'
            }
        };
        
        this.currentState = 'idle';
        this.stateStartTime = Date.now();
    }
    
    async initialize() {
        // Create audio context
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Create feedback UI element
        this.createFeedbackUI();
        
        // Listen for state changes
        this.setupEventListeners();
        
        // Initialize visual feedback
        const canvas = document.getElementById('feedback-canvas');
        if (canvas) {
            this.visualFeedback.init(canvas);
        }
    }
    
    createFeedbackUI() {
        // Check if container already exists
        if (document.getElementById('user-feedback-container')) {
            this.feedbackElement = document.getElementById('feedback-message');
            this.detailElement = document.getElementById('feedback-detail');
            this.progressElement = document.getElementById('feedback-progress');
            this.iconElement = document.getElementById('feedback-icon');
            return;
        }
        
        // Main feedback container
        const container = document.createElement('div');
        container.id = 'user-feedback-container';
        container.className = 'feedback-container';
        container.innerHTML = `
            <div class="feedback-header">
                <span id="feedback-icon" class="feedback-icon">✓</span>
                <div class="feedback-text">
                    <span id="feedback-message">Ready to help</span>
                    <span id="feedback-detail" class="feedback-detail"></span>
                </div>
                <div class="feedback-timer" id="feedback-timer"></div>
            </div>
            <div class="feedback-visual">
                <canvas id="feedback-canvas" width="260" height="40"></canvas>
            </div>
            <div class="feedback-progress">
                <div class="progress-bar" id="feedback-progress"></div>
            </div>
        `;
        
        // Add styles
        const styles = document.createElement('style');
        styles.textContent = `
            .feedback-container {
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(255, 255, 255, 0.95);
                color: #333;
                padding: 15px 20px;
                border-radius: 12px;
                backdrop-filter: blur(10px);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                min-width: 300px;
                transition: all 0.3s ease;
                z-index: 1000;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            
            .feedback-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 10px;
            }
            
            .feedback-icon {
                font-size: 24px;
                transition: transform 0.3s ease;
            }
            
            .feedback-text {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 2px;
            }
            
            #feedback-message {
                font-size: 16px;
                font-weight: 500;
                transition: color 0.3s ease;
            }
            
            .feedback-detail {
                font-size: 12px;
                opacity: 0.7;
                display: none;
            }
            
            .feedback-timer {
                font-size: 12px;
                opacity: 0.6;
                min-width: 40px;
                text-align: right;
            }
            
            .feedback-visual {
                margin: 10px 0;
                border-radius: 8px;
                overflow: hidden;
                background: rgba(0, 0, 0, 0.03);
            }
            
            .feedback-progress {
                margin-top: 10px;
                height: 3px;
                background: rgba(0, 0, 0, 0.1);
                border-radius: 3px;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                background: currentColor;
                width: 0%;
                transition: width 0.3s ease;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.05); opacity: 0.8; }
            }
            
            @keyframes wave {
                0%, 100% { transform: translateY(0); }
                25% { transform: translateY(-2px); }
                75% { transform: translateY(2px); }
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            @keyframes dots {
                0%, 20% { content: '.'; }
                40% { content: '..'; }
                60%, 100% { content: '...'; }
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            
            @keyframes scan {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            
            @keyframes fade {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .state-pulse .feedback-icon { animation: pulse 1.5s infinite; }
            .state-wave .feedback-icon { animation: wave 1s infinite; }
            .state-spin .feedback-icon { animation: spin 1s linear infinite; }
            .state-shake .feedback-icon { animation: shake 0.5s; }
            .state-fade .feedback-icon { animation: fade 1s infinite; }
        `;
        
        document.head.appendChild(styles);
        document.body.appendChild(container);
        
        this.feedbackElement = document.getElementById('feedback-message');
        this.detailElement = document.getElementById('feedback-detail');
        this.progressElement = document.getElementById('feedback-progress');
        this.iconElement = document.getElementById('feedback-icon');
        this.timerElement = document.getElementById('feedback-timer');
        this.canvasElement = document.getElementById('feedback-canvas');
    }
    
    setupEventListeners() {
        // Listen for state changes
        window.addEventListener('assistantStateChange', (event) => {
            this.showState(event.detail.state, event.detail.detail);
        });
        
        // Listen for specific events
        window.addEventListener('flightSearchStatus', (event) => {
            this.showDetail(event.detail.message);
        });
        
        // Listen for progress updates
        window.addEventListener('progressUpdate', (event) => {
            this.updateProgress(event.detail.progress);
        });
    }
    
    async showState(stateName, detail = '') {
        const state = this.states[stateName];
        if (!state) {
            console.warn(`Unknown state: ${stateName}`);
            return;
        }
        
        this.currentState = stateName;
        this.stateStartTime = Date.now();
        
        // Update visual state
        const container = document.getElementById('user-feedback-container');
        container.className = `feedback-container state-${state.animation}`;
        container.style.borderColor = state.color;
        
        // Update icon
        if (this.iconElement) {
            this.iconElement.textContent = state.icon;
            this.iconElement.style.color = state.color;
        }
        
        // Update text
        this.feedbackElement.textContent = state.text;
        this.feedbackElement.style.color = state.color;
        
        if (detail) {
            this.detailElement.textContent = detail;
            this.detailElement.style.display = 'block';
        } else {
            this.detailElement.style.display = 'none';
        }
        
        // Update visual feedback
        this.visualFeedback.setState(stateName, state.color);
        
        // Update progress bar color
        this.progressElement.style.backgroundColor = state.color;
        
        // Start timer for certain states
        if (['processing', 'thinking', 'searching'].includes(stateName)) {
            this.startTimer();
        } else {
            this.stopTimer();
        }
        
        // Auto-hide error messages after 5 seconds
        if (stateName === 'error') {
            setTimeout(() => {
                if (this.currentState === 'error') {
                    this.showState('idle');
                }
            }, 5000);
        }
    }
    
    showDetail(detail) {
        this.detailElement.textContent = detail;
        this.detailElement.style.display = 'block';
    }
    
    updateProgress(progress) {
        this.progressElement.style.width = `${Math.min(100, Math.max(0, progress))}%`;
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.stateStartTime) / 1000);
            if (this.timerElement) {
                this.timerElement.textContent = `${elapsed}s`;
            }
        }, 100);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        if (this.timerElement) {
            this.timerElement.textContent = '';
        }
    }
}

// Visual feedback renderer
class VisualFeedbackRenderer {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.animationId = null;
        this.currentState = 'idle';
        this.currentColor = '#4CAF50';
        this.particles = [];
    }
    
    init(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.startAnimation();
    }
    
    setState(state, color) {
        this.currentState = state;
        this.currentColor = color;
        
        // Reset particles for certain states
        if (state === 'searching' || state === 'processing') {
            this.initParticles();
        }
    }
    
    initParticles() {
        this.particles = [];
        for (let i = 0; i < 5; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: this.canvas.height / 2,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                size: Math.random() * 3 + 1,
                alpha: 1
            });
        }
    }
    
    startAnimation() {
        const animate = () => {
            this.clear();
            
            switch (this.currentState) {
                case 'listening':
                    this.drawWaveform();
                    break;
                case 'processing':
                case 'thinking':
                    this.drawProcessing();
                    break;
                case 'speaking':
                    this.drawSpeakingWave();
                    break;
                case 'searching':
                    this.drawSearching();
                    break;
                case 'error':
                    this.drawError();
                    break;
                default:
                    this.drawIdle();
            }
            
            this.animationId = requestAnimationFrame(animate);
        };
        
        animate();
    }
    
    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    drawWaveform() {
        const time = Date.now() / 1000;
        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        
        for (let x = 0; x < this.canvas.width; x += 5) {
            const y = this.canvas.height / 2 + 
                     Math.sin((x / 20) + time * 2) * 10 * 
                     Math.sin(time * 0.5);
            if (x === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }
        
        this.ctx.stroke();
    }
    
    drawProcessing() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const time = Date.now() / 1000;
        
        // Draw rotating dots
        for (let i = 0; i < 3; i++) {
            const angle = (time * 2) + (i * Math.PI * 2 / 3);
            const x = centerX + Math.cos(angle) * 15;
            const y = centerY + Math.sin(angle) * 15;
            
            this.ctx.fillStyle = this.currentColor;
            this.ctx.globalAlpha = 0.8 - (i * 0.2);
            this.ctx.beginPath();
            this.ctx.arc(x, y, 4, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        this.ctx.globalAlpha = 1;
    }
    
    drawSpeakingWave() {
        const time = Date.now() / 1000;
        const centerY = this.canvas.height / 2;
        
        this.ctx.fillStyle = this.currentColor;
        
        for (let i = 0; i < 7; i++) {
            const x = (this.canvas.width / 8) * (i + 1);
            const height = Math.abs(Math.sin(time * 3 + i * 0.5)) * 15 + 5;
            
            this.ctx.fillRect(
                x - 2, 
                centerY - height / 2, 
                4, 
                height
            );
        }
    }
    
    drawSearching() {
        // Update and draw particles
        this.ctx.fillStyle = this.currentColor;
        
        this.particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.alpha -= 0.01;
            
            // Wrap around
            if (particle.x < 0) particle.x = this.canvas.width;
            if (particle.x > this.canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.height;
            if (particle.y > this.canvas.height) particle.y = 0;
            
            // Reset faded particles
            if (particle.alpha <= 0) {
                particle.alpha = 1;
                particle.x = Math.random() * this.canvas.width;
                particle.y = this.canvas.height / 2;
            }
            
            this.ctx.globalAlpha = particle.alpha;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fill();
        });
        
        this.ctx.globalAlpha = 1;
    }
    
    drawError() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const time = Date.now() / 1000;
        
        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineWidth = 3;
        
        // Draw X
        const size = 15;
        const offset = Math.sin(time * 10) * 2;
        
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - size + offset, centerY - size);
        this.ctx.lineTo(centerX + size + offset, centerY + size);
        this.ctx.moveTo(centerX + size + offset, centerY - size);
        this.ctx.lineTo(centerX - size + offset, centerY + size);
        this.ctx.stroke();
    }
    
    drawIdle() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const time = Date.now() / 1000;
        
        // Draw subtle breathing circle
        const radius = 10 + Math.sin(time) * 2;
        
        this.ctx.fillStyle = this.currentColor;
        this.ctx.globalAlpha = 0.3;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.globalAlpha = 0.6;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius * 0.6, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.globalAlpha = 1;
    }
}

// Export for use in main app
window.UserFeedbackManager = UserFeedbackManager;