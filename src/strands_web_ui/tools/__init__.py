"""
Custom tools for Strands Web UI.

This package contains custom tools that can be used with Strands agents,
including audio transcription capabilities.
"""

from .audio_transcribe_tool import transcribe_audio_file_sync, get_supported_languages

__all__ = ['transcribe_audio_file_sync', 'get_supported_languages']
