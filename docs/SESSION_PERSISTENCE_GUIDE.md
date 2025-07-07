# LiveKit Agent Session Persistence Implementation Guide

## Overview

This document details the implementation of session persistence for LiveKit agents, allowing users to maintain their conversation context across browser refreshes, network disconnections, and temporary disruptions. This guide covers both the current in-memory implementation and potential Redis-based improvements.

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Current Implementation](#current-implementation)
3. [Technical Architecture](#technical-architecture)
4. [Key Challenges and Solutions](#key-challenges-and-solutions)
5. [Testing Session Persistence](#testing-session-persistence)
6. [Redis-Based Improvements](#redis-based-improvements)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Problem Statement

In real-time voice applications, users frequently experience:
- Browser tab refreshes (accidental or intentional)
- Network connectivity issues
- Browser crashes
- Device switching

Without session persistence, these disruptions result in:
- Lost conversation context
- Repeated introductions
- Frustrated users having to restart conversations
- Poor user experience in production environments

## Current Implementation

### In-Memory Session Tracking

Our implementation uses a global dictionary to track participant sessions outside of the AgentSession lifecycle:

```python
# Global dictionary to store session state outside of AgentSession
# This enables persistence across disconnections
PARTICIPANT_SESSIONS: Dict[str, Dict] = {}
```

Each session stores:
- `joined_at`: Initial connection timestamp
- `last_seen`: Most recent activity timestamp
- `reconnect_count`: Number of reconnections
- `language`: User's preferred language
- `conversation_context`: (optional) Recent conversation history

### Browser-Side Identity Persistence

Participant identity is persisted using localStorage to ensure consistent identity across page reloads:

```javascript
// Get or create persistent participant identity
let participantIdentity = localStorage.getItem('participantIdentity');
if (!participantIdentity) {
    participantIdentity = `user-${Date.now()}`;
    localStorage.setItem('participantIdentity', participantIdentity);
}
```

### Event Handler Architecture

Session persistence is managed through LiveKit room event handlers:

```python
@ctx.room.on("participant_connected")
def on_participant_connected(participant: rtc.RemoteParticipant):
    """Handle new and returning participants - SYNC callback"""
    if participant.identity in PARTICIPANT_SESSIONS:
        # Welcome back returning participant
        session_data = PARTICIPANT_SESSIONS[participant.identity]
        reconnect_count = session_data.get('reconnect_count', 0) + 1
        # Send personalized welcome-back message
    else:
        # Initialize new participant session
        PARTICIPANT_SESSIONS[participant.identity] = {
            'joined_at': time.time(),
            'last_seen': time.time(),
            'reconnect_count': 0,
            'language': language
        }
```

## Technical Architecture

### Component Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Browser UI    │────▶│  LiveKit Cloud   │────▶│  Python Agent   │
│  (localStorage) │     │   (WebSocket)    │     │  (In-Memory)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                                                  │
        │                                                  ▼
        │                                         ┌─────────────────┐
        └────────── Persistent Identity ─────────▶│ Session State   │
                                                  │   Dictionary    │
                                                  └─────────────────┘
```

### Session Lifecycle

1. **Initial Connection**
   - Browser generates unique identity (`user-{timestamp}`)
   - Identity stored in localStorage
   - Agent creates session entry in PARTICIPANT_SESSIONS

2. **Active Session**
   - Conversation proceeds normally
   - Session data updated with last_seen timestamps
   - Context accumulates (if implemented)

3. **Disconnection**
   - Participant removed from greeted_participants set
   - Session data retained in memory
   - 5-minute cleanup timer initiated

4. **Reconnection**
   - Same identity retrieved from localStorage
   - Agent detects returning participant
   - Welcome-back message with context continuity

## Key Challenges and Solutions

### Challenge 1: Event Handler Timing

**Problem**: Session variable not accessible in event handlers registered before session creation.

**Solution**: Move event handler registration after session.start():

```python
# Create session first
await session.start(agent=agent, room=ctx.room)

# Then register handlers that need session access
@ctx.room.on("participant_connected")
def on_participant_connected(participant):
    # Now session is accessible via closure
    session.say("Welcome back!")
```

### Challenge 2: Multiple Greetings

**Problem**: Participants receiving duplicate greetings on reconnection.

**Solution**: Track greeted participants and clear on disconnect:

```python
# On disconnect, remove from greeted set
greeted_participants.discard(participant.identity)

# On reconnect, check if already greeted
if participant.identity not in greeted_participants:
    greeted_participants.add(participant.identity)
    # Send welcome message
```

### Challenge 3: Version Compatibility

**Problem**: LiveKit v1.1.5+ requires synchronous event handlers.

**Solution**: Use sync handlers with async inner functions:

```python
@ctx.room.on("participant_connected")
def on_participant_connected(participant):  # SYNC
    async def handle_async():  # ASYNC inner function
        await asyncio.sleep(1.5)
        session.say("Welcome!")
    
    asyncio.create_task(handle_async())
```

### Challenge 4: Memory Cleanup

**Problem**: Memory leaks from abandoned sessions.

**Solution**: Automatic cleanup after inactivity:

```python
async def cleanup_old_session():
    await asyncio.sleep(300)  # 5 minutes
    if identity in PARTICIPANT_SESSIONS:
        if time.time() - last_seen > 299:
            del PARTICIPANT_SESSIONS[identity]
```

## Testing Session Persistence

### Manual Testing Steps

1. **Initial Connection Test**
   ```bash
   # Start agent
   python agent.py
   
   # Connect via browser
   # Verify initial greeting
   ```

2. **Soft Disconnect Test**
   - Click disconnect button
   - Wait 3 seconds
   - Reconnect
   - Verify: "Welcome back!" message

3. **Browser Refresh Test**
   - Press F5/Cmd+R
   - Verify same identity maintained
   - Verify welcome-back message

4. **Network Interruption Test**
   - Disable WiFi for 10 seconds
   - Re-enable
   - Verify automatic reconnection

5. **Long Disconnect Test**
   - Disconnect for 4 minutes
   - Reconnect (should work)
   - Disconnect for 6 minutes
   - Reconnect (should be new session)

### Automated Testing

```python
async def test_session_persistence():
    # Simulate participant connection
    participant = MockParticipant("user-123")
    on_participant_connected(participant)
    
    # Verify session created
    assert "user-123" in PARTICIPANT_SESSIONS
    
    # Simulate disconnect
    on_participant_disconnected(participant)
    
    # Verify session retained
    assert "user-123" in PARTICIPANT_SESSIONS
    
    # Simulate reconnect
    on_participant_connected(participant)
    
    # Verify reconnect count
    assert PARTICIPANT_SESSIONS["user-123"]["reconnect_count"] == 1
```

## Redis-Based Improvements

### Why Redis?

Current limitations of in-memory storage:
- Lost on agent restart
- Not shared across multiple agent instances
- Limited to single process
- No persistence across deployments

Redis provides:
- Persistent storage with configurable TTL
- Shared state across multiple agents
- Atomic operations for race condition prevention
- Pub/sub for real-time updates

### Redis Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Agent 1    │     │   Agent 2    │     │   Agent 3    │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                     │                     │
       └─────────────────────┴─────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Redis Cluster │
                    │                 │
                    │  Sessions DB    │
                    │  Pub/Sub Chan   │
                    └─────────────────┘
```

### Redis Implementation

```python
import redis
import json
from typing import Optional

class RedisSessionStore:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.pubsub = self.redis_client.pubsub()
        self.session_prefix = "livekit:session:"
        self.ttl = 300  # 5 minutes
        
    async def get_session(self, participant_id: str) -> Optional[Dict]:
        """Retrieve session data from Redis"""
        key = f"{self.session_prefix}{participant_id}"
        data = await self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set_session(self, participant_id: str, session_data: Dict):
        """Store session data with TTL"""
        key = f"{self.session_prefix}{participant_id}"
        await self.redis_client.setex(
            key, 
            self.ttl, 
            json.dumps(session_data)
        )
        
    async def update_session(self, participant_id: str, updates: Dict):
        """Atomic session update"""
        key = f"{self.session_prefix}{participant_id}"
        
        # Use Redis transaction for atomic update
        async with self.redis_client.pipeline() as pipe:
            pipe.watch(key)
            current = await pipe.get(key)
            
            if current:
                session_data = json.loads(current)
                session_data.update(updates)
                
                pipe.multi()
                pipe.setex(key, self.ttl, json.dumps(session_data))
                await pipe.execute()
    
    async def extend_ttl(self, participant_id: str):
        """Extend session TTL on activity"""
        key = f"{self.session_prefix}{participant_id}"
        await self.redis_client.expire(key, self.ttl)
    
    async def publish_event(self, event_type: str, data: Dict):
        """Publish session events for other agents"""
        channel = f"session_events:{event_type}"
        await self.redis_client.publish(
            channel, 
            json.dumps(data)
        )
    
    async def subscribe_to_events(self, event_type: str, callback):
        """Subscribe to session events from other agents"""
        channel = f"session_events:{event_type}"
        await self.pubsub.subscribe(channel)
        
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await callback(data)
```

### Integrating Redis with LiveKit Agent

```python
# Initialize Redis session store
session_store = RedisSessionStore(os.getenv("REDIS_URL"))

@ctx.room.on("participant_connected")
def on_participant_connected(participant: rtc.RemoteParticipant):
    async def handle_participant():
        # Check Redis for existing session
        session_data = await session_store.get_session(participant.identity)
        
        if session_data:
            # Returning participant
            reconnect_count = session_data.get('reconnect_count', 0) + 1
            
            # Update session in Redis
            await session_store.update_session(
                participant.identity,
                {
                    'reconnect_count': reconnect_count,
                    'last_seen': time.time()
                }
            )
            
            # Notify other agents
            await session_store.publish_event('participant_returned', {
                'identity': participant.identity,
                'reconnect_count': reconnect_count
            })
            
            # Welcome back
            message = f"Welcome back! This is visit #{reconnect_count}"
            session.say(message)
        else:
            # New participant
            await session_store.set_session(
                participant.identity,
                {
                    'joined_at': time.time(),
                    'last_seen': time.time(),
                    'reconnect_count': 0,
                    'language': detect_language(participant),
                    'context': {}
                }
            )
    
    asyncio.create_task(handle_participant())
```

### Advanced Redis Features

#### 1. Conversation Context Storage

```python
async def store_conversation_turn(participant_id: str, role: str, message: str):
    """Store conversation history in Redis list"""
    key = f"conversation:{participant_id}"
    turn = {
        'role': role,
        'message': message,
        'timestamp': time.time()
    }
    
    # Store in Redis list with trimming
    await redis_client.lpush(key, json.dumps(turn))
    await redis_client.ltrim(key, 0, 99)  # Keep last 100 turns
    await redis_client.expire(key, 3600)  # 1 hour TTL

async def get_conversation_context(participant_id: str, num_turns: int = 10):
    """Retrieve recent conversation history"""
    key = f"conversation:{participant_id}"
    turns = await redis_client.lrange(key, 0, num_turns - 1)
    return [json.loads(turn) for turn in turns]
```

#### 2. Distributed Lock for Session Updates

```python
async def update_session_with_lock(participant_id: str, updates: Dict):
    """Update session with distributed lock"""
    lock_key = f"lock:session:{participant_id}"
    
    # Acquire lock with timeout
    lock = await redis_client.set(
        lock_key, 
        "locked", 
        nx=True, 
        ex=5  # 5 second timeout
    )
    
    if lock:
        try:
            # Perform update
            await session_store.update_session(participant_id, updates)
        finally:
            # Release lock
            await redis_client.delete(lock_key)
    else:
        # Lock acquisition failed
        raise Exception("Could not acquire session lock")
```

#### 3. Session Analytics

```python
async def track_session_metrics(participant_id: str, event: str):
    """Track session metrics in Redis"""
    # Daily active users
    today = datetime.now().strftime("%Y-%m-%d")
    await redis_client.sadd(f"active_users:{today}", participant_id)
    
    # Session events counter
    await redis_client.hincrby(
        f"session_metrics:{participant_id}", 
        event, 
        1
    )
    
    # Global metrics
    await redis_client.hincrby("global_metrics", event, 1)

async def get_session_analytics(participant_id: str) -> Dict:
    """Retrieve session analytics"""
    metrics = await redis_client.hgetall(f"session_metrics:{participant_id}")
    return {k.decode(): int(v) for k, v in metrics.items()}
```

### Redis Deployment Considerations

#### 1. Connection Pooling

```python
# Use connection pool for better performance
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50
)
redis_client = redis.Redis(connection_pool=pool)
```

#### 2. Redis Sentinel for High Availability

```python
from redis.sentinel import Sentinel

sentinels = [
    ('sentinel1.example.com', 26379),
    ('sentinel2.example.com', 26379),
    ('sentinel3.example.com', 26379),
]

sentinel = Sentinel(sentinels)
redis_client = sentinel.master_for('mymaster', socket_timeout=0.1)
```

#### 3. Redis Cluster for Scaling

```python
from rediscluster import RedisCluster

startup_nodes = [
    {"host": "redis1.example.com", "port": "7000"},
    {"host": "redis2.example.com", "port": "7000"},
    {"host": "redis3.example.com", "port": "7000"},
]

redis_client = RedisCluster(
    startup_nodes=startup_nodes,
    decode_responses=True
)
```

## Best Practices

### 1. Session Data Structure

Keep session data minimal and structured:

```python
SESSION_SCHEMA = {
    'identity': str,           # Unique participant ID
    'joined_at': float,        # Unix timestamp
    'last_seen': float,        # Unix timestamp
    'reconnect_count': int,    # Number of reconnections
    'language': str,           # User's preferred language
    'metadata': dict,          # User-provided metadata
    'context': {
        'last_query': str,     # Last user query
        'last_response': str,  # Last agent response
        'preferences': dict,   # User preferences
    }
}
```

### 2. TTL Management

Implement intelligent TTL based on user activity:

```python
def calculate_ttl(session_data: Dict) -> int:
    """Dynamic TTL based on user engagement"""
    reconnect_count = session_data.get('reconnect_count', 0)
    
    if reconnect_count == 0:
        return 300  # 5 minutes for new users
    elif reconnect_count < 3:
        return 600  # 10 minutes for returning users
    else:
        return 1800  # 30 minutes for frequent users
```

### 3. Error Handling

Implement graceful fallbacks:

```python
async def get_session_safe(participant_id: str) -> Optional[Dict]:
    """Get session with fallback to in-memory"""
    try:
        # Try Redis first
        return await session_store.get_session(participant_id)
    except redis.RedisError:
        # Fallback to in-memory
        logger.warning("Redis unavailable, using in-memory fallback")
        return PARTICIPANT_SESSIONS.get(participant_id)
```

### 4. Security Considerations

- **Encryption**: Encrypt sensitive session data before storing
- **Access Control**: Use Redis ACLs to limit access
- **Data Minimization**: Don't store unnecessary personal data
- **Audit Logging**: Log all session access for compliance

```python
from cryptography.fernet import Fernet

class EncryptedSessionStore(RedisSessionStore):
    def __init__(self, redis_url: str, encryption_key: bytes):
        super().__init__(redis_url)
        self.cipher = Fernet(encryption_key)
    
    async def set_session(self, participant_id: str, session_data: Dict):
        """Store encrypted session data"""
        encrypted = self.cipher.encrypt(
            json.dumps(session_data).encode()
        )
        key = f"{self.session_prefix}{participant_id}"
        await self.redis_client.setex(key, self.ttl, encrypted)
    
    async def get_session(self, participant_id: str) -> Optional[Dict]:
        """Retrieve and decrypt session data"""
        key = f"{self.session_prefix}{participant_id}"
        encrypted = await self.redis_client.get(key)
        if encrypted:
            decrypted = self.cipher.decrypt(encrypted)
            return json.loads(decrypted)
        return None
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Session Not Persisting

**Symptoms**: User gets new greeting after refresh

**Diagnosis Steps**:
```bash
# Check browser console
localStorage.getItem('participantIdentity')

# Check agent logs
grep "Participant connected" agent.log
grep "PARTICIPANT_SESSIONS" agent.log
```

**Common Causes**:
- localStorage cleared/disabled
- Different subdomain/protocol
- Incognito/private browsing

#### 2. Welcome Message Not Speaking

**Symptoms**: Log shows welcome-back but no audio

**Solutions**:
- Ensure event handlers registered after session.start()
- Check session.say() is called in correct context
- Verify TTS service is initialized

#### 3. Memory Leaks

**Symptoms**: Growing memory usage over time

**Prevention**:
```python
# Monitor session count
async def monitor_sessions():
    while True:
        count = len(PARTICIPANT_SESSIONS)
        memory = psutil.Process().memory_info().rss / 1024 / 1024
        logger.info(f"Sessions: {count}, Memory: {memory:.2f}MB")
        await asyncio.sleep(60)

# Aggressive cleanup for production
async def cleanup_stale_sessions():
    while True:
        now = time.time()
        to_remove = []
        
        for identity, session in PARTICIPANT_SESSIONS.items():
            if now - session['last_seen'] > 300:  # 5 minutes
                to_remove.append(identity)
        
        for identity in to_remove:
            del PARTICIPANT_SESSIONS[identity]
            logger.info(f"Cleaned up stale session: {identity}")
        
        await asyncio.sleep(60)  # Run every minute
```

### Debug Logging

Enable comprehensive logging for troubleshooting:

```python
# Session event logging
@ctx.room.on("participant_connected")
def on_participant_connected(participant):
    logger.info(f"""
    ========== PARTICIPANT CONNECTED ==========
    Identity: {participant.identity}
    Metadata: {participant.metadata}
    Sessions Count: {len(PARTICIPANT_SESSIONS)}
    Is Returning: {participant.identity in PARTICIPANT_SESSIONS}
    ==========================================
    """)
```

### Performance Monitoring

Track session persistence metrics:

```python
from prometheus_client import Counter, Gauge, Histogram

# Metrics
session_connections = Counter('session_connections_total', 'Total session connections')
session_reconnections = Counter('session_reconnections_total', 'Total session reconnections')
active_sessions = Gauge('active_sessions', 'Current active sessions')
session_duration = Histogram('session_duration_seconds', 'Session duration')

# Update metrics in handlers
@ctx.room.on("participant_connected")
def on_participant_connected(participant):
    session_connections.inc()
    if participant.identity in PARTICIPANT_SESSIONS:
        session_reconnections.inc()
    active_sessions.set(len(PARTICIPANT_SESSIONS))
```

## Future Enhancements

### 1. Multi-Device Sessions

Allow users to switch between devices:

```python
class MultiDeviceSession:
    def __init__(self):
        self.devices = {}  # device_id -> device_info
        self.primary_device = None
        self.sync_enabled = True
    
    async def add_device(self, device_id: str, device_info: Dict):
        """Register new device for session"""
        self.devices[device_id] = {
            **device_info,
            'last_seen': time.time(),
            'is_active': True
        }
        
        # Sync session to new device
        if self.sync_enabled:
            await self.sync_to_device(device_id)
```

### 2. Session Migration

Support for migrating sessions between agents:

```python
async def migrate_session(
    participant_id: str, 
    from_agent: str, 
    to_agent: str
):
    """Migrate session between agents"""
    # Export session from source
    session_data = await export_session(participant_id, from_agent)
    
    # Import to target
    await import_session(participant_id, to_agent, session_data)
    
    # Notify user
    await notify_migration(participant_id, to_agent)
```

### 3. AI-Powered Context Summarization

Use LLM to summarize long conversations:

```python
async def summarize_context(conversation_history: List[Dict]) -> str:
    """Generate concise summary of conversation"""
    prompt = "Summarize this conversation in 2-3 sentences..."
    # Call LLM API
    summary = await llm.generate(prompt, conversation_history)
    return summary
```

## Conclusion

Session persistence is crucial for production-ready LiveKit agents. While the in-memory implementation provides a solid foundation, Redis-based solutions offer superior scalability, reliability, and feature richness. The key to success is:

1. Start simple with in-memory storage
2. Add Redis when you need multi-instance support
3. Monitor and optimize based on real usage patterns
4. Always have fallback mechanisms
5. Keep session data minimal and secure

By following this guide, you can build robust session persistence that enhances user experience and enables continuous, context-aware conversations across any disruption.