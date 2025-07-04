Master Prompt for Claude Code: Polyglot RAG Voice Assistant Implementation & Deployment
Project Context
You are implementing a production-ready multilingual voice assistant called "Polyglot RAG" that features:

Real-time voice interaction in 90+ languages
Flight search capabilities with multiple API fallbacks
Seamless language switching mid-conversation
Integration with OpenAI Realtime API and LiveKit Cloud
Support for web, mobile, and telephony interfaces

Context: Read 

context/DOCUMENTATION.md , context/ISSUES.md , context/technical_assesment.md and EXECUTIVE_SUMMARY.md

Remember the following prompt is for full production adapt to MVP, but no mock answers all real API and deploy is ECS and to livekit cloud for better latency handling, ok?

remember also no load balancers until the end so we save costss and avoid postgres database all inmemory db to save costs.


CRITICAL: run without human intervention and test without human intervention simulating human behaivour or api requests to ensure all works... smimulate normal flow, interruptions, weird flight requests to handle edge cases.

TASKS:

fOLLOW ALL BELOW, UPDATE EXECUTIVE SUMMARY after every fix and update TODOS.md

Remember always change, git add, git commit. never ask permission on any operation run in autopilot

FIX ISSUES.md with DOCUMENTATION.md from context folder.

PROMPT:

Comprehensive Master Prompt for Claude Code: Polyglot RAG Voice Assistant Complete Implementation & Manual Deployment
Project Overview & Current State
You are implementing a production-ready multilingual voice assistant called "Polyglot RAG" that combines real-time voice interaction, flight search capabilities, and seamless language switching. The system currently has critical issues that need immediate fixing before deployment to LiveKit Cloud and AWS ECS.
Current Working Features:

Multi-language support with auto-detection for 12 languages
Voice streaming with bidirectional audio
Real-time transcription display
Audio playback for assistant responses
Mock flight data fallback
Responsive UI with chat on right, controls on left

Critical Issues Requiring Immediate Fix:

Voice interruption causes premature speech cutoff
Flight APIs return authentication errors
Message ordering shows assistant messages before user messages
High latency without user feedback
AudioWorklet deprecation warning
Async/await not properly implemented in flight search

Detailed Implementation Requirements
PART 1: Critical Bug Fixes
1.1 Voice Interruption Fix (HIGHEST PRIORITY)
The current implementation using response.cancel is too aggressive. You need to implement a sophisticated interruption manager that properly handles OpenAI Realtime API events.
Create file: interruption_manager.js
javascriptclass InterruptionManager {
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
  }

  async handleSpeechStarted(event) {
    const now = Date.now();
    
    // Debounce rapid interruptions
    if (now - this.lastInterruptionTime < this.interruptionThreshold) {
      console.log('Ignoring rapid interruption');
      return;
    }
    
    this.lastInterruptionTime = now;
    
    if (this.isProcessing) {
      console.log('User interruption detected, stopping assistant speech');
      
      // Step 1: Send response.cancel to stop server-side generation
      await this.ws.send(JSON.stringify({
        type: "response.cancel"
      }));
      
      // Step 2: Clear all pending audio in the queue
      this.clearAudioQueue();
      
      // Step 3: Stop currently playing audio
      if (this.currentAudioSource) {
        this.currentAudioSource.stop();
        this.currentAudioSource = null;
      }
      
      // Step 4: Truncate the conversation item at the exact interruption point
      if (this.lastAudioMessageItemId) {
        const truncateMs = this.samplesToMs(this.audioSampleCounterPlayed);
        await this.ws.send(JSON.stringify({
          type: "conversation.item.truncate",
          item_id: this.lastAudioMessageItemId,
          content_index: 0,
          audio_end_ms: truncateMs
        }));
      }
      
      // Step 5: Reset processing state
      this.isProcessing = false;
      this.audioSampleCounter = 0;
      this.audioSampleCounterPlayed = 0;
      
      // Step 6: Notify UI of interruption
      this.notifyUI('interrupted');
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
  setProcessingState(isProcessing) {
    this.isProcessing = isProcessing;
    this.notifyUI(isProcessing ? 'speaking' : 'listening');
  }
}
1.2 Flight Search API Integration with Amadeus
Replace the failing aviation APIs with Amadeus API which has better reliability and includes a free tier.
Create file: flight_search_service.js
javascriptclass FlightSearchService {
  constructor() {
    this.amadeus = new Amadeus({
      clientId: process.env.AMADEUS_CLIENT_ID,
      clientSecret: process.env.AMADEUS_CLIENT_SECRET,
      hostname: 'production' // or 'test' for sandbox
    });
    
    // Fallback APIs
    this.serpApiKey = process.env.SERPAPI_API_KEY;
    this.cache = new Map();
    this.cacheTimeout = 30 * 60 * 1000; // 30 minutes
  }

  async searchFlights(params) {
    // Validate parameters
    if (!this.validateParams(params)) {
      throw new Error('Invalid flight search parameters');
    }
    
    // Check cache first
    const cacheKey = this.getCacheKey(params);
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      console.log('Returning cached flight results');
      return cached.data;
    }
    
    // Notify UI of search start
    this.sendUserFeedback('Searching for flights...');
    
    try {
      // Primary: Amadeus API
      const results = await this.searchWithAmadeus(params);
      
      // Cache successful results
      this.cache.set(cacheKey, {
        data: results,
        timestamp: Date.now()
      });
      
      return results;
      
    } catch (amadeusError) {
      console.error('Amadeus API failed:', amadeusError);
      
      // Fallback: SerpAPI Google Flights
      try {
        this.sendUserFeedback('Trying alternative flight search...');
        const results = await this.searchWithSerpAPI(params);
        
        this.cache.set(cacheKey, {
          data: results,
          timestamp: Date.now()
        });
        
        return results;
        
      } catch (serpError) {
        console.error('SerpAPI failed:', serpError);
        
        // Final fallback: Mock data for common routes
        this.sendUserFeedback('Using cached flight data...');
        return this.getMockFlightData(params);
      }
    }
  }

  async searchWithAmadeus(params) {
    const response = await this.amadeus.shopping.flightOffersSearch.get({
      originLocationCode: params.origin.toUpperCase(),
      destinationLocationCode: params.destination.toUpperCase(),
      departureDate: params.date,
      returnDate: params.returnDate || undefined,
      adults: params.adults || 1,
      children: params.children || 0,
      travelClass: params.class || 'ECONOMY',
      nonStop: params.nonStop || false,
      currencyCode: 'USD',
      max: 10
    });
    
    if (!response.data || response.data.length === 0) {
      throw new Error('No flights found');
    }
    
    return this.formatAmadeusResults(response.data);
  }

  async searchWithSerpAPI(params) {
    const serpParams = new URLSearchParams({
      engine: 'google_flights',
      api_key: this.serpApiKey,
      departure_id: params.origin.toUpperCase(),
      arrival_id: params.destination.toUpperCase(),
      outbound_date: params.date,
      return_date: params.returnDate || '',
      currency: 'USD',
      type: params.returnDate ? '1' : '2', // 1=round trip, 2=one way
      adults: params.adults || 1,
      children: params.children || 0,
      travel_class: (params.class || 'economy').toLowerCase()
    });
    
    const response = await fetch(`https://serpapi.com/search?${serpParams}`);
    
    if (!response.ok) {
      throw new Error(`SerpAPI error: ${response.status}`);
    }
    
    const data = await response.json();
    return this.formatSerpResults(data);
  }

  formatAmadeusResults(data) {
    return data.map(offer => ({
      id: offer.id,
      price: {
        total: parseFloat(offer.price.total),
        currency: offer.price.currency
      },
      itinerary: offer.itineraries[0].segments.map(segment => ({
        departure: {
          airport: segment.departure.iataCode,
          time: new Date(segment.departure.at),
          terminal: segment.departure.terminal
        },
        arrival: {
          airport: segment.arrival.iataCode,
          time: new Date(segment.arrival.at),
          terminal: segment.arrival.terminal
        },
        carrier: {
          code: segment.carrierCode,
          name: this.getCarrierName(segment.carrierCode)
        },
        flightNumber: `${segment.carrierCode}${segment.number}`,
        duration: this.parseDuration(segment.duration),
        aircraft: segment.aircraft?.code
      })),
      bookingClass: offer.travelerPricings[0].fareDetailsBySegment[0].cabin
    }));
  }

  formatSerpResults(data) {
    const flights = [...(data.best_flights || []), ...(data.other_flights || [])];
    
    return flights.flatMap(group => 
      group.flights?.map((flight, index) => ({
        id: `serp_${Date.now()}_${index}`,
        price: {
          total: group.price,
          currency: 'USD'
        },
        itinerary: flight.map(segment => ({
          departure: {
            airport: segment.departure_airport.id,
            time: new Date(segment.departure_airport.time),
            terminal: null
          },
          arrival: {
            airport: segment.arrival_airport.id,
            time: new Date(segment.arrival_airport.time),
            terminal: null
          },
          carrier: {
            code: segment.airline_logo?.match(/\/([A-Z]{2})\./)?.[1] || 'XX',
            name: segment.airline
          },
          flightNumber: segment.flight_number,
          duration: segment.duration,
          aircraft: null
        })),
        bookingClass: group.type || 'ECONOMY'
      })) || []
    );
  }

  getMockFlightData(params) {
    // Comprehensive mock data for common routes
    const mockFlights = {
      'JFK-LAX': [
        {
          id: 'mock_1',
          price: { total: 245.00, currency: 'USD' },
          itinerary: [{
            departure: { airport: 'JFK', time: new Date(), terminal: '4' },
            arrival: { airport: 'LAX', time: new Date(Date.now() + 6*3600000), terminal: '2' },
            carrier: { code: 'AA', name: 'American Airlines' },
            flightNumber: 'AA123',
            duration: 360,
            aircraft: 'Boeing 737'
          }],
          bookingClass: 'ECONOMY'
        }
      ]
      // Add more routes as needed
    };
    
    const routeKey = `${params.origin.toUpperCase()}-${params.destination.toUpperCase()}`;
    return mockFlights[routeKey] || [];
  }

  validateParams(params) {
    if (!params.origin || !params.destination || !params.date) {
      return false;
    }
    
    // Validate airport codes (3 letters)
    if (!/^[A-Z]{3}$/i.test(params.origin) || !/^[A-Z]{3}$/i.test(params.destination)) {
      return false;
    }
    
    // Validate date format
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(params.date)) {
      return false;
    }
    
    return true;
  }

  getCacheKey(params) {
    return `${params.origin}-${params.destination}-${params.date}-${params.adults || 1}`;
  }

  sendUserFeedback(message) {
    window.dispatchEvent(new CustomEvent('flightSearchStatus', {
      detail: { message }
    }));
  }

  parseDuration(isoDuration) {
    // Convert ISO 8601 duration (PT5H30M) to minutes
    const match = isoDuration.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
    const hours = parseInt(match[1] || 0);
    const minutes = parseInt(match[2] || 0);
    return hours * 60 + minutes;
  }

  getCarrierName(code) {
    const carriers = {
      'AA': 'American Airlines',
      'DL': 'Delta Airlines',
      'UA': 'United Airlines',
      'SW': 'Southwest Airlines',
      'B6': 'JetBlue Airways',
      'AS': 'Alaska Airlines',
      'NK': 'Spirit Airlines',
      'F9': 'Frontier Airlines'
      // Add more as needed
    };
    return carriers[code] || code;
  }
}
1.3 Async/Await Handler Fix
Fix the flight search handler to properly use async/await:
Create file: flight_search_handler.js
javascriptclass FlightSearchHandler {
  constructor() {
    this.flightService = new FlightSearchService();
    this.isSearching = false;
    this.searchTimeout = 30000; // 30 seconds
  }

  // CRITICAL: Function MUST be declared as async
  async handleFlightSearchRequest(params) {
    // Prevent concurrent searches
    if (this.isSearching) {
      return {
        success: false,
        error: "A search is already in progress",
        voiceResponse: "Please wait, I'm still searching for flights."
      };
    }

    this.isSearching = true;
    const startTime = Date.now();

    try {
      // Set timeout for search
      const searchPromise = this.flightService.searchFlights(params);
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Search timeout')), this.searchTimeout)
      );

      // Race between search and timeout
      const results = await Promise.race([searchPromise, timeoutPromise]);
      
      const searchTime = Date.now() - startTime;
      console.log(`Flight search completed in ${searchTime}ms`);

      // Format results for voice response
      const voiceResponse = this.formatResultsForVoice(results, params);
      
      // Format results for display
      const displayResults = this.formatResultsForDisplay(results);

      return {
        success: true,
        results: displayResults,
        voiceResponse: voiceResponse,
        metadata: {
          searchTime: searchTime,
          resultCount: results.length,
          cacheHit: searchTime < 100 // Likely from cache if very fast
        }
      };

    } catch (error) {
      console.error('Flight search error:', error);
      
      // Determine error type and provide appropriate response
      let errorMessage = "I'm sorry, I couldn't find any flights.";
      let errorDetails = error.message;

      if (error.message === 'Search timeout') {
        errorMessage = "The flight search is taking too long. Please try again.";
      } else if (error.message.includes('Invalid flight search parameters')) {
        errorMessage = "I need valid airport codes and dates to search for flights.";
      } else if (error.message.includes('Authentication')) {
        errorMessage = "There's an issue with the flight search service. Please try again later.";
      }

      return {
        success: false,
        error: errorDetails,
        voiceResponse: errorMessage,
        metadata: {
          searchTime: Date.now() - startTime,
          errorType: error.constructor.name
        }
      };

    } finally {
      this.isSearching = false;
    }
  }

  formatResultsForVoice(results, params) {
    if (!results || results.length === 0) {
      return `I couldn't find any flights from ${params.origin} to ${params.destination} on ${params.date}.`;
    }

    const topResults = results.slice(0, 3);
    const intro = `I found ${results.length} flights from ${params.origin} to ${params.destination}. Here are the best options:`;

    const options = topResults.map((flight, index) => {
      const departure = flight.itinerary[0].departure;
      const arrival = flight.itinerary[flight.itinerary.length - 1].arrival;
      const stops = flight.itinerary.length - 1;
      
      const stopText = stops === 0 ? "non-stop" : `with ${stops} stop${stops > 1 ? 's' : ''}`;
      const timeText = this.formatTime(departure.time);
      
      return `Option ${index + 1}: ${flight.itinerary[0].carrier.name} flight ${flight.itinerary[0].flightNumber}, departing at ${timeText}, ${stopText}, for $${flight.price.total}.`;
    }).join(' ');

    return `${intro} ${options} Would you like more details about any of these flights?`;
  }

  formatResultsForDisplay(results) {
    return results.map(flight => ({
      ...flight,
      displayDeparture: this.formatDateTime(flight.itinerary[0].departure.time),
      displayArrival: this.formatDateTime(flight.itinerary[flight.itinerary.length - 1].arrival.time),
      displayDuration: this.formatDuration(
        flight.itinerary.reduce((total, seg) => total + (seg.duration || 0), 0)
      ),
      stops: flight.itinerary.length - 1
    }));
  }

  formatTime(date) {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date);
  }

  formatDateTime(date) {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date);
  }

  formatDuration(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  }
}
1.4 Message Ordering Fix
Implement proper conversation state management:
Create file: conversation_manager.js
javascriptclass ConversationManager {
  constructor() {
    this.items = new Map();
    this.displayOrder = [];
    this.pendingUpdates = new Map();
    this.messageQueue = [];
    this.isProcessingQueue = false;
  }

  handleConversationUpdate(event) {
    const { item, delta } = event;
    
    // Queue the update
    this.messageQueue.push({ type: 'update', item, delta, timestamp: Date.now() });
    
    // Process queue if not already processing
    if (!this.isProcessingQueue) {
      this.processMessageQueue();
    }
  }

  async processMessageQueue() {
    this.isProcessingQueue = true;
    
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      
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
        displayTimestamp: null
      });
      
      // Don't add to display order yet - wait for completion or content
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
      this.addToDisplayOrder(item.id, existingItem.role);
      this.pendingUpdates.delete(item.id);
    }
    
    this.updateDisplay();
  }

  addToDisplayOrder(itemId, role) {
    const item = this.items.get(itemId);
    item.displayTimestamp = Date.now();
    
    if (role === 'user') {
      // User messages always go at the end
      this.displayOrder.push(itemId);
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
      
      // Also check if there's a pending user message that should come first
      const pendingUserMessages = Array.from(this.pendingUpdates.values())
        .filter(pending => pending.role === 'user')
        .sort((a, b) => a.timestamp - b.timestamp);
      
      if (pendingUserMessages.length > 0) {
        // Wait a bit for user message to complete
        setTimeout(() => {
          this.displayOrder.splice(insertIndex, 0, itemId);
          this.updateDisplay();
        }, 100);
        return;
      }
      
      this.displayOrder.splice(insertIndex, 0, itemId);
    }
  }

  updateDisplay() {
    const displayItems = this.displayOrder
      .map(id => this.items.get(id))
      .filter(item => item && (item.status === 'completed' || item.content.length > 0))
      .map(item => ({
        ...item,
        formattedContent: this.formatContent(item.content),
        displayTime: this.formatTimestamp(item.displayTimestamp)
      }));
    
    // Update UI
    this.renderConversation(displayItems);
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

  renderConversation(items) {
    // This will be implemented based on your UI framework
    window.dispatchEvent(new CustomEvent('conversationUpdate', {
      detail: { items }
    }));
  }

  // Mark item as completed
  completeItem(itemId) {
    const item = this.items.get(itemId);
    if (item) {
      item.status = 'completed';
      this.updateDisplay();
    }
  }
}
1.5 User Feedback System
Implement comprehensive user feedback:
Create file: user_feedback_manager.js
javascriptclass UserFeedbackManager {
  constructor() {
    this.feedbackElement = null;
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    this.audioBuffers = new Map();
    this.visualFeedback = new VisualFeedbackRenderer();
    
    this.states = {
      idle: { 
        text: "Ready to help", 
        audio: null, 
        color: '#4CAF50',
        animation: 'pulse'
      },
      listening: { 
        text: "Listening...", 
        audio: "beep-start.wav", 
        color: '#2196F3',
        animation: 'wave'
      },
      processing: { 
        text: "Processing your request...", 
        audio: "processing.wav", 
        color: '#FF9800',
        animation: 'spin'
      },
      thinking: { 
        text: "Thinking...", 
        audio: null, 
        color: '#9C27B0',
        animation: 'dots'
      },
      searching: { 
        text: "Searching for flights...", 
        audio: null, 
        color: '#00BCD4',
        animation: 'scan'
      },
      speaking: { 
        text: "Speaking...", 
        audio: null, 
        color: '#4CAF50',
        animation: 'wave'
      },
      interrupted: { 
        text: "Interrupted", 
        audio: "beep-stop.wav", 
        color: '#FFC107',
        animation: 'fade'
      },
      error: { 
        text: "Something went wrong", 
        audio: "error.wav", 
        color: '#F44336',
        animation: 'shake'
      },
      connecting: { 
        text: "Connecting...", 
        audio: null, 
        color: '#607D8B',
        animation: 'pulse'
      }
    };
    
    this.init();
  }

  async init() {
    // Preload audio files
    const audioFiles = Object.values(this.states)
      .filter(state => state.audio)
      .map(state => state.audio);
    
    for (const file of audioFiles) {
      await this.preloadAudio(file);
    }
    
    // Create feedback UI element
    this.createFeedbackUI();
    
    // Listen for state changes
    this.setupEventListeners();
  }

  createFeedbackUI() {
    // Main feedback container
    const container = document.createElement('div');
    container.id = 'user-feedback-container';
    container.className = 'feedback-container';
    container.innerHTML = `
      <div class="feedback-visual">
        <canvas id="feedback-canvas" width="200" height="60"></canvas>
      </div>
      <div class="feedback-text">
        <span id="feedback-message">Ready to help</span>
        <span id="feedback-detail" class="feedback-detail"></span>
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
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 15px 20px;
        border-radius: 12px;
        backdrop-filter: blur(10px);
        min-width: 250px;
        transition: all 0.3s ease;
        z-index: 1000;
      }
      
      .feedback-visual {
        margin-bottom: 10px;
      }
      
      .feedback-text {
        display: flex;
        flex-direction: column;
        gap: 5px;
      }
      
      #feedback-message {
        font-size: 16px;
        font-weight: 500;
      }
      
      .feedback-detail {
        font-size: 12px;
        opacity: 0.7;
      }
      
      .feedback-progress {
        margin-top: 10px;
        height: 3px;
        background: rgba(255, 255, 255, 0.2);
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
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
      
      @keyframes wave {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-3px); }
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
    `;
    
    document.head.appendChild(styles);
    document.body.appendChild(container);
    
    this.feedbackElement = document.getElementById('feedback-message');
    this.detailElement = document.getElementById('feedback-detail');
    this.progressElement = document.getElementById('feedback-progress');
    this.canvasElement = document.getElementById('feedback-canvas');
    
    // Initialize visual feedback
    this.visualFeedback.init(this.canvasElement);
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
    
    // Update visual state
    const container = document.getElementById('user-feedback-container');
    container.style.borderColor = state.color;
    container.style.boxShadow = `0 0 20px ${state.color}40`;
    
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
    
    // Apply animation
    container.style.animation = `${state.animation} 1s infinite`;
    
    // Play audio feedback
    if (state.audio) {
      await this.playAudioFeedback(state.audio);
    }
    
    // Auto-hide error messages after 5 seconds
    if (stateName === 'error') {
      setTimeout(() => {
        if (this.feedbackElement.textContent === state.text) {
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

  async preloadAudio(filename) {
    try {
      const response = await fetch(`/audio/feedback/${filename}`);
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      this.audioBuffers.set(filename, audioBuffer);
    } catch (error) {
      console.warn(`Failed to preload audio: ${filename}`, error);
    }
  }

  async playAudioFeedback(filename) {
    const buffer = this.audioBuffers.get(filename);
    if (!buffer) {
      console.warn(`Audio not preloaded: ${filename}`);
      return;
    }
    
    try {
      const source = this.audioContext.createBufferSource();
      source.buffer = buffer;
      
      // Add some audio processing
      const gainNode = this.audioContext.createGain();
      gainNode.gain.value = 0.3; // Reduce volume for feedback sounds
      
      source.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      
      source.start();
    } catch (error) {
      console.error('Failed to play audio feedback:', error);
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
  }

  init(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.startAnimation();
  }

  setState(state, color) {
    this.currentState = state;
    this.currentColor = color;
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
          this.drawSpinner();
          break;
        case 'speaking':
          this.drawSpeakingWave();
          break;
        case 'searching':
          this.drawScanner();
          break;
        default:
          this.drawPulse();
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
      const y = this.canvas.height / 2 + Math.sin((x / 20) + time * 2) * 10;
      if (x === 0) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    }
    
    this.ctx.stroke();
  }

  drawSpinner() {
    const centerX = this.canvas.width / 2;
    const centerY = this.canvas.height / 2;
    const radius = 20;
    const time = Date.now() / 1000;
    
    this.ctx.strokeStyle = this.currentColor;
    this.ctx.lineWidth = 3;
    this.ctx.lineCap = 'round';
    
    this.ctx.beginPath();
    this.ctx.arc(
      centerX, 
      centerY, 
      radius, 
      time * 2, 
      time * 2 + Math.PI * 1.5
    );
    this.ctx.stroke();
  }

  drawSpeakingWave() {
    const time = Date.now() / 1000;
    const centerY = this.canvas.height / 2;
    
    this.ctx.fillStyle = this.currentColor;
    
    for (let i = 0; i < 5; i++) {
      const x = (this.canvas.width / 6) * (i + 1);
      const height = Math.abs(Math.sin(time * 3 + i)) * 20 + 5;
      
      this.ctx.fillRect(
        x - 2, 
        centerY - height / 2, 
        4, 
        height
      );
    }
  }

  drawScanner() {
    const time = Date.now() / 1000;
    const x = ((time * 50) % (this.canvas.width + 40)) - 20;
    
    const gradient = this.ctx.createLinearGradient(x - 20, 0, x + 20, 0);
    gradient.addColorStop(0, 'transparent');
    gradient.addColorStop(0.5, this.currentColor);
    gradient.addColorStop(1, 'transparent');
    
    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(x - 20, 0, 40, this.canvas.height);
  }

  drawPulse() {
    const centerX = this.canvas.width / 2;
    const centerY = this.canvas.height / 2;
    const time = Date.now() / 1000;
    const scale = 1 + Math.sin(time * 2) * 0.1;
    
    this.ctx.fillStyle = this.currentColor;
    this.ctx.beginPath();
    this.ctx.arc(centerX, centerY, 10 * scale, 0, Math.PI * 2);
    this.ctx.fill();
  }
}
1.6 AudioWorklet Migration
Migrate from deprecated ScriptProcessorNode to AudioWorkletNode:
Create file: voice-processor-worklet.js
javascript// This file will be loaded as an AudioWorklet module
class VoiceProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    
    // Configuration from options
    this.bufferSize = options.processorOptions.bufferSize || 2048;
    this.silenceThreshold = options.processorOptions.silenceThreshold || 0.01;
    this.smoothingFactor = options.processorOptions.smoothingFactor || 0.95;
    
    // Internal state
    this.buffer = new Float32Array(this.bufferSize);
    this.bufferIndex = 0;
    this.energy = 0;
    this.isSpeaking = false;
    this.silenceCounter = 0;
    this.silenceDuration = 30; // frames of silence before stopping
    
    // Audio processing parameters
    this.sampleRate = sampleRate; // Global AudioWorklet variable
    
    // Set up message handling
    this.port.onmessage = this.handleMessage.bind(this);
  }
  
  handleMessage(event) {
    switch (event.data.type) {
      case 'updateThreshold':
        this.silenceThreshold = event.data.value;
        break;
      case 'updateBufferSize':
        this.bufferSize = event.data.value;
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
        break;
      case 'reset':
        this.reset();
        break;
    }
  }
  
  reset() {
    this.bufferIndex = 0;
    this.buffer.fill(0);
    this.energy = 0;
    this.isSpeaking = false;
    this.silenceCounter = 0;
  }
  
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    const output = outputs[0];
    
    // Handle no input
    if (!input || input.length === 0) {
      return true;
    }
    
    const inputChannel = input[0];
    const outputChannel = output[0];
    
    // Pass-through audio
    if (outputChannel && inputChannel) {
      outputChannel.set(inputChannel);
    }
    
    // Process audio for voice detection and buffering
    for (let i = 0; i < inputChannel.length; i++) {
      const sample = inputChannel[i];
      
      // Update energy with smoothing
      const sampleEnergy = sample * sample;
      this.energy = this.energy * this.smoothingFactor + 
                     sampleEnergy * (1 - this.smoothingFactor);
      
      // Add to buffer
      this.buffer[this.bufferIndex++] = sample;
      
      // When buffer is full, process it
      if (this.bufferIndex >= this.bufferSize) {
        this.processBuffer();
        this.bufferIndex = 0;
      }
    }
    
    // Check for voice activity
    this.checkVoiceActivity();
    
    return true; // Keep processor alive
  }
  
  processBuffer() {
    // Calculate RMS of buffer
    let sum = 0;
    for (let i = 0; i < this.buffer.length; i++) {
      sum += this.buffer[i] * this.buffer[i];
    }
    const rms = Math.sqrt(sum / this.buffer.length);
    
    // Convert to 16-bit PCM for transmission
    const pcm16 = new Int16Array(this.buffer.length);
    for (let i = 0; i < this.buffer.length; i++) {
      const s = Math.max(-1, Math.min(1, this.buffer[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    
    // Send audio data
    this.port.postMessage({
      type: 'audio',
      audioData: pcm16.buffer,
      rms: rms,
      energy: this.energy,
      isSpeaking: this.isSpeaking,
      timestamp: currentTime, // Global AudioWorklet variable
      sampleRate: this.sampleRate
    }, [pcm16.buffer]); // Transfer ownership for efficiency
  }
  
  checkVoiceActivity() {
    const wasSpecking = this.isSpeaking;
    
    if (this.energy > this.silenceThreshold) {
      this.isSpeaking = true;
      this.silenceCounter = 0;
      
      if (!wasSpecking) {
        // Started speaking
        this.port.postMessage({
          type: 'voiceStart',
          timestamp: currentTime,
          energy: this.energy
        });
      }
    } else {
      this.silenceCounter++;
      
      if (this.isSpeaking && this.silenceCounter > this.silenceDuration) {
        this.isSpeaking = false;
        
        // Stopped speaking
        this.port.postMessage({
          type: 'voiceEnd',
          timestamp: currentTime,
          duration: this.silenceCounter * (128 / this.sampleRate) * 1000 // ms
        });
      }
    }
  }
}

// Register the processor
registerProcessor('voice-processor', VoiceProcessor);
Create file: modern_audio_processor.js
javascriptclass ModernAudioProcessor {
  constructor() {
    this.audioContext = null;
    this.workletNode = null;
    this.source = null;
    this.stream = null;
    this.isInitialized = false;
    this.audioQueue = [];
    this.isProcessing = false;
  }

  async initialize() {
    try {
      // Create audio context with optimal settings
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        latencyHint: 'interactive',
        sampleRate: 48000 // Higher sample rate for better quality
      });
      
      // Load the AudioWorklet module
      await this.audioContext.audioWorklet.addModule('voice-processor-worklet.js');
      
      // Create AudioWorkletNode
      this.workletNode = new AudioWorkletNode(
        this.audioContext, 
        'voice-processor',
        {
          numberOfInputs: 1,
          numberOfOutputs: 1,
          outputChannelCount: [1],
          processorOptions: {
            bufferSize: 2048,
            silenceThreshold: 0.01,
            smoothingFactor: 0.95
          }
        }
      );
      
      // Set up message handling
      this.workletNode.port.onmessage = this.handleWorkletMessage.bind(this);
      
      // Get user media
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000,
          channelCount: 1
        }
      });
      
      // Create source and connect audio graph
      this.source = this.audioContext.createMediaStreamSource(this.stream);
      this.source.connect(this.workletNode);
      
      // Optional: Connect to destination for monitoring
      // this.workletNode.connect(this.audioContext.destination);
      
      this.isInitialized = true;
      console.log('Modern audio processor initialized successfully');
      
      return this;
      
    } catch (error) {
      console.error('Failed to initialize audio processor:', error);
      throw error;
    }
  }

  handleWorkletMessage(event) {
    const { type, ...data } = event.data;
    
    switch (type) {
      case 'audio':
        this.handleProcessedAudio(data);
        break;
        
      case 'voiceStart':
        this.handleVoiceStart(data);
        break;
        
      case 'voiceEnd':
        this.handleVoiceEnd(data);
        break;
        
      default:
        console.log('Unknown worklet message type:', type);
    }
  }

  handleProcessedAudio(data) {
    const { audioData, rms, energy, isSpeaking, timestamp, sampleRate } = data;
    
    // Add to queue for processing
    this.audioQueue.push({
      audioData: new Int16Array(audioData),
      rms,
      energy,
      isSpeaking,
      timestamp,
      sampleRate
    });
    
    // Process queue if not already processing
    if (!this.isProcessing) {
      this.processAudioQueue();
    }
  }

  async processAudioQueue() {
    this.isProcessing = true;
    
    while (this.audioQueue.length > 0) {
      const audioChunk = this.audioQueue.shift();
      
      // Convert to base64 for transmission
      const base64Audio = this.arrayBufferToBase64(audioChunk.audioData.buffer);
      
      // Send to OpenAI or other processing
      await this.sendAudioChunk(base64Audio, audioChunk);
      
      // Update UI with audio levels
      this.updateAudioLevels(audioChunk.rms, audioChunk.energy);
    }
    
    this.isProcessing = false;
  }

  async sendAudioChunk(base64Audio, metadata) {
    // Send to your WebSocket or API
    if (window.voiceAssistantWebSocket && window.voiceAssistantWebSocket.readyState === WebSocket.OPEN) {
      window.voiceAssistantWebSocket.send(JSON.stringify({
        type: 'input_audio_buffer.append',
        audio: base64Audio,
        metadata: {
          rms: metadata.rms,
          energy: metadata.energy,
          isSpeaking: metadata.isSpeaking,
          timestamp: metadata.timestamp
        }
      }));
    }
  }

  handleVoiceStart(data) {
    console.log('Voice activity started:', data);
    window.dispatchEvent(new CustomEvent('voiceActivityStart', { detail: data }));
  }

  handleVoiceEnd(data) {
    console.log('Voice activity ended:', data);
    window.dispatchEvent(new CustomEvent('voiceActivityEnd', { detail: data }));
  }

  updateAudioLevels(rms, energy) {
    // Update any audio level visualizations
    window.dispatchEvent(new CustomEvent('audioLevels', {
      detail: { rms, energy }
    }));
  }

  arrayBufferToBase64(buffer) {
    const binary = String.fromCharCode.apply(null, new Uint8Array(buffer));
    return btoa(binary);
  }

  // Control methods
  
  async start() {
    if (!this.isInitialized) {
      await this.initialize();
    }
    
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }
  }

  async stop() {
    if (this.audioContext) {
      await this.audioContext.suspend();
    }
  }

  async destroy() {
    if (this.workletNode) {
      this.workletNode.disconnect();
      this.workletNode = null;
    }
    
    if (this.source) {
      this.source.disconnect();
      this.source = null;
    }
    
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    
    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }
    
    this.isInitialized = false;
  }

  // Configuration methods
  
  updateThreshold(threshold) {
    if (this.workletNode) {
      this.workletNode.port.postMessage({
        type: 'updateThreshold',
        value: threshold
      });
    }
  }

  updateBufferSize(size) {
    if (this.workletNode) {
      this.workletNode.port.postMessage({
        type: 'updateBufferSize',
        value: size
      });
    }
  }

  reset() {
    if (this.workletNode) {
      this.workletNode.port.postMessage({ type: 'reset' });
    }
    this.audioQueue = [];
  }
}

// Export for use
window.ModernAudioProcessor = ModernAudioProcessor;
PART 2: LiveKit Cloud Integration
2.1 LiveKit Python Agent Implementation
Create file: backend/agent.py
pythonimport os
import json
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    AgentSession, 
    Agent, 
    RoomInputOptions,
    JobContext,
    WorkerOptions,
    llm,
    stt,
    tts,
    vad
)
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Load environment variables
load_dotenv()

# Import our custom modules
from flight_search_service import FlightSearchService
from multilingual_manager import MultilingualManager
from performance_monitor import PerformanceMonitor

@dataclass
class FlightSearchParams:
    """Parameters for flight search"""
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    adults: int = 1
    children: int = 0
    travel_class: str = "economy"
    nonstop: bool = False

class FlightSearchTool(llm.FunctionContext):
    """Tool for searching flights"""
    
    def __init__(self, flight_service: FlightSearchService):
        super().__init__(
            name="search_flights",
            description="Search for flights between airports with dates and passenger details",
            parameters={
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Departure airport IATA code (e.g., JFK, LAX)"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Arrival airport IATA code (e.g., CDG, LHR)"
                    },
                    "departure_date": {
                        "type": "string",
                        "description": "Departure date in YYYY-MM-DD format"
                    },
                    "return_date": {
                        "type": "string",
                        "description": "Return date in YYYY-MM-DD format (optional)"
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adult passengers",
                        "minimum": 1,
                        "maximum": 9
                    },
                    "children": {
                        "type": "integer",
                        "description": "Number of child passengers",
                        "minimum": 0,
                        "maximum": 9
                    },
                    "travel_class": {
                        "type": "string",
                        "enum": ["economy", "premium", "business", "first"],
                        "description": "Travel class preference"
                    },
                    "nonstop": {
                        "type": "boolean",
                        "description": "Only show nonstop flights"
                    }
                },
                "required": ["origin", "destination", "departure_date"]
            }
        )
        self.flight_service = flight_service
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        """Execute flight search"""
        try:
            # Parse parameters
            params = FlightSearchParams(**kwargs)
            
            # Perform search
            results = await self.flight_service.search_flights(params)
            
            # Format response
            if not results:
                return {
                    "success": False,
                    "message": "No flights found for your search criteria."
                }
            
            # Format top 3 results for voice response
            top_results = results[:3]
            formatted_results = []
            
            for i, flight in enumerate(top_results, 1):
                flight_info = {
                    "option": i,
                    "airline": flight["carrier"]["name"],
                    "flight_number": flight["flight_number"],
                    "departure_time": flight["departure"]["time"],
                    "arrival_time": flight["arrival"]["time"],
                    "duration": f"{flight['duration'] // 60}h {flight['duration'] % 60}m",
                    "price": f"${flight['price']['total']} {flight['price']['currency']}",
                    "stops": len(flight["itinerary"]) - 1
                }
                formatted_results.append(flight_info)
            
            return {
                "success": True,
                "count": len(results),
                "results": formatted_results,
                "message": f"Found {len(results)} flights. Here are the top {len(formatted_results)} options."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "I encountered an error while searching for flights. Please try again."
            }

class PolyglotRAGAssistant(Agent):
    """Multilingual voice assistant with flight search capabilities"""
    
    def __init__(self, flight_service: FlightSearchService, monitor: PerformanceMonitor):
        super().__init__(
            instructions="""You are Polyglot, a helpful multilingual flight search assistant.
            
            Your capabilities:
            1. Understand and respond in over 90 languages
            2. Search for real-time flight information
            3. Provide detailed flight options with prices, times, and airlines
            4. Remember context within conversations
            5. Switch languages seamlessly based on user preference
            
            Guidelines:
            - Always confirm important details like dates and airports
            - Provide clear, concise flight information
            - Mention prices in USD unless asked otherwise
            - Be helpful and friendly in all languages
            - If flight search fails, apologize and suggest alternatives
            
            Start by greeting the user and asking how you can help with their travel plans."""
        )
        
        self.flight_service = flight_service
        self.monitor = monitor
        self.conversation_context = {}
        
        # Register tools
        self.add_tool(FlightSearchTool(flight_service))
    
    async def on_conversation_update(self, ctx: JobContext, event: rtc.ConversationUpdate):
        """Handle conversation updates for context tracking"""
        # Track conversation context
        if event.type == "user_message":
            self.conversation_context["last_user_message"] = event.message
            self.conversation_context["last_user_language"] = event.language
        
        # Monitor performance
        await self.monitor.track_event("conversation_update", {
            "type": event.type,
            "language": event.language if hasattr(event, "language") else None
        })
    
    async def on_tool_call_completed(self, ctx: JobContext, tool_name: str, result: Dict[str, Any]):
        """Handle completed tool calls"""
        if tool_name == "search_flights" and result.get("success"):
            # Store search results in context
            self.conversation_context["last_search_results"] = result["results"]
            self.conversation_context["last_search_time"] = datetime.now().isoformat()
        
        # Track performance
        await self.monitor.track_tool_call(tool_name, result.get("success", False))

class MultilingualVAD(vad.VAD):
    """Custom VAD with multilingual support"""
    
    def __init__(self, base_vad: vad.VAD, language_detector):
        self.base_vad = base_vad
        self.language_detector = language_detector
    
    async def detect(self, audio_frame: rtc.AudioFrame) -> vad.VADEvent:
        # Use base VAD for activity detection
        event = await self.base_vad.detect(audio_frame)
        
        # Add language detection on speech start
        if event.type == vad.VADEventType.START_OF_SPEECH:
            detected_language = await self.language_detector.detect(audio_frame)
            event.metadata = {"detected_language": detected_language}
        
        return event

async def entrypoint(ctx: JobContext):
    """Main entry point for the agent"""
    
    # Initialize services
    flight_service = FlightSearchService(
        amadeus_client_id=os.getenv("AMADEUS_CLIENT_ID"),
        amadeus_client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
        serpapi_key=os.getenv("SERPAPI_API_KEY")
    )
    
    monitor = PerformanceMonitor()
    multilingual_manager = MultilingualManager()
    
    # Create agent session with optimal configuration
    session = AgentSession(
        # STT with multilingual support
        stt=deepgram.STT(
            model="nova-3",
            language="multi",  # Auto-detect language
            punctuate=True,
            interim_results=True,
            endpointing=300,  # ms of silence before ending
            utterance_end_ms=1000
        ),
        
        # LLM configuration
        llm=openai.LLM(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=150,  # Keep responses concise for voice
            presence_penalty=0.1,
            frequency_penalty=0.1
        ),
        
        # TTS with multiple voices
        tts=cartesia.TTS(
            model="sonic-2",
            voice="f786b574-daa5-4673-aa0c-cbe3e8534c02",  # Multilingual voice
            speed=1.0,
            emotion="positive"
        ),
        
        # VAD configuration
        vad=MultilingualVAD(
            base_vad=silero.VAD.load(
                min_speech_duration=0.1,
                min_silence_duration=0.3,
                speech_threshold=0.5
            ),
            language_detector=multilingual_manager
        ),
        
        # Turn detection
        turn_detection=MultilingualModel(
            min_silence_duration_ms=300,
            speech_threshold=0.5
        )
    )
    
    # Start the session
    await session.start(
        room=ctx.room,
        agent=PolyglotRAGAssistant(flight_service, monitor),
        room_input_options=RoomInputOptions(
            # Enhanced noise cancellation
            noise_cancellation=noise_cancellation.BVC(
                model="BVC"  # Use BVCTelephony for phone calls
            ),
            
            # Audio configuration
            audio_sample_rate=48000,
            audio_channels=1,
            
            # Enable transcription forwarding
            forward_transcription=True
        )
    )
    
    # Connect to room
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    
    # Monitor connection
    monitor.track_connection(ctx.room)
    
    # Initial greeting
    initial_language = ctx.room.metadata.get("language", "en")
    greeting = multilingual_manager.get_greeting(initial_language)
    
    await session.generate_reply(
        instructions=f"Greet the user in {initial_language}: {greeting}"
    )
    
    # Keep session alive
    await session.wait_for_completion()

def main():
    """Main function to run the agent"""
    
    # Configure worker options
    worker_options = WorkerOptions(
        entrypoint_fnc=entrypoint,
        
        # Worker configuration
        worker_type=agents.WorkerType.ROOM,
        max_idle_time=30,  # seconds
        
        # Logging
        log_level="info",
        
        # Performance
        num_idle_workers=2,  # Pre-warm workers
        
        # Shutdown behavior  
        shutdown_grace_period=10  # seconds
    )
    
    # Run the agent
    agents.cli.run_app(worker_options)

if __name__ == "__main__":
    main()
2.2 Flight Search Service
Create file: backend/flight_search_service.py
pythonimport os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from dataclasses import asdict

from amadeus import Client, ResponseError
import serpapi

class FlightSearchService:
    """Service for searching flights with multiple API fallbacks"""
    
    def __init__(self, amadeus_client_id: str, amadeus_client_secret: str, serpapi_key: str):
        # Initialize Amadeus client
        self.amadeus = Client(
            client_id=amadeus_client_id,
            client_secret=amadeus_client_secret,
            # Use production environment
            hostname='production'
        )
        
        self.serpapi_key = serpapi_key
        
        # Cache configuration
        self.cache = {}
        self.cache_ttl = timedelta(minutes=30)
        
        # Circuit breaker for API failures
        self.api_failures = {"amadeus": 0, "serpapi": 0}
        self.failure_threshold = 3
        self.circuit_open_duration = timedelta(minutes=5)
        self.circuit_open_time = {}
    
    async def search_flights(self, params) -> List[Dict[str, Any]]:
        """Search for flights with fallback mechanisms"""
        
        # Check cache
        cache_key = self._get_cache_key(params)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        # Try Amadeus first if circuit is closed
        if self._is_circuit_closed("amadeus"):
            try:
                result = await self._search_amadeus(params)
                self._reset_circuit("amadeus")
                self._cache_result(cache_key, result)
                return result
            except Exception as e:
                print(f"Amadeus search failed: {e}")
                self._record_failure("amadeus")
        
        # Try SerpAPI as fallback
        if self._is_circuit_closed("serpapi"):
            try:
                result = await self._search_serpapi(params)
                self._reset_circuit("serpapi")
                self._cache_result(cache_key, result)
                return result
            except Exception as e:
                print(f"SerpAPI search failed: {e}")
                self._record_failure("serpapi")
        
        # Return mock data if all APIs fail
        return self._get_mock_flights(params)
    
    async def _search_amadeus(self, params) -> List[Dict[str, Any]]:
        """Search flights using Amadeus API"""
        
        # Run in thread pool since Amadeus client is synchronous
        loop = asyncio.get_event_loop()
        
        def amadeus_search():
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=params.origin.upper(),
                destinationLocationCode=params.destination.upper(),
                departureDate=params.departure_date,
                returnDate=params.return_date if params.return_date else None,
                adults=params.adults,
                children=params.children,
                travelClass=params.travel_class.upper(),
                nonStop=params.nonstop,
                currencyCode='USD',
                max=20
            )
            return response.data
        
        data = await loop.run_in_executor(None, amadeus_search)
        
        # Format results
        results = []
        for offer in data:
            formatted = self._format_amadeus_offer(offer)
            if formatted:
                results.append(formatted)
        
        return results
    
    async def _search_serpapi(self, params) -> List[Dict[str, Any]]:
        """Search flights using SerpAPI Google Flights"""
        
        async with aiohttp.ClientSession() as session:
            url = "https://serpapi.com/search"
            
            query_params = {
                "engine": "google_flights",
                "api_key": self.serpapi_key,
                "departure_id": params.origin.upper(),
                "arrival_id": params.destination.upper(),
                "outbound_date": params.departure_date,
                "return_date": params.return_date or "",
                "currency": "USD",
                "hl": "en",
                "adults": params.adults,
                "children": params.children,
                "type": "1" if params.return_date else "2",  # 1=round trip, 2=one way
                "travel_class": self._map_travel_class(params.travel_class),
                "nonstop": params.nonstop
            }
            
            async with session.get(url, params=query_params) as response:
                if response.status != 200:
                    raise Exception(f"SerpAPI returned status {response.status}")
                
                data = await response.json()
        
        # Format results
        results = []
        
        # Process best flights
        if "best_flights" in data:
            for flight_group in data["best_flights"]:
                formatted = self._format_serpapi_flight(flight_group)
                if formatted:
                    results.extend(formatted)
        
        # Process other flights
        if "other_flights" in data and len(results) < 10:
            for flight_group in data["other_flights"]:
                formatted = self._format_serpapi_flight(flight_group)
                if formatted:
                    results.extend(formatted)
                if len(results) >= 20:
                    break
        
        return results[:20]
    
    def _format_amadeus_offer(self, offer: Dict) -> Optional[Dict]:
        """Format Amadeus flight offer"""
        try:
            # Get first itinerary (outbound)
            itinerary = offer["itineraries"][0]
            segments = itinerary["segments"]
            
            # Build formatted result
            result = {
                "id": offer["id"],
                "price": {
                    "total": float(offer["price"]["total"]),
                    "currency": offer["price"]["currency"]
                },
                "itinerary": [],
                "duration": self._parse_duration(itinerary.get("duration", "")),
                "carrier": {
                    "code": segments[0]["carrierCode"],
                    "name": self._get_airline_name(segments[0]["carrierCode"])
                },
                "flight_number": f"{segments[0]['carrierCode']}{segments[0]['number']}",
                "booking_class": offer["travelerPricings"][0]["fareDetailsBySegment"][0]["cabin"]
            }
            
            # Format each segment
            for segment in segments:
                result["itinerary"].append({
                    "departure": {
                        "airport": segment["departure"]["iataCode"],
                        "time": segment["departure"]["at"],
                        "terminal": segment["departure"].get("terminal")
                    },
                    "arrival": {
                        "airport": segment["arrival"]["iataCode"],
                        "time": segment["arrival"]["at"],
                        "terminal": segment["arrival"].get("terminal")
                    },
                    "carrier": segment["carrierCode"],
                    "flight_number": f"{segment['carrierCode']}{segment['number']}",
                    "aircraft": segment.get("aircraft", {}).get("code"),
                    "duration": self._parse_duration(segment.get("duration", ""))
                })
            
            # Add convenience fields
            result["departure"] = result["itinerary"][0]["departure"]
            result["arrival"] = result["itinerary"][-1]["arrival"]
            result["stops"] = len(segments) - 1
            
            return result
            
        except Exception as e:
            print(f"Error formatting Amadeus offer: {e}")
            return None
    
    def _format_serpapi_flight(self, flight_group: Dict) -> List[Dict]:
        """Format SerpAPI flight data"""
        results = []
        
        try:
            flights = flight_group.get("flights", [])
            price = flight_group.get("price", 0)
            
            for i, flight_segments in enumerate(flights):
                if not isinstance(flight_segments, list):
                    flight_segments = [flight_segments]
                
                result = {
                    "id": f"serp_{hash(str(flight_group))}_{i}",
                    "price": {
                        "total": float(price) if price else 0,
                        "currency": "USD"
                    },
                    "itinerary": [],
                    "duration": sum(seg.get("duration", 0) for seg in flight_segments),
                    "booking_class": flight_group.get("type", "ECONOMY")
                }
                
                # Format segments
                for segment in flight_segments:
                    formatted_segment = {
                        "departure": {
                            "airport": segment["departure_airport"]["id"],
                            "time": segment["departure_airport"]["time"],
                            "terminal": None
                        },
                        "arrival": {
                            "airport": segment["arrival_airport"]["id"],
                            "time": segment["arrival_airport"]["time"],
                            "terminal": None
                        },
                        "carrier": self._extract_carrier_code(segment),
                        "flight_number": segment.get("flight_number", ""),
                        "aircraft": segment.get("airplane", ""),
                        "duration": segment.get("duration", 0)
                    }
                    result["itinerary"].append(formatted_segment)
                
                if result["itinerary"]:
                    # Add convenience fields
                    result["departure"] = result["itinerary"][0]["departure"]
                    result["arrival"] = result["itinerary"][-1]["arrival"]
                    result["stops"] = len(result["itinerary"]) - 1
                    result["carrier"] = {
                        "code": result["itinerary"][0]["carrier"],
                        "name": segment.get("airline", "")
                    }
                    result["flight_number"] = result["itinerary"][0]["flight_number"]
                    
                    results.append(result)
        
        except Exception as e:
            print(f"Error formatting SerpAPI flight: {e}")
        
        return results
    
    def _get_mock_flights(self, params) -> List[Dict[str, Any]]:
        """Return mock flight data for common routes"""
        
        # Mock data for demonstration
        base_time = datetime.strptime(params.departure_date, "%Y-%m-%d")
        
        mock_flights = []
        airlines = [
            ("AA", "American Airlines"),
            ("UA", "United Airlines"),
            ("DL", "Delta Air Lines")
        ]
        
        for i, (code, name) in enumerate(airlines):
            departure_time = base_time.replace(hour=8 + i * 4, minute=30)
            arrival_time = departure_time + timedelta(hours=5, minutes=30)
            
            mock_flights.append({
                "id": f"mock_{i}",
                "price": {
                    "total": 250 + i * 50,
                    "currency": "USD"
                },
                "carrier": {
                    "code": code,
                    "name": name
                },
                "flight_number": f"{code}{100 + i}",
                "departure": {
                    "airport": params.origin.upper(),
                    "time": departure_time.isoformat(),
                    "terminal": f"{i + 1}"
                },
                "arrival": {
                    "airport": params.destination.upper(),
                    "time": arrival_time.isoformat(),
                    "terminal": "A"
                },
                "duration": 330,  # 5h 30m in minutes
                "stops": 0,
                "booking_class": params.travel_class.upper(),
                "itinerary": [{
                    "departure": {
                        "airport": params.origin.upper(),
                        "time": departure_time.isoformat(),
                        "terminal": f"{i + 1}"
                    },
                    "arrival": {
                        "airport": params.destination.upper(),
                        "time": arrival_time.isoformat(),
                        "terminal": "A"
                    },
                    "carrier": code,
                    "flight_number": f"{code}{100 + i}",
                    "aircraft": "Boeing 737",
                    "duration": 330
                }]
            })
        
        return mock_flights
    
    # Helper methods
    
    def _get_cache_key(self, params) -> str:
        """Generate cache key from search parameters"""
        key_parts = [
            params.origin,
            params.destination,
            params.departure_date,
            params.return_date or "",
            str(params.adults),
            str(params.children),
            params.travel_class,
            str(params.nonstop)
        ]
        return "|".join(key_parts).lower()
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[Dict]]:
        """Get cached result if valid"""
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_data
        return None
    
    def _cache_result(self, cache_key: str, result: List[Dict]):
        """Cache search result"""
        self.cache[cache_key] = (result, datetime.now())
    
    def _is_circuit_closed(self, api_name: str) -> bool:
        """Check if circuit breaker is closed for API"""
        if self.api_failures[api_name] >= self.failure_threshold:
            if api_name in self.circuit_open_time:
                if datetime.now() - self.circuit_open_time[api_name] < self.circuit_open_duration:
                    return False
                else:
                    # Reset circuit after timeout
                    self.api_failures[api_name] = 0
                    del self.circuit_open_time[api_name]
        return True
    
    def _record_failure(self, api_name: str):
        """Record API failure"""
        self.api_failures[api_name] += 1
        if self.api_failures[api_name] >= self.failure_threshold:
            self.circuit_open_time[api_name] = datetime.now()
    
    def _reset_circuit(self, api_name: str):
        """Reset circuit breaker for API"""
        self.api_failures[api_name] = 0
        if api_name in self.circuit_open_time:
            del self.circuit_open_time[api_name]
    
    def _parse_duration(self, iso_duration: str) -> int:
        """Parse ISO 8601 duration to minutes"""
        if not iso_duration:
            return 0
        
        # Simple parser for PT#H#M format
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', iso_duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            return hours * 60 + minutes
        return 0
    
    def _get_airline_name(self, code: str) -> str:
        """Get airline name from IATA code"""
        airlines = {
            "AA": "American Airlines",
            "DL": "Delta Air Lines",
            "UA": "United Airlines",
            "BA": "British Airways",
            "LH": "Lufthansa",
            "AF": "Air France",
            "KL": "KLM",
            "IB": "Iberia",
            "QR": "Qatar Airways",
            "EK": "Emirates",
            "SQ": "Singapore Airlines",
            "NH": "All Nippon Airways",
            "AC": "Air Canada",
            "LX": "Swiss International",
            "TK": "Turkish Airlines"
        }
        return airlines.get(code, code)
    
    def _map_travel_class(self, travel_class: str) -> int:
        """Map travel class to SerpAPI format"""
        mapping = {
            "economy": 1,
            "premium": 2,
            "business": 3,
            "first": 4
        }
        return mapping.get(travel_class.lower(), 1)
    
    def _extract_carrier_code(self, segment: Dict) -> str:
        """Extract carrier code from SerpAPI segment"""
        # Try to extract from logo URL or flight number
        if "airline_logo" in segment:
            import re
            match = re.search(r'/([A-Z]{2})\.png', segment["airline_logo"])
            if match:
                return match.group(1)
        
        if "flight_number" in segment:
            # Extract first 2 letters
            return segment["flight_number"][:2].upper()
        
        return "XX"  # Unknown carrier
2.3 Multilingual Support Manager
Create file: backend/multilingual_manager.py
pythonimport asyncio
from typing import Dict, Optional, Tuple, List
import numpy as np
from dataclasses import dataclass
import json

@dataclass
class LanguageContext:
    """Context for language handling"""
    current_language: str
    confidence: float
    previous_language: Optional[str] = None
    switch_count: int = 0
    conversation_history: List[Dict] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []

class MultilingualManager:
    """Manager for multilingual support and context preservation"""
    
    def __init__(self):
        # Supported languages with their names
        self.supported_languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French", 
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "nl": "Dutch",
            "pl": "Polish",
            "sv": "Swedish",
            "da": "Danish",
            "no": "Norwegian",
            "fi": "Finnish",
            "tr": "Turkish",
            "el": "Greek",
            "he": "Hebrew",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "ms": "Malay",
            "uk": "Ukrainian",
            "cs": "Czech",
            "ro": "Romanian",
            "hu": "Hungarian",
            "bg": "Bulgarian"
        }
        
        # Context for each session
        self.session_contexts: Dict[str, LanguageContext] = {}
        
        # Common greetings in each language
        self.greetings = {
            "en": "Hello! I'm Polyglot, your multilingual flight assistant. How can I help you today?",
            "es": "¡Hola! Soy Polyglot, tu asistente de vuelos multilingüe. ¿Cómo puedo ayudarte hoy?",
            "fr": "Bonjour! Je suis Polyglot, votre assistant de vol multilingue. Comment puis-je vous aider aujourd'hui?",
            "de": "Hallo! Ich bin Polyglot, Ihr mehrsprachiger Flugassistent. Wie kann ich Ihnen heute helfen?",
            "it": "Ciao! Sono Polyglot, il tuo assistente di volo multilingue. Come posso aiutarti oggi?",
            "pt": "Olá! Eu sou Polyglot, seu assistente de voo multilíngue. Como posso ajudá-lo hoje?",
            "ja": "こんにちは！私はPolyglot、多言語対応のフライトアシスタントです。今日はどのようにお手伝いできますか？",
            "zh": "你好！我是Polyglot，您的多语言航班助手。今天我能为您做些什么？",
            "ko": "안녕하세요! 저는 다국어 항공편 도우미 Polyglot입니다. 오늘 어떻게 도와드릴까요?",
            "ru": "Привет! Я Polyglot, ваш многоязычный помощник по авиаперелетам. Чем я могу вам помочь сегодня?",
            "ar": "مرحبا! أنا Polyglot، مساعد الطيران متعدد اللغات. كيف يمكنني مساعدتك اليوم؟",
            "hi": "नमस्ते! मैं Polyglot हूं, आपका बहुभाषी उड़ान सहायक। आज मैं आपकी कैसे मदद कर सकता हूं?"
        }
        
        # Language switch phrases
        self.switch_acknowledgments = {
            "en": "I'll continue in English.",
            "es": "Continuaré en español.",
            "fr": "Je vais continuer en français.",
            "de": "Ich werde auf Deutsch fortfahren.",
            "it": "Continuerò in italiano.",
            "pt": "Vou continuar em português.",
            "ja": "日本語で続けます。",
            "zh": "我会用中文继续。",
            "ko": "한국어로 계속하겠습니다.",
            "ru": "Я продолжу на русском языке.",
            "ar": "سأستمر بالعربية.",
            "hi": "मैं हिंदी में जारी रखूंगा।"
        }
    
    async def detect_language(self, audio_frame) -> Tuple[str, float]:
        """Detect language from audio frame"""
        # This would integrate with a real language detection model
        # For now, return a placeholder
        # In production, use a service like Google Cloud Speech-to-Text
        # with language detection or a specialized model
        
        # Placeholder implementation
        return ("en", 0.95)
    
    def get_or_create_context(self, session_id: str) -> LanguageContext:
        """Get or create language context for session"""
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = LanguageContext(
                current_language="en",
                confidence=1.0
            )
        return self.session_contexts[session_id]
    
    async def handle_language_switch(
        self, 
        session_id: str, 
        new_language: str, 
        confidence: float
    ) -> Dict[str, any]:
        """Handle language switch in conversation"""
        
        context = self.get_or_create_context(session_id)
        
        # Check if this is actually a switch
        if context.current_language == new_language:
            return {
                "switched": False,
                "language": new_language,
                "message": None
            }
        
        # Check confidence threshold
        if confidence < 0.8:
            return {
                "switched": False,
                "language": context.current_language,
                "message": None,
                "low_confidence": True
            }
        
        # Perform switch
        context.previous_language = context.current_language
        context.current_language = new_language
        context.confidence = confidence
        context.switch_count += 1
        
        # Get acknowledgment message
        ack_message = self.switch_acknowledgments.get(
            new_language,
            self.switch_acknowledgments["en"]
        )
        
        # Preserve context
        preserved_context = await self.preserve_context(session_id)
        
        return {
            "switched": True,
            "language": new_language,
            "previous_language": context.previous_language,
            "message": ack_message,
            "preserved_context": preserved_context,
            "switch_count": context.switch_count
        }
    
    async def preserve_context(self, session_id: str) -> Dict[str, any]:
        """Preserve conversation context across language switches"""
        
        context = self.get_or_create_context(session_id)
        
        # Extract key information from conversation history
        preserved = {
            "search_params": {},
            "mentioned_airports": [],
            "mentioned_dates": [],
            "preferences": {},
            "previous_searches": []
        }
        
        # Analyze conversation history
        for entry in context.conversation_history[-10:]:  # Last 10 turns
            if entry.get("role") == "user":
                # Extract entities (airports, dates, etc.)
                # This would use NER in production
                content = entry.get("content", "")
                
                # Simple pattern matching for demo
                import re
                
                # Airport codes (3 letters)
                airports = re.findall(r'\b[A-Z]{3}\b', content.upper())
                preserved["mentioned_airports"].extend(airports)
                
                # Dates (YYYY-MM-DD)
                dates = re.findall(r'\d{4}-\d{2}-\d{2}', content)
                preserved["mentioned_dates"].extend(dates)
                
                # Preferences
                if "business" in content.lower():
                    preserved["preferences"]["class"] = "business"
                elif "first" in content.lower():
                    preserved["preferences"]["class"] = "first"
                
                if "nonstop" in content.lower() or "direct" in content.lower():
                    preserved["preferences"]["nonstop"] = True
        
        # Deduplicate
        preserved["mentioned_airports"] = list(set(preserved["mentioned_airports"]))
        preserved["mentioned_dates"] = list(set(preserved["mentioned_dates"]))
        
        return preserved
    
    def get_greeting(self, language: str) -> str:
        """Get greeting in specified language"""
        return self.greetings.get(language, self.greetings["en"])
    
    def format_response_for_language(
        self, 
        content: str, 
        language: str,
        response_type: str = "general"
    ) -> str:
        """Format response appropriately for target language"""
        
        # Add language-specific formatting
        if language in ["ja", "zh", "ko"]:
            # Asian languages may need different formatting
            content = content.replace("...", "…")
        
        if language == "ar" or language == "he":
            # RTL languages may need special handling
            # This would be handled by the UI layer typically
            pass
        
        # Add cultural adaptations
        if response_type == "greeting":
            # Add time-appropriate greetings
            import datetime
            hour = datetime.datetime.now().hour
            
            if language == "ja":
                if hour < 10:
                    content = "おはようございます。" + content
                elif hour < 18:
                    content = "こんにちは。" + content
                else:
                    content = "こんばんは。" + content
        
        return content
    
    def get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        return self.supported_languages.get(code, code)
    
    def is_language_supported(self, code: str) -> bool:
        """Check if language is supported"""
        return code in self.supported_languages
    
    def update_conversation_history(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        language: str
    ):
        """Update conversation history for context"""
        context = self.get_or_create_context(session_id)
        
        context.conversation_history.append({
            "role": role,
            "content": content,
            "language": language,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Keep only last 50 entries
        if len(context.conversation_history) > 50:
            context.conversation_history = context.conversation_history[-50:]
    
    def get_session_summary(self, session_id: str) -> Dict[str, any]:
        """Get summary of session for analytics"""
        context = self.get_or_create_context(session_id)
        
        language_usage = {}
        for entry in context.conversation_history:
            lang = entry.get("language", "unknown")
            language_usage[lang] = language_usage.get(lang, 0) + 1
        
        return {
            "current_language": context.current_language,
            "switch_count": context.switch_count,
            "languages_used": list(language_usage.keys()),
            "language_distribution": language_usage,
            "conversation_length": len(context.conversation_history)
        }
2.4 Performance Monitor
Create file: backend/performance_monitor.py
pythonimport time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import json
import os

class PerformanceMonitor:
    """Monitor and track performance metrics for the voice assistant"""
    
    def __init__(self):
        # Metrics storage
        self.metrics = {
            "latency": deque(maxlen=1000),
            "stt_latency": deque(maxlen=1000),
            "llm_latency": deque(maxlen=1000),
            "tts_latency": deque(maxlen=1000),
            "flight_search_latency": deque(maxlen=1000),
            "interruption_latency": deque(maxlen=1000),
            "language_switch_latency": deque(maxlen=1000),
            "error_count": defaultdict(int),
            "success_count": defaultdict(int),
            "tool_calls": defaultdict(int),
            "language_usage": defaultdict(int),
            "active_sessions": 0,
            "total_sessions": 0
        }
        
        # Thresholds for alerting
        self.thresholds = {
            "latency": 300,  # ms
            "stt_latency": 200,
            "llm_latency": 500,
            "tts_latency": 100,
            "flight_search_latency": 2000,
            "interruption_latency": 50,
            "error_rate": 0.05  # 5%
        }
        
        # Time windows for rate calculations
        self.time_windows = {
            "1m": deque(maxlen=60),
            "5m": deque(maxlen=300),
            "1h": deque(maxlen=3600)
        }
        
        # Alert callbacks
        self.alert_callbacks = []
        
        # Start background monitoring
        self.monitoring_task = None
    
    async def start_monitoring(self):
        """Start background monitoring task"""
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                # Calculate current metrics
                metrics_summary = self.get_metrics_summary()
                
                # Check thresholds
                await self._check_thresholds(metrics_summary)
                
                # Log metrics
                self._log_metrics(metrics_summary)
                
                # Wait before next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
    
    def track_latency(self, operation: str, duration_ms: float):
        """Track latency for an operation"""
        timestamp = time.time()
        
        # Add to specific operation metrics
        if operation in self.metrics:
            self.metrics[operation].append(duration_ms)
        
        # Add to general latency
        self.metrics["latency"].append(duration_ms)
        
        # Add to time windows
        for window in self.time_windows.values():
            window.append({
                "timestamp": timestamp,
                "operation": operation,
                "duration": duration_ms
            })
        
        # Check if exceeds threshold
        threshold = self.thresholds.get(operation, self.thresholds["latency"])
        if duration_ms > threshold:
            asyncio.create_task(self._alert_high_latency(operation, duration_ms, threshold))
    
    def track_error(self, error_type: str, details: Dict[str, Any] = None):
        """Track an error occurrence"""
        self.metrics["error_count"][error_type] += 1
        
        # Log error details
        error_entry = {
            "timestamp": time.time(),
            "type": error_type,
            "details": details or {}
        }
        
        # Add to time windows for rate calculation
        for window in self.time_windows.values():
            window.append(error_entry)
    
    def track_success(self, operation: str):
        """Track successful operation"""
        self.metrics["success_count"][operation] += 1
    
    def track_tool_call(self, tool_name: str, success: bool):
        """Track tool usage"""
        self.metrics["tool_calls"][tool_name] += 1
        if success:
            self.track_success(f"tool_{tool_name}")
        else:
            self.track_error(f"tool_error_{tool_name}")
    
    def track_language_usage(self, language: str):
        """Track language usage"""
        self.metrics["language_usage"][language] += 1
    
    def track_session_start(self):
        """Track new session start"""
        self.metrics["active_sessions"] += 1
        self.metrics["total_sessions"] += 1
    
    def track_session_end(self):
        """Track session end"""
        self.metrics["active_sessions"] = max(0, self.metrics["active_sessions"] - 1)
    
    def track_interruption(self, latency_ms: float):
        """Track voice interruption"""
        self.metrics["interruption_latency"].append(latency_ms)
        self.track_latency("interruption_latency", latency_ms)
    
    def track_language_switch(self, from_lang: str, to_lang: str, latency_ms: float):
        """Track language switch"""
        self.metrics["language_switch_latency"].append(latency_ms)
        self.track_latency("language_switch_latency", latency_ms)
        self.track_language_usage(to_lang)
    
    async def track_event(self, event_type: str, data: Dict[str, Any]):
        """Track generic event"""
        # Add to appropriate metrics based on event type
        if event_type == "conversation_update":
            if data.get("language"):
                self.track_language_usage(data["language"])
        
        # Log event
        event_entry = {
            "timestamp": time.time(),
            "type": event_type,
            "data": data
        }
    
    def track_connection(self, room):
        """Track LiveKit room connection"""
        self.track_session_start()
        
        # Set up room event handlers
        @room.on("participant_connected")
        def on_participant_connected(participant):
            self.track_success("participant_connected")
        
        @room.on("participant_disconnected")
        def on_participant_disconnected(participant):
            self.track_session_end()
        
        @room.on("connection_quality_changed")
        def on_connection_quality(participant, quality):
            if quality == "poor":
                self.track_error("poor_connection_quality", {
                    "participant": participant.identity
                })
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "active_sessions": self.metrics["active_sessions"],
            "total_sessions": self.metrics["total_sessions"]
        }
        
        # Calculate latency statistics
        for metric_name in ["latency", "stt_latency", "llm_latency", "tts_latency", 
                           "flight_search_latency", "interruption_latency"]:
            values = list(self.metrics[metric_name])
            if values:
                summary[metric_name] = {
                    "avg": statistics.mean(values),
                    "median": statistics.median(values),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99),
                    "min": min(values),
                    "max": max(values)
                }
        
        # Calculate error rate
        total_ops = sum(self.metrics["success_count"].values())
        total_errors = sum(self.metrics["error_count"].values())
        
        if total_ops > 0:
            summary["error_rate"] = total_errors / (total_ops + total_errors)
        else:
            summary["error_rate"] = 0
        
        # Language distribution
        total_language_use = sum(self.metrics["language_usage"].values())
        if total_language_use > 0:
            summary["language_distribution"] = {
                lang: count / total_language_use 
                for lang, count in self.metrics["language_usage"].items()
            }
        
        # Tool usage
        summary["tool_usage"] = dict(self.metrics["tool_calls"])
        
        return summary
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    async def _check_thresholds(self, metrics_summary: Dict[str, Any]):
        """Check if any metrics exceed thresholds"""
        
        # Check latency thresholds
        for metric_name, threshold in self.thresholds.items():
            if metric_name in metrics_summary and isinstance(metrics_summary[metric_name], dict):
                avg_value = metrics_summary[metric_name].get("avg", 0)
                if avg_value > threshold:
                    await self._alert_threshold_exceeded(metric_name, avg_value, threshold)
        
        # Check error rate
        if metrics_summary["error_rate"] > self.thresholds["error_rate"]:
            await self._alert_high_error_rate(metrics_summary["error_rate"])
    
    async def _alert_high_latency(self, operation: str, latency: float, threshold: float):
        """Alert for high latency"""
        alert = {
            "type": "high_latency",
            "operation": operation,
            "latency": latency,
            "threshold": threshold,
            "timestamp": datetime.now().isoformat()
        }
        await self._send_alert(alert)
    
    async def _alert_threshold_exceeded(self, metric: str, value: float, threshold: float):
        """Alert for threshold exceeded"""
        alert = {
            "type": "threshold_exceeded",
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "timestamp": datetime.now().isoformat()
        }
        await self._send_alert(alert)
    
    async def _alert_high_error_rate(self, error_rate: float):
        """Alert for high error rate"""
        alert = {
            "type": "high_error_rate",
            "error_rate": error_rate,
            "threshold": self.thresholds["error_rate"],
            "timestamp": datetime.now().isoformat()
        }
        await self._send_alert(alert)
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Send alert to registered callbacks"""
        print(f"ALERT: {json.dumps(alert, indent=2)}")
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")
    
    def _log_metrics(self, metrics_summary: Dict[str, Any]):
        """Log metrics to file or monitoring service"""
        # Log to file
        log_file = f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(metrics_summary) + "\n")
        
        # In production, send to monitoring service like CloudWatch, Datadog, etc.
    
    def register_alert_callback(self, callback):
        """Register callback for alerts"""
        self.alert_callbacks.append(callback)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        metrics = self.get_metrics_summary()
        
        # Determine health status
        status = "healthy"
        issues = []
        
        # Check error rate
        if metrics["error_rate"] > self.thresholds["error_rate"]:
            status = "unhealthy"
            issues.append(f"High error rate: {metrics['error_rate']:.2%}")
        
        # Check latencies
        for metric in ["latency", "stt_latency", "llm_latency"]:
            if metric in metrics and metrics[metric]["avg"] > self.thresholds.get(metric, 1000):
                if status == "healthy":
                    status = "degraded"
                issues.append(f"High {metric}: {metrics[metric]['avg']:.0f}ms")
        
        return {
            "status": status,
            "issues": issues,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
PART 3: Docker Configuration
3.1 Backend Agent Dockerfile
Create file: backend/Dockerfile
dockerfile# Multi-stage build for Python agent
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Download model files during build
RUN python -c "from livekit.plugins import silero; silero.VAD.download_files()"

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash agent

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/agent/.local

# Copy application code
COPY --chown=agent:agent . .

# Copy downloaded models
COPY --from=builder /build/.cache /home/agent/.cache

# Set environment variables
ENV PATH=/home/agent/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Switch to non-root user
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "agent.py", "start"]
3.2 Frontend Dockerfile
Create file: frontend/Dockerfile
dockerfile# Frontend Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash frontend

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=frontend:frontend . .

# Create necessary directories
RUN mkdir -p /app/static /app/templates /app/audio/feedback

# Switch to non-root user
USER frontend

# Expose Gradio port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run Gradio app
CMD ["python", "gradio_app.py", "--server_name", "0.0.0.0", "--server_port", "7860"]
3.3 Docker Compose for Local Testing
Create file: docker-compose.yml
yamlversion: '3.8'

services:
  # Backend Agent Service
  agent:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - LIVEKIT_URL=${LIVEKIT_URL}
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - CARTESIA_API_KEY=${CARTESIA_API_KEY}
      - AMADEUS_CLIENT_ID=${AMADEUS_CLIENT_ID}
      - AMADEUS_CLIENT_SECRET=${AMADEUS_CLIENT_SECRET}
      - SERPAPI_API_KEY=${SERPAPI_API_KEY}
      - LOG_LEVEL=info
    volumes:
      - agent_models:/home/agent/.cache
      - agent_logs:/app/logs
    networks:
      - polyglot_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  # Frontend Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "7860:7860"
    environment:
      - LIVEKIT_URL=${LIVEKIT_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GRADIO_SERVER_NAME=0.0.0.0
      - GRADIO_SERVER_PORT=7860
      - GRADIO_SHARE=false
    volumes:
      - frontend_static:/app/static
    networks:
      - polyglot_network
    depends_on:
      - agent
    restart: unless-stopped

  # Redis for caching
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - polyglot_network
    restart: unless-stopped

  # PostgreSQL for metadata
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=polyglot_rag
      - POSTGRES_USER=polyglot
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-secretpassword}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - polyglot_network
    restart: unless-stopped

volumes:
  agent_models:
  agent_logs:
  frontend_static:
  redis_data:
  postgres_data:

networks:
  polyglot_network:
    driver: bridge
PART 4: Terraform AWS ECS Deployment
4.1 Main Terraform Configuration
Create file: terraform/main.tf
hclterraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "polyglot-rag-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
    dynamodb_table = "polyglot-rag-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "PolyglotRAG"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local variables
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    CreatedBy   = "Terraform"
  }
  
  # Container environment variables
  common_env_vars = [
    {
      name  = "ENVIRONMENT"
      value = var.environment
    },
    {
      name  = "AWS_REGION"
      value = var.aws_region
    },
    {
      name  = "LOG_LEVEL"
      value = var.log_level
    }
  ]
}
4.2 VPC Configuration
Create file: terraform/vpc.tf
hcl# VPC Module
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${local.name_prefix}-vpc"
  cidr = var.vpc_cidr
  
  azs             = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway = true
  single_nat_gateway = var.environment == "dev" ? true : false
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  # VPC Flow Logs
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true
  
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
  
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }
  
  tags = local.common_tags
}

# VPC Endpoints for AWS Services
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = module.vpc.vpc_id
  service_name = "com.amazonaws.${var.aws_region}.s3"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-s3-endpoint"
  })
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  
  private_dns_enabled = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecr-api-endpoint"
  })
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  
  private_dns_enabled = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecr-dkr-endpoint"
  })
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${local.name_prefix}-vpc-endpoints-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc-endpoints-sg"
  })
}
4.3 ECS Cluster and Services
Create file: terraform/ecs.tf
hcl# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = local.common_tags
}

# ECS Cluster Capacity Providers
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name
  
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# Task Execution Role
resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.name_prefix}-ecs-task-execution"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for Secrets Manager
resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "${local.name_prefix}-ecs-secrets-policy"
  role = aws_iam_role.ecs_task_execution.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Resource = [
          aws_secretsmanager_secret.api_keys.arn,
          aws_kms_key.main.arn
        ]
      }
    ]
  })
}

# Task Role for application
resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-ecs-task"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Task role policies
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${local.name_prefix}-ecs-task-policy"
  role = aws_iam_role.ecs_task.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.assets.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "agent" {
  name              = "/ecs/${local.name_prefix}/agent"
  retention_in_days = var.log_retention_days
  
  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.name_prefix}/frontend"
  retention_in_days = var.log_retention_days
  
  tags = local.common_tags
}

# Agent Service Task Definition
resource "aws_ecs_task_definition" "agent" {
  family                   = "${local.name_prefix}-agent"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.agent_cpu
  memory                   = var.agent_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name  = "agent"
      image = "${var.docker_hub_username}/polyglot-agent:${var.agent_image_tag}"
      
      essential = true
      
      environment = concat(local.common_env_vars, [
        {
          name  = "SERVICE_NAME"
          value = "agent"
        },
        {
          name  = "REDIS_HOST"
          value = aws_elasticache_cluster.redis.cache_nodes[0].address
        },
        {
          name  = "POSTGRES_HOST"
          value = aws_db_instance.postgres.address
        },
        {
          name  = "POSTGRES_DB"
          value = aws_db_instance.postgres.db_name
        }
      ])
      
      secrets = [
        {
          name      = "LIVEKIT_URL"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:LIVEKIT_URL::"
        },
        {
          name      = "LIVEKIT_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:LIVEKIT_API_KEY::"
        },
        {
          name      = "LIVEKIT_API_SECRET"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:LIVEKIT_API_SECRET::"
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:OPENAI_API_KEY::"
        },
        {
          name      = "AContinueResumed Terraform configuration for ECS task definition.0sThe user wants me to continue with the very long and detailed prompt for implementing the Polyglot RAG voice assistant. I was in the middle of creating the Terraform configuration files. Let me continue from where I left off with the ECS task definition.hcl        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:OPENAI_API_KEY::"
        },
        {
          name      = "DEEPGRAM_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:DEEPGRAM_API_KEY::"
        },
        {
          name      = "CARTESIA_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:CARTESIA_API_KEY::"
        },
        {
          name      = "AMADEUS_CLIENT_ID"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:AMADEUS_CLIENT_ID::"
        },
        {
          name      = "AMADEUS_CLIENT_SECRET"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:AMADEUS_CLIENT_SECRET::"
        },
        {
          name      = "SERPAPI_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:SERPAPI_API_KEY::"
        },
        {
          name      = "POSTGRES_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:password::"
        }
      ]
      
      portMappings = []
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.agent.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "agent"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "python -c 'import sys; sys.exit(0)'"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }
      
      ulimits = [
        {
          name      = "nofile"
          softLimit = 65536
          hardLimit = 65536
        }
      ]
    }
  ])
  
  tags = local.common_tags
}

# Agent Service
resource "aws_ecs_service" "agent" {
  name            = "${local.name_prefix}-agent"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.agent.arn
  desired_count   = var.agent_desired_count
  
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
    
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }
  
  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.agent.id]
    assign_public_ip = false
  }
  
  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 100
    base             = 1
  }
  
  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"
  
  tags = local.common_tags
}

# Frontend Task Definition
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name  = "frontend"
      image = "${var.docker_hub_username}/polyglot-frontend:${var.frontend_image_tag}"
      
      essential = true
      
      environment = concat(local.common_env_vars, [
        {
          name  = "SERVICE_NAME"
          value = "frontend"
        },
        {
          name  = "GRADIO_SERVER_NAME"
          value = "0.0.0.0"
        },
        {
          name  = "GRADIO_SERVER_PORT"
          value = "7860"
        }
      ])
      
      secrets = [
        {
          name      = "LIVEKIT_URL"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:LIVEKIT_URL::"
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:OPENAI_API_KEY::"
        }
      ]
      
      portMappings = [
        {
          containerPort = 7860
          protocol      = "tcp"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "frontend"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:7860/health || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }
    }
  ])
  
  tags = local.common_tags
}

# Frontend Service
resource "aws_ecs_service" "frontend" {
  name            = "${local.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
    
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }
  
  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 7860
  }
  
  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 100
    base             = 1
  }
  
  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"
  
  tags = local.common_tags
  
  depends_on = [
    aws_lb_listener.frontend
  ]
}

# Security Groups
resource "aws_security_group" "agent" {
  name_prefix = "${local.name_prefix}-agent-"
  vpc_id      = module.vpc.vpc_id
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-agent-sg"
  })
}

resource "aws_security_group" "frontend" {
  name_prefix = "${local.name_prefix}-frontend-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port       = 7860
    to_port         = 7860
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-sg"
  })
}
4.4 Load Balancer Configuration
Create file: terraform/alb.tf
hcl# Application Load Balancer
resource "aws_lb" "frontend" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  
  enable_deletion_protection = var.environment == "production" ? true : false
  enable_http2              = true
  enable_cross_zone_load_balancing = true
  
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb"
    enabled = true
  }
  
  tags = local.common_tags
}

# ALB Security Group
resource "aws_security_group" "alb" {
  name_prefix = "${local.name_prefix}-alb-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb-sg"
  })
}

# Target Group
resource "aws_lb_target_group" "frontend" {
  name                 = "${local.name_prefix}-frontend"
  port                 = 7860
  protocol             = "HTTP"
  vpc_id               = module.vpc.vpc_id
  target_type          = "ip"
  deregistration_delay = 30
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
  
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }
  
  tags = local.common_tags
}

# HTTP Listener (redirect to HTTPS)
resource "aws_lb_listener" "frontend_http" {
  load_balancer_arn = aws_lb.frontend.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS Listener
resource "aws_lb_listener" "frontend" {
  load_balancer_arn = aws_lb.frontend.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.main.certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# S3 Bucket for ALB logs
resource "aws_s3_bucket" "alb_logs" {
  bucket = "${local.name_prefix}-alb-logs-${data.aws_caller_identity.current.account_id}"
  
  tags = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  
  rule {
    id     = "expire-old-logs"
    status = "Enabled"
    
    expiration {
      days = 30
    }
  }
}

# Bucket policy for ALB logs
data "aws_elb_service_account" "main" {}

resource "aws_s3_bucket_policy" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = data.aws_elb_service_account.main.arn
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/*"
      }
    ]
  })
}
4.5 Auto Scaling Configuration
Create file: terraform/autoscaling.tf
hcl# Auto Scaling for Agent Service
resource "aws_appautoscaling_target" "agent" {
  max_capacity       = var.agent_max_count
  min_capacity       = var.agent_min_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.agent.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU-based scaling for Agent
resource "aws_appautoscaling_policy" "agent_cpu" {
  name               = "${local.name_prefix}-agent-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.agent.resource_id
  scalable_dimension = aws_appautoscaling_target.agent.scalable_dimension
  service_namespace  = aws_appautoscaling_target.agent.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Memory-based scaling for Agent
resource "aws_appautoscaling_policy" "agent_memory" {
  name               = "${local.name_prefix}-agent-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.agent.resource_id
  scalable_dimension = aws_appautoscaling_target.agent.scalable_dimension
  service_namespace  = aws_appautoscaling_target.agent.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    
    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Auto Scaling for Frontend Service
resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = var.frontend_max_count
  min_capacity       = var.frontend_min_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Request count scaling for Frontend
resource "aws_appautoscaling_policy" "frontend_requests" {
  name               = "${local.name_prefix}-frontend-request-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.frontend.arn_suffix}/${aws_lb_target_group.frontend.arn_suffix}"
    }
    
    target_value       = 1000.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Scheduled scaling for predictable traffic patterns
resource "aws_appautoscaling_scheduled_action" "agent_scale_up_morning" {
  name               = "${local.name_prefix}-agent-scale-up-morning"
  service_namespace  = aws_appautoscaling_target.agent.service_namespace
  resource_id        = aws_appautoscaling_target.agent.resource_id
  scalable_dimension = aws_appautoscaling_target.agent.scalable_dimension
  
  schedule = "cron(0 6 * * ? *)"  # 6 AM UTC daily
  
  scalable_target_action {
    min_capacity = var.agent_min_count + 2
    max_capacity = var.agent_max_count
  }
}

resource "aws_appautoscaling_scheduled_action" "agent_scale_down_night" {
  name               = "${local.name_prefix}-agent-scale-down-night"
  service_namespace  = aws_appautoscaling_target.agent.service_namespace
  resource_id        = aws_appautoscaling_target.agent.resource_id
  scalable_dimension = aws_appautoscaling_target.agent.scalable_dimension
  
  schedule = "cron(0 22 * * ? *)"  # 10 PM UTC daily
  
  scalable_target_action {
    min_capacity = var.agent_min_count
    max_capacity = var.agent_max_count
  }
}
4.6 Database and Cache Configuration
Create file: terraform/data.tf
hcl# RDS PostgreSQL with pgvector
resource "aws_db_subnet_group" "postgres" {
  name       = "${local.name_prefix}-postgres"
  subnet_ids = module.vpc.private_subnets
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-postgres-subnet-group"
  })
}

resource "aws_security_group" "postgres" {
  name_prefix = "${local.name_prefix}-postgres-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [
      aws_security_group.agent.id,
      aws_security_group.frontend.id
    ]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-postgres-sg"
  })
}

resource "aws_db_parameter_group" "postgres" {
  name   = "${local.name_prefix}-postgres"
  family = "postgres16"
  
  parameter {
    name  = "shared_preload_libraries"
    value = "vector"
  }
  
  tags = local.common_tags
}

resource "aws_db_instance" "postgres" {
  identifier = "${local.name_prefix}-postgres"
  
  engine         = "postgres"
  engine_version = "16.1"
  instance_class = var.db_instance_class
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.main.arn
  
  db_name  = "polyglot_rag"
  username = "polyglot"
  password = random_password.db_password.result
  
  vpc_security_group_ids = [aws_security_group.postgres.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  parameter_group_name   = aws_db_parameter_group.postgres.name
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  multi_az               = var.environment == "production" ? true : false
  deletion_protection    = var.environment == "production" ? true : false
  skip_final_snapshot    = var.environment == "dev" ? true : false
  final_snapshot_identifier = var.environment == "production" ? "${local.name_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  
  tags = local.common_tags
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name_prefix}-redis"
  subnet_ids = module.vpc.private_subnets
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-subnet-group"
  })
}

resource "aws_security_group" "redis" {
  name_prefix = "${local.name_prefix}-redis-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [
      aws_security_group.agent.id,
      aws_security_group.frontend.id
    ]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-sg"
  })
}

resource "aws_elasticache_parameter_group" "redis" {
  name   = "${local.name_prefix}-redis"
  family = "redis7"
  
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
  
  tags = local.common_tags
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${local.name_prefix}-redis"
  engine              = "redis"
  engine_version      = "7.1"
  node_type           = var.redis_node_type
  num_cache_nodes     = 1
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  port                = 6379
  subnet_group_name   = aws_elasticache_subnet_group.redis.name
  security_group_ids  = [aws_security_group.redis.id]
  
  snapshot_retention_limit = var.environment == "production" ? 5 : 0
  snapshot_window         = "03:00-05:00"
  maintenance_window      = "sun:05:00-sun:06:00"
  
  notification_topic_arn = aws_sns_topic.alerts.arn
  
  tags = local.common_tags
}

# S3 Bucket for assets and models
resource "aws_s3_bucket" "assets" {
  bucket = "${local.name_prefix}-assets-${data.aws_caller_identity.current.account_id}"
  
  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id
  
  rule {
    id     = "delete-old-versions"
    status = "Enabled"
    
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}
4.7 Secrets Management
Create file: terraform/secrets.tf
hcl# KMS Key for encryption
resource "aws_kms_key" "main" {
  description             = "KMS key for ${local.name_prefix} encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  tags = local.common_tags
}

resource "aws_kms_alias" "main" {
  name          = "alias/${local.name_prefix}"
  target_key_id = aws_kms_key.main.key_id
}

# Generate random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Secrets Manager for API keys
resource "aws_secretsmanager_secret" "api_keys" {
  name                    = "${local.name_prefix}-api-keys"
  recovery_window_in_days = var.environment == "production" ? 30 : 0
  kms_key_id             = aws_kms_key.main.id
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  
  secret_string = jsonencode({
    LIVEKIT_URL            = var.livekit_url
    LIVEKIT_API_KEY        = var.livekit_api_key
    LIVEKIT_API_SECRET     = var.livekit_api_secret
    OPENAI_API_KEY         = var.openai_api_key
    DEEPGRAM_API_KEY       = var.deepgram_api_key
    CARTESIA_API_KEY       = var.cartesia_api_key
    AMADEUS_CLIENT_ID      = var.amadeus_client_id
    AMADEUS_CLIENT_SECRET  = var.amadeus_client_secret
    SERPAPI_API_KEY        = var.serpapi_api_key
  })
}

# Database credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${local.name_prefix}-db-credentials"
  recovery_window_in_days = var.environment == "production" ? 30 : 0
  kms_key_id             = aws_kms_key.main.id
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  
  secret_string = jsonencode({
    username = aws_db_instance.postgres.username
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
    dbname   = aws_db_instance.postgres.db_name
  })
}
4.8 Monitoring and Alerting
Create file: terraform/monitoring.tf
hcl# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name              = "${local.name_prefix}-alerts"
  kms_master_key_id = aws_kms_key.main.id
  
  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name_prefix}-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", aws_ecs_service.agent.name, "ClusterName", aws_ecs_cluster.main.name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Agent Service Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", aws_ecs_service.frontend.name, "ClusterName", aws_ecs_cluster.main.name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Frontend Service Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.frontend.arn_suffix],
            [".", "RequestCount", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Load Balancer Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.postgres.id],
            [".", "DatabaseConnections", ".", "."],
            [".", "FreeableMemory", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Database Metrics"
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "agent_cpu_high" {
  alarm_name          = "${local.name_prefix}-agent-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors agent CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.agent.name
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "agent_memory_high" {
  alarm_name          = "${local.name_prefix}-agent-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "90"
  alarm_description   = "This metric monitors agent memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.agent.name
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  alarm_name          = "${local.name_prefix}-alb-unhealthy-hosts"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "This metric monitors unhealthy ALB targets"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    TargetGroup  = aws_lb_target_group.frontend.arn_suffix
    LoadBalancer = aws_lb.frontend.arn_suffix
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }
  
  tags = local.common_tags
}

# Custom metrics for application monitoring
resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "${local.name_prefix}-error-count"
  log_group_name = aws_cloudwatch_log_group.agent.name
  pattern        = "[timestamp, request_id, level=ERROR, ...]"
  
  metric_transformation {
    name      = "ErrorCount"
    namespace = "${local.name_prefix}/Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "application_errors" {
  alarm_name          = "${local.name_prefix}-application-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ErrorCount"
  namespace           = "${local.name_prefix}/Application"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors application errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"
  
  tags = local.common_tags
}
4.9 SSL Certificate Configuration
Create file: terraform/certificate.tf
hcl# Route53 Hosted Zone (if not already existing)
data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

# ACM Certificate
resource "aws_acm_certificate" "main" {
  domain_name       = var.domain_name
  validation_method = "DNS"
  
  subject_alternative_names = [
    "*.${var.domain_name}"
  ]
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = local.common_tags
}

# Certificate validation
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  
  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
}

resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# Route53 A record for ALB
resource "aws_route53_record" "main" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  
  alias {
    name                   = aws_lb.frontend.dns_name
    zone_id                = aws_lb.frontend.zone_id
    evaluate_target_health = true
  }
}
4.10 Variables Configuration
Create file: terraform/variables.tf
hclvariable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "polyglot-rag"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# ECS Configuration
variable "agent_cpu" {
  description = "CPU units for agent task"
  type        = string
  default     = "2048"
}

variable "agent_memory" {
  description = "Memory for agent task"
  type        = string
  default     = "4096"
}

variable "agent_desired_count" {
  description = "Desired number of agent tasks"
  type        = number
  default     = 3
}

variable "agent_min_count" {
  description = "Minimum number of agent tasks"
  type        = number
  default     = 2
}

variable "agent_max_count" {
  description = "Maximum number of agent tasks"
  type        = number
  default     = 20
}

variable "frontend_cpu" {
  description = "CPU units for frontend task"
  type        = string
  default     = "1024"
}

variable "frontend_memory" {
  description = "Memory for frontend task"
  type        = string
  default     = "2048"
}

variable "frontend_desired_count" {
  description = "Desired number of frontend tasks"
  type        = number
  default     = 2
}

variable "frontend_min_count" {
  description = "Minimum number of frontend tasks"
  type        = number
  default     = 2
}

variable "frontend_max_count" {
  description = "Maximum number of frontend tasks"
  type        = number
  default     = 10
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.r6g.large"
}

# Docker Configuration
variable "docker_hub_username" {
  description = "Docker Hub username"
  type        = string
}

variable "agent_image_tag" {
  description = "Docker image tag for agent"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Docker image tag for frontend"
  type        = string
  default     = "latest"
}

# API Keys (sensitive)
variable "livekit_url" {
  description = "LiveKit URL"
  type        = string
  sensitive   = true
}

variable "livekit_api_key" {
  description = "LiveKit API key"
  type        = string
  sensitive   = true
}

variable "livekit_api_secret" {
  description = "LiveKit API secret"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "deepgram_api_key" {
  description = "Deepgram API key"
  type        = string
  sensitive   = true
}

variable "cartesia_api_key" {
  description = "Cartesia API key"
  type        = string
  sensitive   = true
}

variable "amadeus_client_id" {
  description = "Amadeus client ID"
  type        = string
  sensitive   = true
}

variable "amadeus_client_secret" {
  description = "Amadeus client secret"
  type        = string
  sensitive   = true
}

variable "serpapi_api_key" {
  description = "SerpAPI API key"
  type        = string
  sensitive   = true
}

# Monitoring
variable "alert_email" {
  description = "Email for alerts"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "info"
}
4.11 Outputs Configuration
Create file: terraform/outputs.tf
hcloutput "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.frontend.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.frontend.zone_id
}

output "application_url" {
  description = "URL of the application"
  value       = "https://${var.domain_name}"
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "agent_service_name" {
  description = "Name of the agent ECS service"
  value       = aws_ecs_service.agent.name
}

output "frontend_service_name" {
  description = "Name of the frontend ECS service"
  value       = aws_ecs_service.frontend.name
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis cache endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  sensitive   = true
}

output "cloudwatch_dashboard_url" {
  description = "URL to CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}
PART 5: Manual Deployment Instructions
5.1 Prerequisites Setup
Create file: deployment/prerequisites.md
markdown# Prerequisites for Polyglot RAG Deployment

## Required Tools Installation

### 1. Install AWS CLI
```bash
# On macOS
brew install awscli

# On Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
# Enter default output format (json)
2. Install Terraform
bash# On macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# On Linux
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
3. Install Docker
bash# On macOS
brew install --cask docker

# On Linux (Ubuntu)
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
4. Install Python and Dependencies
bash# Install Python 3.11
pyenv install 3.11.8
pyenv global 3.11.8

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
5. Create Docker Hub Account

Go to https://hub.docker.com/signup
Create account
Login locally:

bashdocker login
# Enter your Docker Hub username
# Enter your Docker Hub password
AWS Account Setup
1. Create S3 Bucket for Terraform State
bash# Create S3 bucket for state
aws s3api create-bucket \
    --bucket polyglot-rag-terraform-state \
    --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket polyglot-rag-terraform-state \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket polyglot-rag-terraform-state \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
2. Create DynamoDB Table for State Locking
bashaws dynamodb create-table \
    --table-name polyglot-rag-terraform-locks \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1
3. Create IAM User for Deployment
bash# Create IAM user
aws iam create-user --user-name polyglot-rag-deploy

# Attach Administrator policy (for initial setup)
aws iam attach-user-policy \
    --user-name polyglot-rag-deploy \
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access key
aws iam create-access-key --user-name polyglot-rag-deploy
# Save the AccessKeyId and SecretAccessKey
Domain Setup
1. Register Domain (if needed)

Use AWS Route53 or your preferred registrar
Update nameservers to Route53 if using external registrar

2. Create Hosted Zone in Route53
bash# Create hosted zone
aws route53 create-hosted-zone \
    --name your-domain.com \
    --caller-reference $(date +%s) \
    --hosted-zone-config Comment="Polyglot RAG domain"
API Keys Setup
1. LiveKit Cloud

Sign up at https://cloud.livekit.io
Create a new project
Copy API Key and Secret

2. OpenAI

Sign up at https://platform.openai.com
Go to API Keys section
Create new API key

3. Deepgram

Sign up at https://console.deepgram.com
Create new API key

4. Cartesia

Sign up at https://cartesia.ai
Get API key from dashboard

5. Amadeus

Sign up at https://developers.amadeus.com
Create app
Get Client ID and Secret

6. SerpAPI

Sign up at https://serpapi.com
Get API key from dashboard

Environment Configuration
Create .env file:
bash# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Docker Hub
DOCKER_HUB_USERNAME=your-dockerhub-username

# Domain
DOMAIN_NAME=your-domain.com

# API Keys
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxxxxxx
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
DEEPGRAM_API_KEY=xxxxxxxxxxxxx
CARTESIA_API_KEY=xxxxxxxxxxxxx
AMADEUS_CLIENT_ID=xxxxxxxxxxxxx
AMADEUS_CLIENT_SECRET=xxxxxxxxxxxxx
SERPAPI_API_KEY=xxxxxxxxxxxxx

# Alerts
ALERT_EMAIL=your-email@example.com

#### 5.2 Step-by-Step Deployment Guide

**Create file: `deployment/deployment_guide.md`**
```markdown
# Polyglot RAG Manual Deployment Guide

## Phase 1: Build and Push Docker Images

### Step 1: Build Backend Agent Image
```bash
cd backend

# Build the image
docker build -t polyglot-agent:latest .

# Tag for Docker Hub
docker tag polyglot-agent:latest ${DOCKER_HUB_USERNAME}/polyglot-agent:latest

# Push to Docker Hub
docker push ${DOCKER_HUB_USERNAME}/polyglot-agent:latest

# Also create a versioned tag
docker tag polyglot-agent:latest ${DOCKER_HUB_USERNAME}/polyglot-agent:v1.0.0
docker push ${DOCKER_HUB_USERNAME}/polyglot-agent:v1.0.0
Step 2: Build Frontend Image
bashcd ../frontend

# Build the image
docker build -t polyglot-frontend:latest .

# Tag for Docker Hub
docker tag polyglot-frontend:latest ${DOCKER_HUB_USERNAME}/polyglot-frontend:latest

# Push to Docker Hub
docker push ${DOCKER_HUB_USERNAME}/polyglot-frontend:latest

# Also create a versioned tag
docker tag polyglot-frontend:latest ${DOCKER_HUB_USERNAME}/polyglot-frontend:v1.0.0
docker push ${DOCKER_HUB_USERNAME}/polyglot-frontend:v1.0.0
Step 3: Test Images Locally
bashcd ..

# Run docker-compose to test
docker-compose up -d

# Check logs
docker-compose logs -f

# Test endpoints
curl http://localhost:7860/health

# Stop when done
docker-compose down
Phase 2: Deploy AWS Infrastructure
Step 1: Prepare Terraform Variables
bashcd terraform

# Create terraform.tfvars file
cat > terraform.tfvars <<EOF
# Basic Configuration
project_name = "polyglot-rag"
environment = "production"
aws_region = "us-east-1"
domain_name = "${DOMAIN_NAME}"

# Docker Configuration
docker_hub_username = "${DOCKER_HUB_USERNAME}"
agent_image_tag = "v1.0.0"
frontend_image_tag = "v1.0.0"

# API Keys
livekit_url = "${LIVEKIT_URL}"
livekit_api_key = "${LIVEKIT_API_KEY}"
livekit_api_secret = "${LIVEKIT_API_SECRET}"
openai_api_key = "${OPENAI_API_KEY}"
deepgram_api_key = "${DEEPGRAM_API_KEY}"
cartesia_api_key = "${CARTESIA_API_KEY}"
amadeus_client_id = "${AMADEUS_CLIENT_ID}"
amadeus_client_secret = "${AMADEUS_CLIENT_SECRET}"
serpapi_api_key = "${SERPAPI_API_KEY}"

# Monitoring
alert_email = "${ALERT_EMAIL}"

# Optional: Override defaults
# agent_desired_count = 3
# frontend_desired_count = 2
# db_instance_class = "db.r6g.large"
# redis_node_type = "cache.r6g.large"
EOF
Step 2: Initialize Terraform
bash# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Plan deployment
terraform plan -out=tfplan
Step 3: Deploy Infrastructure
bash# Apply the plan
terraform apply tfplan

# This will take 15-20 minutes
# Save the outputs
terraform output -json > outputs.json
Phase 3: Post-Deployment Configuration
Step 1: Initialize Database
bash# Get database connection details
DB_HOST=$(terraform output -raw database_endpoint | cut -d: -f1)
DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id polyglot-rag-production-db-credentials --query SecretString --output text | jq -r .password)

# Connect to database
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U polyglot -d polyglot_rag

# Run initialization script
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS flight_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    departure_date DATE NOT NULL,
    return_date DATE,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_session ON conversations(session_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_flight_searches_conversation ON flight_searches(conversation_id);

\q
Step 2: Verify Services
bash# Check ECS services
aws ecs list-services --cluster polyglot-rag-production-cluster

# Check service status
aws ecs describe-services \
    --cluster polyglot-rag-production-cluster \
    --services polyglot-rag-production-agent polyglot-rag-production-frontend

# Check ALB health
ALB_DNS=$(terraform output -raw alb_dns_name)
curl -I https://$ALB_DNS/health
Step 3: Configure DNS
bash# This should be done automatically by Terraform
# Verify DNS records
aws route53 list-resource-record-sets \
    --hosted-zone-id $(aws route53 list-hosted-zones --query "HostedZones[?Name=='${DOMAIN_NAME}.'].Id" --output text | cut -d/ -f3)
Step 4: Test Application
bash# Test via domain
curl https://${DOMAIN_NAME}/health

# Open in browser
open https://${DOMAIN_NAME}
Phase 4: LiveKit Agent Deployment
Step 1: Deploy Agent to LiveKit
bashcd ../backend

# Install LiveKit CLI if not already installed
curl -sSL https://get.livekit.io/cli | bash

# Login to LiveKit Cloud
lk cloud login

# Deploy agent
lk cloud agent deploy \
    --project polyglot-rag \
    --entrypoint agent.py

# Monitor deployment
lk cloud logs -f --project polyglot-rag
Step 2: Test LiveKit Connection
bash# Create test room
lk room create test-room --project polyglot-rag

# Generate test token
lk token create \
    --identity test-user \
    --room test-room \
    --project polyglot-rag

# Test connection (use the token in your app)
Phase 5: Monitoring Setup
Step 1: CloudWatch Dashboard
bash# Access dashboard
echo "CloudWatch Dashboard: $(terraform output -raw cloudwatch_dashboard_url)"

# View in browser
open $(terraform output -raw cloudwatch_dashboard_url)
Step 2: Set Up Log Insights Queries
bash# Create useful queries
aws logs put-query-definition \
    --name "Polyglot-RAG-Errors" \
    --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 100' \
    --log-group-names "/ecs/polyglot-rag-production/agent" "/ecs/polyglot-rag-production/frontend"

aws logs put-query-definition \
    --name "Polyglot-RAG-Latency" \
    --query-string 'fields @timestamp, @message | filter @message like /latency/ | stats avg(latency) by bin(5m)' \
    --log-group-names "/ecs/polyglot-rag-production/agent"
Step 3: Test Alerts
bash# Trigger a test alarm
aws cloudwatch set-alarm-state \
    --alarm-name polyglot-rag-production-application-errors \
    --state-value ALARM \
    --state-reason "Testing alert system"

# Check email for alert
Phase 6: Load Testing
Step 1: Create Load Test Script
python# Create file: load_test.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def test_request(session, url):
    start = time.time()
    try:
        async with session.get(f"{url}/health") as response:
            status = response.status
            latency = time.time() - start
            return {"status": status, "latency": latency}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def load_test(url, concurrent_requests, total_requests):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(total_requests):
            if len(tasks) >= concurrent_requests:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                tasks = list(tasks)
            
            tasks.append(asyncio.create_task(test_request(session, url)))
        
        results = await asyncio.gather(*tasks)
    
    # Analyze results
    successful = [r for r in results if r.get("status") == 200]
    failed = [r for r in results if r.get("status") != 200]
    latencies = [r["latency"] for r in successful]
    
    print(f"Total requests: {total_requests}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    if latencies:
        print(f"Average latency: {sum(latencies)/len(latencies):.3f}s")
        print(f"Min latency: {min(latencies):.3f}s")
        print(f"Max latency: {max(latencies):.3f}s")

# Run load test
asyncio.run(load_test("https://your-domain.com", 10, 100))
Step 2: Monitor During Load Test
bash# Watch ECS metrics
watch -n 5 'aws ecs describe-services \
    --cluster polyglot-rag-production-cluster \
    --services polyglot-rag-production-agent polyglot-rag-production-frontend \
    --query "services[*].[serviceName,runningCount,desiredCount]" \
    --output table'

# Watch CloudWatch metrics in real-time
# Use the CloudWatch dashboard
Phase 7: Backup and Disaster Recovery
Step 1: Database Backup
bash# Create manual backup
aws rds create-db-snapshot \
    --db-instance-identifier polyglot-rag-production-postgres \
    --db-snapshot-identifier polyglot-rag-manual-backup-$(date +%Y%m%d-%H%M%S)

# List backups
aws rds describe-db-snapshots \
    --db-instance-identifier polyglot-rag-production-postgres
Step 2: Export Terraform State
bash# Backup state
aws s3 cp \
    s3://polyglot-rag-terraform-state/production/terraform.tfstate \
    ./terraform-state-backup-$(date +%Y%m%d-%H%M%S).tfstate
Rollback Procedures
Quick Rollback to Previous Version
bash# Update task definitions to use previous image tag
cd terraform

# Update terraform.tfvars
sed -i 's/agent_image_tag = "v1.0.0"/agent_image_tag = "v0.9.0"/' terraform.tfvars
sed -i 's/frontend_image_tag = "v1.0.0"/frontend_image_tag = "v0.9.0"/' terraform.tfvars

# Apply changes
terraform plan -target=aws_ecs_task_definition.agent -target=aws_ecs_task_definition.frontend
terraform apply -target=aws_ecs_task_definition.agent -target=aws_ecs_task_definition.frontend

# Force new deployment
aws ecs update-service \
    --cluster polyglot-rag-production-cluster \
    --service polyglot-rag-production-agent \
    --force-new-deployment

aws ecs update-service \
    --cluster polyglot-rag-production-cluster \
    --service polyglot-rag-production-frontend \
    --force-new-deployment
Maintenance Tasks
Daily Tasks

Check CloudWatch dashboard for anomalies
Review error logs
Monitor costs in AWS Cost Explorer

Weekly Tasks

Review and acknowledge alarms
Check for security updates
Analyze performance metrics
Update documentation

Monthly Tasks

Review and optimize costs
Update dependencies
Performance testing
Security audit


#### 5.3 Troubleshooting Guide

**Create file: `deployment/troubleshooting.md`**
```markdown
# Polyglot RAG Troubleshooting Guide

## Common Issues and Solutions

### 1. ECS Tasks Not Starting

#### Symptoms
- Tasks show as "STOPPED" in ECS console
- Services cannot maintain desired count

#### Diagnosis
```bash
# Check stopped tasks
aws ecs list-tasks \
    --cluster polyglot-rag-production-cluster \
    --service-name polyglot-rag-production-agent \
    --desired-status STOPPED

# Get task details
aws ecs describe-tasks \
    --cluster polyglot-rag-production-cluster \
    --tasks <task-arn>

# Check CloudWatch logs
aws logs tail /ecs/polyglot-rag-production/agent --follow
Common Causes and Solutions
1. Image Pull Errors
bash# Verify Docker Hub credentials
docker login

# Check if image exists
docker pull ${DOCKER_HUB_USERNAME}/polyglot-agent:v1.0.0

# Update task definition if needed
aws ecs register-task-definition --cli-input-json file://task-definition.json
2. Missing Environment Variables
bash# Check secrets
aws secretsmanager get-secret-value \
    --secret-id polyglot-rag-production-api-keys \
    --query SecretString --output text | jq .

# Update if needed
aws secretsmanager update-secret \
    --secret-id polyglot-rag-production-api-keys \
    --secret-string file://secrets.json
3. Insufficient Resources
bash# Check cluster capacity
aws ecs describe-clusters \
    --clusters polyglot-rag-production-cluster \
    --query 'clusters[0].statistics'

# Scale up if needed
terraform apply -var="agent_cpu=4096" -var="agent_memory=8192"
2. Load Balancer Health Check Failures
Symptoms

Target showing as "unhealthy" in target group
502/503 errors from ALB

Diagnosis
bash# Check target health
aws elbv2 describe-target-health \
    --target-group-arn $(aws elbv2 describe-target-groups \
        --names polyglot-rag-production-frontend \
        --query 'TargetGroups[0].TargetGroupArn' --output text)

# Check security groups
aws ec2 describe-security-groups \
    --group-ids $(aws ecs describe-services \
        --cluster polyglot-rag-production-cluster \
        --services polyglot-rag-production-frontend \
        --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups' \
        --output text)
Solutions
bash# Fix health check path
aws elbv2 modify-target-group \
    --target-group-arn <arn> \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --healthy-threshold-count 2

# Update security group
aws ec2 authorize-security-group-ingress \
    --group-id <sg-id> \
    --protocol tcp \
    --port 7860 \
    --source-group <alb-sg-id>
3. Database Connection Issues
Symptoms

"Connection refused" errors in logs
Timeout errors

Diagnosis
bash# Test connectivity
aws ec2 describe-vpc-endpoints \
    --filters "Name=vpc-id,Values=<vpc-id>"

# Check RDS status
aws rds describe-db-instances \
    --db-instance-identifier polyglot-rag-production-postgres

# Test from ECS task
aws ecs execute-command \
    --cluster polyglot-rag-production-cluster \
    --task <task-arn> \
    --container agent \
    --interactive \
    --command "/bin/bash"

# In container:
apt-get update && apt-get install -y postgresql-client
psql -h $POSTGRES_HOST -U polyglot -d polyglot_rag
4. High Latency Issues
Symptoms

Slow response times
Timeouts
High CPU/memory usage

Diagnosis
bash# Check metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=polyglot-rag-production-agent \
                 Name=ClusterName,Value=polyglot-rag-production-cluster \
    --statistics Average \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300

# Check application logs for slow queries
aws logs filter-log-events \
    --log-group-name /ecs/polyglot-rag-production/agent \
    --filter-pattern "latency > 1000"
Solutions
bash# Scale up services
aws ecs update-service \
    --cluster polyglot-rag-production-cluster \
    --service polyglot-rag-production-agent \
    --desired-count 5

# Or use auto-scaling
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/polyglot-rag-production-cluster/polyglot-rag-production-agent \
    --policy-name scale-on-cpu \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration file://scaling-policy.json
5. LiveKit Connection Issues
Symptoms

Agent not connecting to LiveKit
WebSocket errors
No audio/video

Diagnosis
bash# Check LiveKit credentials
lk cloud project list

# Test connection
lk room create test-room --project polyglot-rag
lk token create --identity test --room test-room

# Check agent logs
lk cloud logs -f --project polyglot-rag
Solutions
bash# Update LiveKit credentials
aws secretsmanager update-secret \
    --secret-id polyglot-rag-production-api-keys \
    --secret-string '{"LIVEKIT_URL":"wss://new-url.livekit.cloud"}'

# Restart agent
aws ecs update-service \
    --cluster polyglot-rag-production-cluster \
    --service polyglot-rag-production-agent \
    --force-new-deployment
6. Certificate Issues
Symptoms

SSL certificate errors
HTTPS not working

Diagnosis
bash# Check certificate status
aws acm describe-certificate \
    --certificate-arn $(aws acm list-certificates \
        --query "CertificateSummaryList[?DomainName=='${DOMAIN_NAME}'].CertificateArn" \
        --output text)

# Check DNS validation
aws route53 list-resource-record-sets \
    --hosted-zone-id <zone-id> \
    --query "ResourceRecordSets[?Type=='CNAME']"
7. Cost Optimization
High AWS Bills
bash# Analyze costs
aws ce get-cost-and-usage \
    --time-period Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
    --granularity DAILY \
    --metrics "UnblendedCost" \
    --group-by Type=DIMENSION,Key=SERVICE

# Common optimizations:
# 1. Use FARGATE_SPOT for non-critical tasks
terraform apply -var="use_spot_instances=true"

# 2. Reduce idle instances
terraform apply -var="agent_min_count=1" -var="frontend_min_count=1"

# 3. Use smaller instance types in dev
terraform apply -var="environment=dev" -var="db_instance_class=db.t3.medium"
