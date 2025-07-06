#!/usr/bin/env python3
"""
Audio utilities for resampling and format conversion
Fixes sample rate mismatch between TTS (24kHz) and WebRTC (48kHz)
"""
import numpy as np
from scipy import signal
from livekit import rtc
import logging

logger = logging.getLogger(__name__)


def resample_audio(audio_data: bytes, original_rate: int = 24000, target_rate: int = 48000) -> bytes:
    """
    Resample audio from original_rate to target_rate
    
    Args:
        audio_data: Raw audio bytes (int16 format)
        original_rate: Original sample rate (Hz)
        target_rate: Target sample rate (Hz)
    
    Returns:
        Resampled audio bytes (int16 format)
    """
    # Convert bytes to numpy array
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    # Convert to float for resampling
    audio_float = audio_array.astype(np.float32) / 32768.0
    
    # Calculate new length
    new_length = int(len(audio_float) * target_rate / original_rate)
    
    # Resample using scipy
    resampled = signal.resample(audio_float, new_length)
    
    # Convert back to int16
    resampled_int16 = (resampled * 32767).astype(np.int16)
    
    logger.debug(
        f"Resampled audio: {original_rate}Hz → {target_rate}Hz, "
        f"{len(audio_array)} → {len(resampled_int16)} samples"
    )
    
    return resampled_int16.tobytes()


def create_audio_frame_48khz(audio_data: bytes, duration_ms: int = 10) -> rtc.AudioFrame:
    """
    Create a properly formatted audio frame at 48kHz
    
    Args:
        audio_data: Raw audio bytes at 48kHz
        duration_ms: Frame duration in milliseconds (default 10ms)
    
    Returns:
        AudioFrame configured for 48kHz mono
    """
    samples_per_channel = int(48000 * duration_ms / 1000)  # 480 for 10ms
    
    return rtc.AudioFrame(
        data=audio_data,
        sample_rate=48000,
        num_channels=1,
        samples_per_channel=samples_per_channel
    )


def chunk_audio_data(audio_data: bytes, chunk_duration_ms: int = 10, sample_rate: int = 48000) -> list[bytes]:
    """
    Split audio data into chunks of specified duration
    
    Args:
        audio_data: Raw audio bytes
        chunk_duration_ms: Duration of each chunk in milliseconds
        sample_rate: Sample rate of the audio
    
    Returns:
        List of audio chunks
    """
    # Calculate bytes per chunk (2 bytes per sample for int16)
    bytes_per_sample = 2
    samples_per_chunk = int(sample_rate * chunk_duration_ms / 1000)
    bytes_per_chunk = samples_per_chunk * bytes_per_sample
    
    chunks = []
    for i in range(0, len(audio_data), bytes_per_chunk):
        chunk = audio_data[i:i + bytes_per_chunk]
        if len(chunk) == bytes_per_chunk:
            chunks.append(chunk)
        elif len(chunk) > 0:
            # Pad the last chunk if needed
            padding = bytes_per_chunk - len(chunk)
            chunk += b'\x00' * padding
            chunks.append(chunk)
    
    return chunks


async def generate_test_tone(
    frequency: float = 440.0,
    duration: float = 1.0,
    sample_rate: int = 48000
) -> bytes:
    """
    Generate a test tone for audio testing
    
    Args:
        frequency: Tone frequency in Hz (default 440Hz = A4)
        duration: Duration in seconds
        sample_rate: Sample rate (should be 48000 for WebRTC)
    
    Returns:
        Audio data as bytes
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Apply envelope to avoid clicks
    envelope = np.ones_like(audio_data)
    fade_samples = int(0.01 * sample_rate)  # 10ms fade
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    audio_data *= envelope
    
    # Convert to int16
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    logger.info(f"Generated {duration}s test tone at {frequency}Hz, {sample_rate}Hz sample rate")
    
    return audio_int16.tobytes()


class AudioFrameBuffer:
    """Buffer for accumulating audio data and creating frames"""
    
    def __init__(self, sample_rate: int = 48000, frame_duration_ms: int = 10):
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.samples_per_frame = int(sample_rate * frame_duration_ms / 1000)
        self.bytes_per_frame = self.samples_per_frame * 2  # 2 bytes per int16 sample
        self.buffer = bytearray()
    
    def add_data(self, data: bytes) -> list[rtc.AudioFrame]:
        """Add audio data to buffer and return complete frames"""
        self.buffer.extend(data)
        frames = []
        
        while len(self.buffer) >= self.bytes_per_frame:
            frame_data = bytes(self.buffer[:self.bytes_per_frame])
            self.buffer = self.buffer[self.bytes_per_frame:]
            
            frame = rtc.AudioFrame(
                data=frame_data,
                sample_rate=self.sample_rate,
                num_channels=1,
                samples_per_channel=self.samples_per_frame
            )
            frames.append(frame)
        
        return frames
    
    def flush(self) -> list[rtc.AudioFrame]:
        """Flush remaining data as a frame (padded if needed)"""
        frames = []
        if self.buffer:
            # Pad to frame size
            padding = self.bytes_per_frame - len(self.buffer)
            if padding > 0:
                self.buffer.extend(b'\x00' * padding)
            
            frame = rtc.AudioFrame(
                data=bytes(self.buffer),
                sample_rate=self.sample_rate,
                num_channels=1,
                samples_per_channel=self.samples_per_frame
            )
            frames.append(frame)
            self.buffer.clear()
        
        return frames