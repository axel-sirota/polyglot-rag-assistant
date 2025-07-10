# Things For Production - TTS Improvements

## TTS Formatting Issues

### Current Problem
The TTS (Text-to-Speech) system doesn't handle formatting characters properly:
- Hyphens (-) are not treated as pause indicators
- List items flow together without natural breaks
- Flight information sounds rushed and hard to follow

### Recommended Improvements

#### 1. Add Natural Pauses for Lists
When generating text for TTS, insert pause markers:
- Replace "- " with a slight pause (e.g., add comma or period)
- Add brief pauses between flight options
- Consider SSML (Speech Synthesis Markup Language) if supported

#### 2. Format Flight Information for Speech
Current: "United Airlines UA123 - $450 - 10:00 AM"
Better: "United Airlines, flight UA123, costs 450 dollars, departing at 10 AM"

#### 3. Separate Visual and Audio Formatting
- Keep current formatting for chat display (with line breaks)
- Create separate TTS-optimized text without visual formatting
- Remove markdown and special characters before TTS processing

#### 4. Implementation Suggestions

In `agent.py`, modify the `strip_markdown` function or create a new `format_for_tts` function:

```python
def format_for_tts(text: str) -> str:
    """Format text specifically for TTS output"""
    # Replace hyphens with commas for natural pauses
    text = text.replace(' - ', ', ')
    
    # Add pauses after list items
    text = re.sub(r'^- ', '', text, flags=re.MULTILINE)  # Remove list markers
    text = re.sub(r'\n', '. ', text)  # Replace newlines with periods
    
    # Format prices
    text = re.sub(r'\$(\d+)', r'\1 dollars', text)
    
    # Format times
    text = re.sub(r'(\d{1,2}):(\d{2})\s*(AM|PM)', r'\1 \2 \3', text)
    
    # Add pauses before conjunctions
    text = text.replace(' and ', ', and ')
    
    return text
```

#### 5. Consider SSML Support
If the TTS provider supports SSML, use it for better control:
- `<break time="200ms"/>` for short pauses
- `<emphasis>` for important information
- `<say-as interpret-as="currency">$450</say-as>` for prices
- `<say-as interpret-as="time">10:00 AM</say-as>` for times

#### 6. Test Different TTS Voices
Some voices handle punctuation better than others. Test and document which voices work best for:
- Flight listings
- Multi-language support
- Natural conversation flow

## Production Deployment Notes

### Performance Considerations
- Pre-process common TTS phrases to reduce latency
- Cache TTS audio for common responses
- Consider streaming TTS for long responses

### Monitoring
- Log TTS generation times
- Track which formatting causes issues
- Monitor user feedback on voice clarity

### Future Enhancements
- Implement voice speed control
- Add user preferences for voice selection
- Support regional accent preferences
- Implement pronunciation corrections for airline codes