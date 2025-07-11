"""
Enhanced Streamlit Handler with Action Capture

This module provides an enhanced callback handler that extends the existing StreamlitHandler
functionality with comprehensive action history capture capabilities.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import streamlit as st

from .streamlit_handler import StreamlitHandler
from .clean_response_handler import CleanResponseHandler
from ..action_history.capture import ActionHistoryCapture
from ..utils.session_state_manager import SessionStateManager

logger = logging.getLogger(__name__)


class CompositeCallbackHandler:
    """
    A composite callback handler that combines multiple handlers.
    
    This allows us to chain handlers together so that events are processed
    by multiple handlers in sequence, enabling both UI updates and action capture.
    """
    
    def __init__(self, handlers: List[Any]):
        """
        Initialize the composite handler.
        
        Args:
            handlers: List of callback handlers to chain together
        """
        self.handlers = handlers or []
        logger.debug(f"Initialized CompositeCallbackHandler with {len(self.handlers)} handlers")
    
    def add_handler(self, handler: Any) -> None:
        """
        Add a handler to the chain.
        
        Args:
            handler: Callback handler to add
        """
        self.handlers.append(handler)
        logger.debug(f"Added handler to composite: {type(handler).__name__}")
    
    def __call__(self, **kwargs):
        """
        Process events by calling all handlers in sequence.
        
        Args:
            **kwargs: Event data from the agent
        """
        # Call each handler in sequence
        for handler in self.handlers:
            try:
                if hasattr(handler, '__call__'):
                    handler(**kwargs)
                else:
                    logger.warning(f"Handler {type(handler).__name__} is not callable")
            except Exception as e:
                logger.error(f"Error in handler {type(handler).__name__}: {e}")
                # Continue with other handlers even if one fails


class ActionCaptureHandler:
    """
    A dedicated handler for capturing action events from the Strands agent.
    
    This handler integrates with the ActionHistoryCapture system to process
    callback events and store structured action data in session state.
    """
    
    def __init__(self):
        """Initialize the action capture handler."""
        # Get or create action capture instance from session state
        SessionStateManager.initialize_session_state()
        self.action_capture = SessionStateManager.get_action_capture()
        logger.debug("Initialized ActionCaptureHandler")
    
    def __call__(self, **kwargs):
        """
        Process callback events and capture relevant action data.
        
        Args:
            **kwargs: Event data from the agent
        """
        try:
            # Handle initialization events
            if "init_event_loop" in kwargs:
                self._handle_initialization()
                return
            
            # Handle reasoning events
            if "reasoningText" in kwargs:
                self._handle_reasoning_event(kwargs["reasoningText"])
                return
            
            if "reasoning_signature" in kwargs:
                self._handle_reasoning_end()
                return
            
            # Handle tool events from various sources
            self._handle_tool_events(kwargs)
            
            # Handle message events that may contain tool information
            if "message" in kwargs:
                self._handle_message_event(kwargs["message"])
            
            # Handle direct tool events
            if "tool_use" in kwargs:
                self._handle_direct_tool_use(kwargs["tool_use"])
            
            if "tool_result" in kwargs:
                self._handle_direct_tool_result(kwargs["tool_result"])
            
            # Handle current_tool_use events (common in MCP integrations)
            if "current_tool_use" in kwargs:
                self._handle_current_tool_use(kwargs["current_tool_use"])
                
        except Exception as e:
            logger.error(f"Error in ActionCaptureHandler: {e}")
            # Don't re-raise to avoid breaking the main flow
    
    def _handle_initialization(self):
        """Handle event loop initialization."""
        logger.debug("Action capture: Event loop initialized")
        # The action capture will handle turn management
    
    def _handle_reasoning_event(self, reasoning_data: Any):
        """
        Handle reasoning text events.
        
        Args:
            reasoning_data: Reasoning data from the event
        """
        try:
            self.action_capture.capture_reasoning(reasoning_data)
            logger.debug("Captured reasoning event")
        except Exception as e:
            logger.error(f"Error capturing reasoning event: {e}")
    
    def _handle_reasoning_end(self):
        """Handle the end of reasoning."""
        try:
            self.action_capture.capture_reasoning_end()
            logger.debug("Captured reasoning end")
        except Exception as e:
            logger.error(f"Error capturing reasoning end: {e}")
    
    def _handle_tool_events(self, kwargs: Dict[str, Any]):
        """
        Handle various tool event formats.
        
        Args:
            kwargs: Event data that may contain tool information
        """
        # Check for tool events in content blocks
        if "content_block_start" in kwargs:
            content_block = kwargs["content_block_start"]
            if isinstance(content_block, dict) and "content_block" in content_block:
                block = content_block["content_block"]
                if isinstance(block, dict) and "toolUse" in block:
                    self._handle_tool_use_block(block["toolUse"])
        
        # Check for tool events in various callback formats
        if "event" in kwargs:
            event_data = kwargs["event"]
            if isinstance(event_data, dict):
                if "current_tool_use" in event_data:
                    self._handle_current_tool_use(event_data["current_tool_use"])
                elif "content" in event_data:
                    self._handle_content_blocks(event_data["content"])
    
    def _handle_message_event(self, message_data: Any):
        """
        Handle message events that may contain tool information.
        
        Args:
            message_data: Message data from the event
        """
        try:
            if isinstance(message_data, dict):
                self.action_capture.capture_message_event(message_data)
                logger.debug("Captured message event")
        except Exception as e:
            logger.error(f"Error capturing message event: {e}")
    
    def _handle_direct_tool_use(self, tool_use_data: Any):
        """
        Handle direct tool use events.
        
        Args:
            tool_use_data: Tool use data from the event
        """
        try:
            if isinstance(tool_use_data, dict):
                self.action_capture.capture_tool_use(tool_use_data)
                logger.debug(f"Captured direct tool use: {tool_use_data.get('name', 'unknown')}")
        except Exception as e:
            logger.error(f"Error capturing direct tool use: {e}")
    
    def _handle_direct_tool_result(self, tool_result_data: Any):
        """
        Handle direct tool result events.
        
        Args:
            tool_result_data: Tool result data from the event
        """
        try:
            if isinstance(tool_result_data, dict):
                self.action_capture.capture_tool_result(tool_result_data)
                logger.debug(f"Captured direct tool result: {tool_result_data.get('toolUseId', 'unknown')}")
        except Exception as e:
            logger.error(f"Error capturing direct tool result: {e}")
    
    def _handle_current_tool_use(self, tool_use_data: Any):
        """
        Handle current_tool_use events (common in MCP integrations).
        
        Args:
            tool_use_data: Tool use data from the event
        """
        try:
            if isinstance(tool_use_data, dict):
                self.action_capture.capture_tool_use(tool_use_data)
                logger.debug(f"Captured current tool use: {tool_use_data.get('name', 'unknown')}")
        except Exception as e:
            logger.error(f"Error capturing current tool use: {e}")
    
    def _handle_tool_use_block(self, tool_use_data: Any):
        """
        Handle tool use blocks from content.
        
        Args:
            tool_use_data: Tool use data from content block
        """
        try:
            if isinstance(tool_use_data, dict):
                self.action_capture.capture_tool_use(tool_use_data)
                logger.debug(f"Captured tool use block: {tool_use_data.get('name', 'unknown')}")
        except Exception as e:
            logger.error(f"Error capturing tool use block: {e}")
    
    def _handle_content_blocks(self, content_data: Any):
        """
        Handle content blocks that may contain tool information.
        
        Args:
            content_data: Content data that may contain tool blocks
        """
        try:
            if isinstance(content_data, list):
                for block in content_data:
                    if isinstance(block, dict):
                        if "toolUse" in block:
                            self.action_capture.capture_tool_use(block["toolUse"])
                        elif "toolResult" in block:
                            self.action_capture.capture_tool_result(block["toolResult"])
        except Exception as e:
            logger.error(f"Error handling content blocks: {e}")


class EnhancedStreamlitHandler:
    """
    Enhanced Streamlit handler that combines existing UI functionality with action capture.
    
    This handler extends the existing StreamlitHandler or CleanResponseHandler with
    comprehensive action history capture while maintaining full compatibility with
    existing functionality.
    """
    
    def __init__(self, 
                 placeholder, 
                 update_interval: float = 0.1,
                 use_clean_handler: bool = True):
        """
        Initialize the enhanced handler.
        
        Args:
            placeholder: Streamlit placeholder for displaying content
            update_interval: Time between UI updates (seconds)
            use_clean_handler: Whether to use CleanResponseHandler (True) or StreamlitHandler (False)
        """
        self.placeholder = placeholder
        self.update_interval = update_interval
        self.use_clean_handler = use_clean_handler
        
        # Create the primary UI handler
        if use_clean_handler:
            self.ui_handler = CleanResponseHandler(
                placeholder=placeholder,
                update_interval=update_interval
            )
        else:
            self.ui_handler = StreamlitHandler(
                placeholder=placeholder,
                update_interval=update_interval
            )
        
        # Create the action capture handler
        self.action_handler = ActionCaptureHandler()
        
        # Create composite handler
        self.composite_handler = CompositeCallbackHandler([
            self.ui_handler,
            self.action_handler
        ])
        
        logger.info(f"Initialized EnhancedStreamlitHandler with {'CleanResponseHandler' if use_clean_handler else 'StreamlitHandler'}")
    
    def __call__(self, **kwargs):
        """
        Process events using the composite handler.
        
        Args:
            **kwargs: Event data from the agent
        """
        self.composite_handler(**kwargs)
    
    @property
    def final_response(self) -> Optional[str]:
        """
        Get the final response text from the UI handler.
        
        Returns:
            Optional[str]: Final response text if available
        """
        if hasattr(self.ui_handler, 'final_response'):
            return self.ui_handler.final_response
        return None
    
    def get_action_summary(self) -> Dict[str, Any]:
        """
        Get a summary of captured actions.
        
        Returns:
            Dict[str, Any]: Action summary from the action capture handler
        """
        try:
            return self.action_handler.action_capture.get_action_summary()
        except Exception as e:
            logger.error(f"Error getting action summary: {e}")
            return {}
    
    def start_new_turn(self) -> None:
        """Start a new conversation turn for action tracking."""
        try:
            self.action_handler.action_capture.start_new_turn()
            SessionStateManager.increment_turn()
            logger.debug("Started new turn in enhanced handler")
        except Exception as e:
            logger.error(f"Error starting new turn: {e}")


def create_enhanced_handler(placeholder, 
                          update_interval: float = 0.1,
                          use_clean_handler: bool = True) -> EnhancedStreamlitHandler:
    """
    Factory function to create an enhanced Streamlit handler.
    
    Args:
        placeholder: Streamlit placeholder for displaying content
        update_interval: Time between UI updates (seconds)
        use_clean_handler: Whether to use CleanResponseHandler (True) or StreamlitHandler (False)
        
    Returns:
        EnhancedStreamlitHandler: Configured enhanced handler
    """
    return EnhancedStreamlitHandler(
        placeholder=placeholder,
        update_interval=update_interval,
        use_clean_handler=use_clean_handler
    )