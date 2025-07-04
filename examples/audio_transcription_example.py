#!/usr/bin/env python3
"""
Audio Transcription Example

This example demonstrates how to use the audio transcription functionality
with the Strands Web UI.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strands_web_ui.utils.audio_transcriber import create_transcriber
from strands_web_ui.tools.audio_transcribe_tool import transcribe_audio_file_sync, get_supported_languages

async def test_transcription():
    """Test the audio transcription functionality."""
    
    print("🎤 Audio Transcription Test")
    print("=" * 50)
    
    # Test 1: Get supported languages
    print("\n1. Getting supported languages...")
    languages = get_supported_languages()
    print(f"Status: {languages['status']}")
    print("Supported languages:")
    for code, name in languages['supported_languages'].items():
        print(f"  - {code}: {name}")
    
    # Test 2: Test transcription with a sample file (if available)
    sample_file = "sample_audio.mp3"
    
    if os.path.exists(sample_file):
        print(f"\n2. Testing transcription with {sample_file}...")
        
        # Test synchronous transcription
        result = transcribe_audio_file_sync(
            file_path=sample_file,
            language_options=["en-US", "id-ID"],
            region="ap-southeast-1"
        )
        
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Transcript: {result['transcript']}")
            print(f"Language: {result['language_code']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Segments: {len(result['segments'])}")
        else:
            print(f"Error: {result['message']}")
    else:
        print(f"\n2. Sample file {sample_file} not found. Skipping transcription test.")
        print("To test transcription, place an MP3 file named 'sample_audio.mp3' in this directory.")
    
    # Test 3: Test direct transcriber usage
    print("\n3. Testing direct transcriber usage...")
    try:
        transcriber = create_transcriber(region="ap-southeast-1")
        print("✅ Transcriber created successfully")
        print(f"Region: {transcriber.region}")
        print(f"Streaming available: {transcriber.streaming_client is not None}")
    except Exception as e:
        print(f"❌ Error creating transcriber: {e}")

def create_sample_audio_info():
    """Provide information about creating sample audio for testing."""
    
    print("\n" + "=" * 50)
    print("📝 How to create sample audio for testing:")
    print("=" * 50)
    
    print("""
1. Record a short audio message (10-30 seconds) in MP3 format
2. Save it as 'sample_audio.mp3' in the examples directory
3. Try both English and Indonesian content to test language detection

Sample content suggestions:
- English: "Hello, this is a test of the audio transcription system."
- Indonesian: "Halo, ini adalah tes sistem transkripsi audio."

Audio requirements:
- Format: MP3
- Quality: Clear speech, minimal background noise
- Length: 10-60 seconds for testing
- Size: Under 10MB
    """)

if __name__ == "__main__":
    print("Starting audio transcription test...")
    
    try:
        # Run the async test
        asyncio.run(test_transcription())
        
        # Show sample audio info
        create_sample_audio_info()
        
        print("\n✅ Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
