"""
Audio transcription utility for MP3 files using AWS Transcribe.

This module provides functionality to:
- Process MP3 files and convert them to the required format for AWS Transcribe
- Automatically detect language (Indonesian/English)
- Handle both streaming and batch transcription
"""

import asyncio
import io
import logging
import tempfile
import os
from typing import Optional, Dict, Any, List
import boto3
from botocore.exceptions import ClientError

try:
    from pydub import AudioSegment
    from pydub.utils import which
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("pydub not available. Audio conversion features will be limited.")

try:
    from amazon_transcribe.client import TranscribeStreamingClient
    from amazon_transcribe.handlers import TranscriptResultStreamHandler
    from amazon_transcribe.model import TranscriptEvent
    TRANSCRIBE_STREAMING_AVAILABLE = True
except ImportError:
    TRANSCRIBE_STREAMING_AVAILABLE = False
    logging.warning("amazon-transcribe not available. Using batch transcription only.")

logger = logging.getLogger(__name__)

class TranscriptionResult:
    """Container for transcription results."""
    
    def __init__(self):
        self.transcript = ""
        self.language_code = None
        self.confidence = None
        self.segments = []
        self.is_complete = False

class StreamingTranscriptHandler(TranscriptResultStreamHandler):
    """Custom handler for streaming transcription events."""
    
    def __init__(self, stream, result_container: TranscriptionResult):
        super().__init__(stream)
        self.result_container = result_container
        
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """Handle transcript events and update the result container."""
        results = transcript_event.transcript.results
        
        for result in results:
            if result.alternatives:
                alt = result.alternatives[0]
                
                # Update language code if available
                if hasattr(result, 'language_code') and result.language_code:
                    self.result_container.language_code = result.language_code
                
                # Update transcript
                if result.is_partial:
                    # For partial results, we might want to show progress
                    logger.debug(f"Partial transcript: {alt.transcript}")
                else:
                    # Final result
                    self.result_container.transcript += alt.transcript + " "
                    self.result_container.confidence = getattr(alt, 'confidence', None)
                    
                    # Store segment information
                    segment = {
                        'transcript': alt.transcript,
                        'confidence': getattr(alt, 'confidence', None),
                        'start_time': getattr(result, 'start_time', None),
                        'end_time': getattr(result, 'end_time', None)
                    }
                    self.result_container.segments.append(segment)

class AudioTranscriber:
    """Main class for handling audio transcription."""
    
    def __init__(self, region: str = "ap-southeast-1"):
        """
        Initialize the audio transcriber.
        
        Args:
            region: AWS region for Transcribe service
        """
        self.region = region
        self.transcribe_client = boto3.client('transcribe', region_name=region)
        
        # Check if streaming client is available
        if TRANSCRIBE_STREAMING_AVAILABLE:
            self.streaming_client = TranscribeStreamingClient(region=region)
        else:
            self.streaming_client = None
            logger.warning("Streaming transcription not available. Using batch mode only.")
    
    def _convert_mp3_to_wav(self, mp3_data: bytes) -> bytes:
        """
        Convert MP3 data to WAV format suitable for transcription.
        
        Args:
            mp3_data: MP3 file data as bytes
            
        Returns:
            WAV file data as bytes
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub is required for audio conversion. Please install it with: pip install pydub")
        
        # Load MP3 from bytes
        audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
        
        # Convert to the format required by Transcribe
        # 16kHz, mono, 16-bit PCM
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)  # 16-bit
        
        # Export to WAV format
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        
        return wav_buffer.read()
    
    async def transcribe_streaming(self, audio_data: bytes, 
                                 language_options: List[str] = None) -> TranscriptionResult:
        """
        Transcribe audio using streaming API.
        
        Args:
            audio_data: Audio data in bytes (WAV format, 16kHz, mono)
            language_options: List of language codes to consider
            
        Returns:
            TranscriptionResult object
        """
        if not self.streaming_client:
            raise RuntimeError("Streaming transcription not available")
        
        if language_options is None:
            language_options = ["en-US", "id-ID"]  # English and Indonesian
        
        result_container = TranscriptionResult()
        
        try:
            # Start transcription stream
            stream = await self.streaming_client.start_stream_transcription(
                language_code=None,  # Auto-detect
                identify_language=True,
                language_options=language_options,
                media_sample_rate_hz=16000,
                media_encoding="pcm",
                identify_multiple_languages=False,  # Set to True if you want to detect multiple languages
            )
            
            # Create handler
            handler = StreamingTranscriptHandler(stream.output_stream, result_container)
            
            # Send audio data
            async def send_audio():
                # Split audio into chunks for streaming
                chunk_size = 1024 * 8  # 8KB chunks
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    await stream.input_stream.send_audio_event(audio_chunk=chunk)
                    await asyncio.sleep(0.01)  # Small delay to simulate streaming
                
                await stream.input_stream.end_stream()
            
            # Process transcription
            await asyncio.gather(send_audio(), handler.handle_events())
            
            result_container.is_complete = True
            result_container.transcript = result_container.transcript.strip()
            
        except Exception as e:
            logger.error(f"Streaming transcription failed: {str(e)}")
            raise
        
        return result_container
    
    def transcribe_batch(self, audio_data: bytes, 
                        language_options: List[str] = None) -> TranscriptionResult:
        """
        Transcribe audio using batch API (upload to S3 first).
        
        Args:
            audio_data: Audio data in bytes
            language_options: List of language codes to consider
            
        Returns:
            TranscriptionResult object
        """
        if language_options is None:
            language_options = ["en-US", "id-ID"]
        
        result_container = TranscriptionResult()
        
        # This would require S3 upload and is more complex
        # For now, we'll focus on the streaming approach
        raise NotImplementedError("Batch transcription requires S3 setup. Use streaming instead.")
    
    async def transcribe_mp3_file(self, mp3_data: bytes, 
                                language_options: List[str] = None) -> TranscriptionResult:
        """
        Transcribe an MP3 file with automatic language detection.
        
        Args:
            mp3_data: MP3 file data as bytes
            language_options: List of language codes to consider (default: en-US, id-ID)
            
        Returns:
            TranscriptionResult object with transcript and detected language
        """
        try:
            # Convert MP3 to WAV format
            logger.info("Converting MP3 to WAV format...")
            wav_data = self._convert_mp3_to_wav(mp3_data)
            
            # Use streaming transcription if available
            if self.streaming_client:
                logger.info("Starting streaming transcription...")
                result = await self.transcribe_streaming(wav_data, language_options)
            else:
                logger.info("Streaming not available, using batch transcription...")
                result = self.transcribe_batch(wav_data, language_options)
            
            logger.info(f"Transcription completed. Language: {result.language_code}")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

def create_transcriber(region: str = "ap-southeast-1") -> AudioTranscriber:
    """
    Factory function to create an AudioTranscriber instance.
    
    Args:
        region: AWS region for Transcribe service
        
    Returns:
        AudioTranscriber instance
    """
    return AudioTranscriber(region=region)

# Example usage
async def example_usage():
    """Example of how to use the AudioTranscriber."""
    transcriber = create_transcriber()
    
    # Read MP3 file
    with open("example.mp3", "rb") as f:
        mp3_data = f.read()
    
    # Transcribe
    result = await transcriber.transcribe_mp3_file(mp3_data)
    
    print(f"Transcript: {result.transcript}")
    print(f"Language: {result.language_code}")
    print(f"Confidence: {result.confidence}")

if __name__ == "__main__":
    asyncio.run(example_usage())
