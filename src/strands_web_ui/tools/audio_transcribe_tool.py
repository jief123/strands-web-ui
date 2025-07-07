"""
Audio transcription tool for Strands agents.

This tool allows agents to transcribe MP3 and WAV audio files using AWS Transcribe
with automatic language detection.
"""

import asyncio
import logging
from typing import Dict, Any, List
from strands import tool
from strands_web_ui.utils.audio_transcriber import create_transcriber, TranscriptionResult

logger = logging.getLogger(__name__)

@tool
async def transcribe_audio_file(file_path: str, 
                              language_options: List[str] = None,
                              region: str = "ap-southeast-1") -> Dict[str, Any]:
    """
    Transcribe an MP3 or WAV audio file using AWS Transcribe with automatic language detection.
    
    This tool supports automatic detection between Indonesian (id-ID) and English (en-US).
    
    Args:
        file_path: Path to the MP3 or WAV audio file to transcribe
        language_options: List of language codes to consider (default: ["en-US", "id-ID"])
        region: AWS region for Transcribe service (default: "ap-southeast-1")
        
    Returns:
        Dictionary containing:
        - transcript: The transcribed text
        - language_code: Detected language code
        - confidence: Confidence score (if available)
        - segments: List of transcript segments with timing info
        - status: "success" or "error"
        - message: Status message
    """
    try:
        # Set default language options
        if language_options is None:
            language_options = ["en-US", "id-ID"]
        
        # Create transcriber
        transcriber = create_transcriber(region=region)
        
        # Read the audio file
        try:
            with open(file_path, "rb") as f:
                audio_data = f.read()
        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"Audio file not found: {file_path}",
                "transcript": "",
                "language_code": None,
                "confidence": None,
                "segments": []
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error reading audio file: {str(e)}",
                "transcript": "",
                "language_code": None,
                "confidence": None,
                "segments": []
            }
        
        # Determine file type and transcribe
        logger.info(f"Starting transcription of {file_path}")
        
        # Check file extension to determine format
        file_extension = file_path.lower().split('.')[-1]
        
        if file_extension == 'mp3':
            result = await transcriber.transcribe_mp3_file(audio_data, language_options)
        elif file_extension == 'wav':
            result = await transcriber.transcribe_wav_file(audio_data, language_options)
        else:
            return {
                "status": "error",
                "message": f"Unsupported file format: {file_extension}. Supported formats: mp3, wav",
                "transcript": "",
                "language_code": None,
                "confidence": None,
                "segments": []
            }
        
        # Format the response
        response = {
            "status": "success",
            "message": f"Successfully transcribed {file_extension.upper()} audio file. Detected language: {result.language_code}",
            "transcript": result.transcript,
            "language_code": result.language_code,
            "confidence": result.confidence,
            "segments": result.segments
        }
        
        logger.info(f"Transcription completed successfully. Language: {result.language_code}")
        return response
        
    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "transcript": "",
            "language_code": None,
            "confidence": None,
            "segments": []
        }

@tool
def get_supported_languages() -> Dict[str, Any]:
    """
    Get the list of supported languages for audio transcription.
    
    Returns:
        Dictionary containing supported language codes and their descriptions
    """
    return {
        "status": "success",
        "supported_languages": {
            "en-US": "English (United States)",
            "id-ID": "Indonesian (Indonesia)",
            "zh-CN": "Chinese (Simplified)",
            "ja-JP": "Japanese",
            "ko-KR": "Korean",
            "th-TH": "Thai",
            "vi-VN": "Vietnamese"
        },
        "supported_formats": ["mp3", "wav"],
        "default_options": ["en-US", "id-ID"],
        "message": "These are the supported languages and formats for audio transcription"
    }

# Synchronous wrapper for compatibility
@tool
def transcribe_audio_file_sync(file_path: str, 
                             language_options: List[str] = None,
                             region: str = "ap-southeast-1") -> Dict[str, Any]:
    """
    Synchronous wrapper for transcribe_audio_file.
    
    Args:
        file_path: Path to the MP3 or WAV audio file to transcribe
        language_options: List of language codes to consider
        region: AWS region for Transcribe service
        
    Returns:
        Dictionary with transcription results
    """
    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            transcribe_audio_file(file_path, language_options, region)
        )
        loop.close()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Synchronous transcription failed: {str(e)}",
            "transcript": "",
            "language_code": None,
            "confidence": None,
            "segments": []
        }
