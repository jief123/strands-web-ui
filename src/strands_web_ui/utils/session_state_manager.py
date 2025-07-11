"""
Session State Manager for Strands Web UI

This module provides comprehensive session state management for the action history display feature,
including initialization, turn-based organization, cleanup, and thread-safe access.
"""

import logging
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
import streamlit as st

# Import types only when needed to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..action_history.capture import ActionEvent, ActionHistoryCapture

logger = logging.getLogger(__name__)


class SessionStateManager:
    """
    Manages Streamlit session state for action history and conversation management.
    
    This class provides:
    - Initialization of action history storage in session state
    - Turn-based organization of actions within conversation sessions
    - Session state cleanup when new conversations start
    - Thread-safe access to action history data
    """
    
    # Class-level lock for thread safety
    _lock = threading.RLock()
    
    # Session state keys
    ACTION_HISTORY_KEY = "action_history"
    CURRENT_TURN_KEY = "current_turn"
    ACTION_CAPTURE_KEY = "action_capture"
    SHOW_ACTION_HISTORY_KEY = "show_action_history"
    ACTION_HISTORY_EXPANDED_KEY = "action_history_expanded"
    CONVERSATION_ID_KEY = "conversation_id"
    LAST_CLEANUP_TIME_KEY = "last_cleanup_time"
    
    @classmethod
    def initialize_session_state(cls) -> None:
        """
        Initialize all session state variables for action history.
        
        This method ensures all required session state variables are properly
        initialized with default values if they don't already exist.
        """
        with cls._lock:
            try:
                # Initialize action history storage
                if cls.ACTION_HISTORY_KEY not in st.session_state:
                    st.session_state[cls.ACTION_HISTORY_KEY] = []
                    logger.debug("Initialized action_history in session state")
                
                # Initialize current turn counter
                if cls.CURRENT_TURN_KEY not in st.session_state:
                    st.session_state[cls.CURRENT_TURN_KEY] = 0
                    logger.debug("Initialized current_turn in session state")
                
                # Initialize action capture instance
                if cls.ACTION_CAPTURE_KEY not in st.session_state:
                    # Import here to avoid circular import
                    from ..action_history.capture import ActionHistoryCapture
                    st.session_state[cls.ACTION_CAPTURE_KEY] = ActionHistoryCapture()
                    logger.debug("Initialized action_capture in session state")
                
                # Initialize UI state variables
                if cls.SHOW_ACTION_HISTORY_KEY not in st.session_state:
                    st.session_state[cls.SHOW_ACTION_HISTORY_KEY] = True
                    logger.debug("Initialized show_action_history in session state")
                
                if cls.ACTION_HISTORY_EXPANDED_KEY not in st.session_state:
                    st.session_state[cls.ACTION_HISTORY_EXPANDED_KEY] = False
                    logger.debug("Initialized action_history_expanded in session state")
                
                # Initialize conversation tracking
                if cls.CONVERSATION_ID_KEY not in st.session_state:
                    st.session_state[cls.CONVERSATION_ID_KEY] = cls._generate_conversation_id()
                    logger.debug("Initialized conversation_id in session state")
                
                # Initialize cleanup tracking
                if cls.LAST_CLEANUP_TIME_KEY not in st.session_state:
                    st.session_state[cls.LAST_CLEANUP_TIME_KEY] = datetime.now()
                    logger.debug("Initialized last_cleanup_time in session state")
                
                logger.info("Session state initialization completed successfully")
                
            except Exception as e:
                logger.error(f"Error initializing session state: {e}")
                raise
    
    @classmethod
    def get_action_history(cls) -> List[Any]:
        """
        Get the current action history from session state.
        
        Returns:
            List[ActionEvent]: Current action history
        """
        with cls._lock:
            try:
                cls.initialize_session_state()
                return st.session_state.get(cls.ACTION_HISTORY_KEY, []).copy()
            except Exception as e:
                logger.error(f"Error getting action history: {e}")
                return []
    
    @classmethod
    def set_action_history(cls, actions: List[Any]) -> None:
        """
        Set the action history in session state.
        
        Args:
            actions: List of action events to store
        """
        with cls._lock:
            try:
                cls.initialize_session_state()
                st.session_state[cls.ACTION_HISTORY_KEY] = actions.copy()
                logger.debug(f"Updated action history with {len(actions)} actions")
            except Exception as e:
                logger.error(f"Error setting action history: {e}")
    
    @classmethod
    def add_action(cls, action: Any) -> None:
        """
        Add a single action to the history.
        
        Args:
            action: Action event to add
        """
        with cls._lock:
            try:
                cls.initialize_session_state()
                current_history = st.session_state.get(cls.ACTION_HISTORY_KEY, [])
                current_history.append(action)
                st.session_state[cls.ACTION_HISTORY_KEY] = current_history
                logger.debug(f"Added action: {action.action_type} - {action.tool_name}")
            except Exception as e:
                logger.error(f"Error adding action: {e}")
    
    @classmethod
    def get_current_turn(cls) -> int:
        """
        Get the current conversation turn number.
        
        Returns:
            int: Current turn number
        """
        with cls._lock:
            try:
                cls.initialize_session_state()
                return st.session_state.get(cls.CURRENT_TURN_KEY, 0)
            except Exception as e:
                logger.error(f"Error getting current turn: {e}")
                return 0
    
    @classmethod
    def set_current_turn(cls, turn: int) -> None:
        """
        Set the current conversation turn number.
        
        Args:
            turn: Turn number to set
        """
        with cls._lock:
            try:
                cls.initialize_session_state()
                st.session_state[cls.CURRENT_TURN_KEY] = turn
                logger.debug(f"Set current turn to: {turn}")
            except Exception as e:
                logger.error(f"Error setting current turn: {e}")
    
    @classmethod
    def increment_turn(cls) -> int:
        """
        Increment the current turn and return the new turn number.
        
        Returns:
            int: New turn number
        """
        with cls._lock:
            try:
                cls.initialize_session_state()
                current_turn = st.session_state.get(cls.CURRENT_TURN_KEY, 0)
                new_turn = current_turn + 1
                st.session_state[cls.CURRENT_TURN_KEY] = new_turn
                logger.debug(f"Incremented turn from {current_turn} to {new_turn}")
                return new_turn
            except Exception as e:
                logger.error(f"Error incrementing turn: {e}")
                return 0
    
    @classmethod
    def get_action_capture(cls):
        """
        Get the action capture instance from session state.
        
        Returns:
            ActionHistoryCapture: Action capture instance
        """
        with cls._lock:
            try:
                cls.initialize_session_state()
                return st.session_state.get(cls.ACTION_CAPTURE_KEY)
            except Exception as e:
                logger.error(f"Error getting action capture: {e}")
                # Return a new instance as fallback
                from ..action_history.capture import ActionHistoryCapture
                return ActionHistoryCapture()
    
    @classmethod
    def get_actions_for_turn(cls, turn: int) -> List[Any]:
        """
        Get all actions for a specific conversation turn.
        
        Args:
            turn: Turn number
            
        Returns:
            List[ActionEvent]: Actions for the specified turn
        """
        with cls._lock:
            try:
                actions = cls.get_action_history()
                return [action for action in actions if action.turn == turn]
            except Exception as e:
                logger.error(f"Error getting actions for turn {turn}: {e}")
                return []
    
    @classmethod
    def get_actions_for_current_turn(cls) -> List[Any]:
        """
        Get all actions for the current conversation turn.
        
        Returns:
            List[ActionEvent]: Actions for the current turn
        """
        current_turn = cls.get_current_turn()
        return cls.get_actions_for_turn(current_turn)
    
    @classmethod
    def start_new_conversation(cls) -> None:
        """
        Start a new conversation by clearing action history and resetting turn counter.
        
        This method performs a complete cleanup of conversation-related session state
        while preserving UI preferences.
        """
        with cls._lock:
            try:
                logger.info("Starting new conversation - clearing action history")
                
                # Clear action history
                st.session_state[cls.ACTION_HISTORY_KEY] = []
                
                # Reset turn counter
                st.session_state[cls.CURRENT_TURN_KEY] = 0
                
                # Create new action capture instance
                from ..action_history.capture import ActionHistoryCapture
                st.session_state[cls.ACTION_CAPTURE_KEY] = ActionHistoryCapture()
                
                # Generate new conversation ID
                st.session_state[cls.CONVERSATION_ID_KEY] = cls._generate_conversation_id()
                
                # Update cleanup time
                st.session_state[cls.LAST_CLEANUP_TIME_KEY] = datetime.now()
                
                # Preserve UI state (don't reset show_action_history or expanded state)
                
                logger.info("New conversation started successfully")
                
            except Exception as e:
                logger.error(f"Error starting new conversation: {e}")
                raise
    
    @classmethod
    def cleanup_old_actions(cls, max_actions: int = 1000) -> None:
        """
        Clean up old actions to prevent memory issues with long conversations.
        
        Args:
            max_actions: Maximum number of actions to keep
        """
        with cls._lock:
            try:
                actions = cls.get_action_history()
                
                if len(actions) > max_actions:
                    # Keep the most recent actions
                    recent_actions = actions[-max_actions:]
                    cls.set_action_history(recent_actions)
                    
                    # Update the action capture instance
                    action_capture = cls.get_action_capture()
                    action_capture.actions = recent_actions
                    
                    logger.info(f"Cleaned up action history: kept {len(recent_actions)} of {len(actions)} actions")
                
            except Exception as e:
                logger.error(f"Error cleaning up old actions: {e}")
    
    @classmethod
    def get_ui_state(cls) -> Dict[str, Any]:
        """
        Get the current UI state for action history display.
        
        Returns:
            Dict[str, Any]: UI state dictionary
        """
        with cls._lock:
            try:
                cls.initialize_session_state()
                return {
                    "show_action_history": st.session_state.get(cls.SHOW_ACTION_HISTORY_KEY, True),
                    "action_history_expanded": st.session_state.get(cls.ACTION_HISTORY_EXPANDED_KEY, False),
                    "conversation_id": st.session_state.get(cls.CONVERSATION_ID_KEY, ""),
                    "current_turn": st.session_state.get(cls.CURRENT_TURN_KEY, 0),
                    "total_actions": len(st.session_state.get(cls.ACTION_HISTORY_KEY, []))
                }
            except Exception as e:
                logger.error(f"Error getting UI state: {e}")
                return {
                    "show_action_history": True,
                    "action_history_expanded": False,
                    "conversation_id": "",
                    "current_turn": 0,
                    "total_actions": 0
                }
    
    @classmethod
    def set_ui_state(cls, **kwargs) -> None:
        """
        Set UI state variables.
        
        Args:
            **kwargs: UI state variables to set
        """
        with cls._lock:
            try:
                cls.initialize_session_state()
                
                if "show_action_history" in kwargs:
                    st.session_state[cls.SHOW_ACTION_HISTORY_KEY] = kwargs["show_action_history"]
                
                if "action_history_expanded" in kwargs:
                    st.session_state[cls.ACTION_HISTORY_EXPANDED_KEY] = kwargs["action_history_expanded"]
                
                logger.debug(f"Updated UI state: {kwargs}")
                
            except Exception as e:
                logger.error(f"Error setting UI state: {e}")
    
    @classmethod
    def get_session_summary(cls) -> Dict[str, Any]:
        """
        Get a summary of the current session state.
        
        Returns:
            Dict[str, Any]: Session summary
        """
        with cls._lock:
            try:
                actions = cls.get_action_history()
                current_turn = cls.get_current_turn()
                
                # Calculate statistics
                tool_uses = len([a for a in actions if a.action_type == "tool_use"])
                reasoning_events = len([a for a in actions if a.action_type == "reasoning"])
                completed_tools = len([a for a in actions if a.action_type == "tool_use" and a.duration is not None])
                
                # Calculate average tool duration
                avg_duration = 0
                if completed_tools > 0:
                    total_duration = sum(a.duration for a in actions if a.action_type == "tool_use" and a.duration is not None)
                    avg_duration = total_duration / completed_tools
                
                # Count tools by source
                tool_sources = {}
                for action in actions:
                    if action.action_type == "tool_use" and action.tool_source:
                        tool_sources[action.tool_source] = tool_sources.get(action.tool_source, 0) + 1
                
                return {
                    "conversation_id": st.session_state.get(cls.CONVERSATION_ID_KEY, ""),
                    "current_turn": current_turn,
                    "total_actions": len(actions),
                    "tool_uses": tool_uses,
                    "reasoning_events": reasoning_events,
                    "completed_tools": completed_tools,
                    "avg_tool_duration": avg_duration,
                    "tool_sources": tool_sources,
                    "last_cleanup": st.session_state.get(cls.LAST_CLEANUP_TIME_KEY),
                    "ui_state": cls.get_ui_state()
                }
                
            except Exception as e:
                logger.error(f"Error getting session summary: {e}")
                return {}
    
    @classmethod
    def _generate_conversation_id(cls) -> str:
        """
        Generate a unique conversation ID.
        
        Returns:
            str: Unique conversation ID
        """
        import uuid
        return f"conv_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    @classmethod
    def is_new_conversation_needed(cls) -> bool:
        """
        Check if a new conversation should be started based on certain conditions.
        
        This can be used to automatically detect when to clean up session state,
        for example when the main chat messages are cleared.
        
        Returns:
            bool: True if new conversation should be started
        """
        try:
            # Check if main chat messages exist in session state
            if "messages" in st.session_state:
                messages = st.session_state["messages"]
                
                # If no messages but we have action history, it might indicate a reset
                if len(messages) == 0 and len(cls.get_action_history()) > 0:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if new conversation needed: {e}")
            return False
    
    @classmethod
    def sync_with_action_capture(cls) -> None:
        """
        Synchronize session state with the action capture instance.
        
        This ensures consistency between the session state and the action capture
        instance, which is important for thread safety and data integrity.
        """
        with cls._lock:
            try:
                action_capture = cls.get_action_capture()
                
                # Sync actions
                session_actions = cls.get_action_history()
                action_capture.actions = session_actions
                
                # Sync turn
                current_turn = cls.get_current_turn()
                action_capture.current_turn = current_turn
                
                logger.debug("Synchronized session state with action capture")
                
            except Exception as e:
                logger.error(f"Error synchronizing with action capture: {e}")