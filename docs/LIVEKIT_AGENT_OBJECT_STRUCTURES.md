# LiveKit Agent Object Structures Reference

This document provides a comprehensive reference for all object structures used in LiveKit Agents v1.0.23, based on runtime debugging and logging.

## Event Structures

### AgentStateChangedEvent

```python
Type: <class 'livekit.agents.voice.events.AgentStateChangedEvent'>

Attributes:
- old_state: Previous agent state
- new_state: New agent state
- type: Event type identifier

Available states:
- initializing
- listening
- speaking
- thinking

Usage:
@session.on("agent_state_changed")
def on_agent_state_changed(event):
    logger.info(f"State: {event.old_state} -> {event.new_state}")
```

### SpeechCreatedEvent

```python
Type: <class 'livekit.agents.voice.events.SpeechCreatedEvent'>

Attributes:
- source: Source of speech ('say', 'generate_reply', 'tool_response')
- speech_handle: SpeechHandle object
- user_initiated: Boolean indicating if user triggered
- type: Event type identifier

Usage:
@session.on("speech_created")
def on_speech_created(event):
    logger.info(f"Source: {event.source}")
    handle = event.speech_handle  # SpeechHandle object
```

### ConversationItemAddedEvent

```python
Type: <class 'livekit.agents.voice.events.ConversationItemAddedEvent'>

Attributes:
- item: ChatMessage object
- type: Event type identifier

ChatMessage attributes:
- content: Message content
- role: 'user', 'assistant', 'system'
- text_content: Text content of the message
- created_at: Timestamp
- id: Unique identifier
- interrupted: Boolean

Usage:
@session.on("conversation_item_added")
def on_conversation_item_added(event):
    if event.item.role == "assistant":
        logger.info(f"Assistant: {event.item.text_content}")
```

### FunctionToolsExecutedEvent

```python
Type: <class 'livekit.agents.voice.events.FunctionToolsExecutedEvent'>

Attributes:
- function_calls: List of FunctionCall objects
- function_call_outputs: List of FunctionCallOutput objects
- type: Event type identifier
- zipped: Method to iterate both lists together

FunctionCall structure:
- id: Unique identifier
- name: Function name
- arguments: JSON string of arguments
- call_id: Call identifier
- created_at: Timestamp

FunctionCallOutput structure:
- id: Unique identifier
- name: Function name
- output: Function output (JSON string)
- call_id: Matching call identifier
- is_error: Boolean
- created_at: Timestamp

Usage:
@session.on("function_tools_executed")
def on_function_tools_executed(event):
    for call, output in zip(event.function_calls, event.function_call_outputs):
        logger.info(f"Tool: {call.name}")
        logger.info(f"Args: {call.arguments}")
        logger.info(f"Result: {output.output}")
```

## Core Objects

### DataPacket (Room Data)

```python
Type: <class 'livekit.rtc.room.DataPacket'>

Attributes:
- data: bytes - Raw data payload
- participant: RemoteParticipant who sent it
- kind: int - 1 for reliable, 0 for lossy
- topic: str - Optional topic/channel name

Usage:
@ctx.room.on("data_received")
def on_data_received(packet):
    data = packet.data  # bytes
    participant = packet.participant
    message = json.loads(data.decode('utf-8'))
```

### SpeechHandle

```python
Type: <class 'livekit.agents.voice.speech_handle.SpeechHandle'>

Attributes:
- id: Unique identifier
- allow_interruptions: Whether speech can be interrupted
- done: Boolean indicating completion
- interrupted: Boolean indicating if interrupted

Methods:
- wait_for_playout(): Async method to wait for speech completion
- interrupt(): Stop the speech
- add_done_callback(callback): Add completion callback

Constants:
- SPEECH_PRIORITY_HIGH
- SPEECH_PRIORITY_LOW
- SPEECH_PRIORITY_NORMAL

Usage:
speech_handle = await session.generate_reply(
    user_input="Hello",
    allow_interruptions=True
)
await speech_handle.wait_for_playout()
```

## Session Methods

### generate_reply()

```python
async def generate_reply(
    user_input: str,
    instructions: str = None,
    allow_interruptions: bool = True
) -> SpeechHandle:
    """
    Inject text directly into the STT-LLM-TTS pipeline.
    
    Args:
        user_input: Text to inject as if user spoke it
        instructions: Additional LLM guidance (not in history)
        allow_interruptions: Whether user can interrupt response
    
    Returns:
        SpeechHandle for tracking speech completion
    """
```

### say()

```python
def say(
    text: str,
    allow_interruptions: bool = True
) -> None:
    """
    Make the agent speak the given text.
    
    Args:
        text: Text to speak
        allow_interruptions: Whether speech can be interrupted
    """
```

### interrupt()

```python
def interrupt() -> None:
    """Stop any ongoing agent speech."""
```

## Common Patterns

### Text Injection Testing

```python
# Via data channel
test_data = json.dumps({
    "type": "test_user_input",
    "text": "Find flights from NYC to LA",
    "timestamp": int(time.time() * 1000)
}).encode('utf-8')
await room.local_participant.publish_data(test_data, reliable=True)

# Direct injection in agent
speech_handle = await session.generate_reply(
    user_input="Find flights from NYC to LA"
)
await speech_handle.wait_for_playout()
```

### Event Flow for Text Injection

1. Text injected via `generate_reply()`
2. `conversation_item_added` event fires (role="user")
3. Agent processes and may call tools
4. `function_call` event (if tools used)
5. `function_tools_executed` event with results
6. `speech_created` event for response
7. `conversation_item_added` event (role="assistant")
8. `agent_state_changed` events throughout

## Error Handling

### Common Issues and Solutions

1. **AttributeError on event properties**
   - Always check event structure with `dir(event)`
   - Use hasattr() before accessing properties

2. **Speech handle methods**
   - Use `wait_for_playout()` not `wait_for_completion()` or `join()`

3. **Function tools event**
   - Use `event.function_calls` and `event.function_call_outputs`
   - Iterate with `zip()` or use the `zipped` property

## Debugging Tips

### Log Event Structures

```python
@session.on("any_event")
def debug_event(event):
    logger.info(f"Event type: {type(event)}")
    logger.info(f"Attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
    
    # For nested objects
    if hasattr(event, 'item'):
        logger.info(f"Item type: {type(event.item)}")
        logger.info(f"Item attrs: {[attr for attr in dir(event.item) if not attr.startswith('_')]}")
```

### Check Available Events

```python
# List all events a session can handle
for attr in dir(session):
    if attr.startswith('on_'):
        print(f"Event: {attr}")
```

## Version Notes

This documentation is based on LiveKit Agents v1.0.23. Different versions may have different APIs:
- v1.0.x: Stable API as documented here
- v1.1.x: May have breaking changes, particularly in audio handling