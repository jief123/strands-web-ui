"""
Action History Capture for Strands Web UI

This module provides functionality to capture and process callback events from the Strands event loop
to maintain a comprehensive history of all agent actions during a conversation session.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import streamlit as st

logger = logging.getLogger(__name__)


@dataclass
class ActionEvent:
    """Represents a single action event in the agent's execution."""
    id: str                           # Unique identifier for the action
    turn: int                         # Conversation turn number
    timestamp: datetime               # When the action occurred
    action_type: str                  # 'tool_use', 'tool_result', 'reasoning'
    tool_name: Optional[str] = None   # Name of the tool used
    tool_source: str = "unknown"      # 'strands_sdk', 'custom', 'mcp'
    tool_use_id: Optional[str] = None # Tool use identifier for matching
    input_data: Dict = field(default_factory=dict)      # Input parameters
    output_data: Optional[Dict] = None                   # Output/result data
    status: Optional[str] = None      # Success/failure status
    duration: Optional[float] = None  # Execution time in seconds
    reasoning_context: Optional[str] = None              # Associated reasoning


class ActionHistoryCapture:
    """
    Captures and processes action events from the Strands event loop.
    
    This class integrates with the StreamlitHandler callback system to capture:
    - Tool usage events from {"callback": {"current_tool_use": ...}} format
    - Reasoning events from {"callback": {"reasoningText": ...}} format  
    - Message events containing tool results and content blocks
    - Stores captured actions in structured format with timestamps and turn tracking
    """
    
    def __init__(self):
        """Initialize the action history capture system."""
        self.actions: List[ActionEvent] = []
        self.current_turn = 0
        self.pending_tool_uses: Dict[str, ActionEvent] = {}  # Track incomplete tool uses
        self.current_reasoning = ""
        self.reasoning_start_time: Optional[datetime] = None
        self._action_counter = 0
        
        # Initialize session state if not already done
        self._initialize_session_state()
        
        # Sync with session state on initialization
        self._sync_from_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for action history."""
        if "action_history" not in st.session_state:
            st.session_state.action_history = []
        if "current_turn" not in st.session_state:
            st.session_state.current_turn = 0
        if "action_capture_initialized" not in st.session_state:
            st.session_state.action_capture_initialized = True
    
    def _sync_from_session_state(self):
        """Sync instance state from session state."""
        try:
            # Sync actions from session state
            if "action_history" in st.session_state:
                self.actions = st.session_state.action_history.copy()
            
            # Sync current turn from session state
            if "current_turn" in st.session_state:
                self.current_turn = st.session_state.current_turn
                
            logger.debug(f"Synced from session state: {len(self.actions)} actions, turn {self.current_turn}")
            
        except Exception as e:
            logger.error(f"Error syncing from session state: {e}")
    
    def _sync_to_session_state(self):
        """Sync instance state to session state."""
        try:
            st.session_state.action_history = self.actions.copy()
            st.session_state.current_turn = self.current_turn
            logger.debug(f"Synced to session state: {len(self.actions)} actions, turn {self.current_turn}")
        except Exception as e:
            logger.error(f"Error syncing to session state: {e}")
    
    def _generate_action_id(self) -> str:
        """Generate a unique action ID."""
        self._action_counter += 1
        return f"action_{self.current_turn}_{self._action_counter}_{int(time.time() * 1000)}"
    
    def _determine_tool_source(self, tool_name: str) -> str:
        """
        Determine the source of a tool based on its name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            str: Tool source ('strands_sdk', 'custom', 'mcp')
        """
        # Known Strands SDK tools
        strands_sdk_tools = {
            "calculator", "editor", "environment", "file_read", "file_write",
            "http_request", "python_repl", "shell", "think", "workflow"
        }
        
        if tool_name in strands_sdk_tools:
            return "strands_sdk"
        elif tool_name.startswith("mcp_") or "." in tool_name:
            # MCP tools often have server prefixes or dot notation
            return "mcp"
        else:
            return "custom"
    
    def capture_tool_use(self, tool_use_data: Dict) -> None:
        """
        Capture a tool use event.
        
        Args:
            tool_use_data: Tool use data from callback event
        """
        try:
            tool_use_id = tool_use_data.get("toolUseId", "unknown")
            tool_name = tool_use_data.get("name", "unknown")
            tool_input = tool_use_data.get("input", {})
            
            # Create action event for tool use
            action = ActionEvent(
                id=self._generate_action_id(),
                turn=self.current_turn,
                timestamp=datetime.now(),
                action_type="tool_use",
                tool_name=tool_name,
                tool_source=self._determine_tool_source(tool_name),
                tool_use_id=tool_use_id,
                input_data=tool_input,
                reasoning_context=self.current_reasoning if self.current_reasoning else None
            )
            
            # Store as pending until we get the result
            self.pending_tool_uses[tool_use_id] = action
            self.actions.append(action)
            
            # Update session state
            self._sync_to_session_state()
            
            logger.debug(f"Captured tool use: {tool_name} (ID: {tool_use_id})")
            
        except Exception as e:
            logger.error(f"Error capturing tool use: {e}")
    
    def capture_tool_result(self, tool_result_data: Dict) -> None:
        """
        Capture a tool result event and match it to the corresponding tool use.
        
        Args:
            tool_result_data: Tool result data from callback event
        """
        try:
            tool_use_id = tool_result_data.get("toolUseId", "unknown")
            status = tool_result_data.get("status", "unknown")
            content = tool_result_data.get("content", [])
            
            # Find the corresponding tool use
            if tool_use_id in self.pending_tool_uses:
                tool_use_action = self.pending_tool_uses[tool_use_id]
                
                # Calculate duration
                duration = (datetime.now() - tool_use_action.timestamp).total_seconds()
                
                # Update the tool use action with result data
                tool_use_action.output_data = {
                    "status": status,
                    "content": content
                }
                tool_use_action.status = status
                tool_use_action.duration = duration
                
                # Remove from pending
                del self.pending_tool_uses[tool_use_id]
                
                # Update session state
                self._sync_to_session_state()
                
                logger.debug(f"Captured tool result: {tool_use_id} ({status}) in {duration:.2f}s")
            else:
                # Create a standalone result action if we don't have the tool use
                action = ActionEvent(
                    id=self._generate_action_id(),
                    turn=self.current_turn,
                    timestamp=datetime.now(),
                    action_type="tool_result",
                    tool_use_id=tool_use_id,
                    output_data={"status": status, "content": content},
                    status=status
                )
                
                self.actions.append(action)
                self._sync_to_session_state()
                
                logger.warning(f"Captured orphaned tool result: {tool_use_id}")
                
        except Exception as e:
            logger.error(f"Error capturing tool result: {e}")
    
    def capture_reasoning(self, reasoning_data: Dict) -> None:
        """
        Capture a reasoning event.
        
        Args:
            reasoning_data: Reasoning data from callback event
        """
        try:
            # Extract reasoning text from various possible formats
            reasoning_text = ""
            
            if isinstance(reasoning_data, dict):
                if "text" in reasoning_data:
                    reasoning_text = reasoning_data["text"]
                elif "reasoningText" in reasoning_data:
                    reasoning_text = reasoning_data["reasoningText"]
                    if isinstance(reasoning_text, dict) and "text" in reasoning_text:
                        reasoning_text = reasoning_text["text"]
            elif isinstance(reasoning_data, str):
                reasoning_text = reasoning_data
            
            if reasoning_text:
                # If this is the start of new reasoning, create an action
                if not self.current_reasoning:
                    self.reasoning_start_time = datetime.now()
                    
                    action = ActionEvent(
                        id=self._generate_action_id(),
                        turn=self.current_turn,
                        timestamp=self.reasoning_start_time,
                        action_type="reasoning",
                        input_data={"reasoning_text": reasoning_text}
                    )
                    
                    self.actions.append(action)
                
                # Accumulate reasoning text
                self.current_reasoning += reasoning_text
                
                # Update the most recent reasoning action
                for action in reversed(self.actions):
                    if action.action_type == "reasoning" and action.turn == self.current_turn:
                        action.input_data["reasoning_text"] = self.current_reasoning
                        if self.reasoning_start_time:
                            action.duration = (datetime.now() - self.reasoning_start_time).total_seconds()
                        break
                
                # Update session state
                self._sync_to_session_state()
                
                logger.debug(f"Captured reasoning text: {len(reasoning_text)} chars")
                
        except Exception as e:
            logger.error(f"Error capturing reasoning: {e}")
    
    def capture_reasoning_end(self) -> None:
        """Mark the end of a reasoning sequence."""
        try:
            if self.current_reasoning and self.reasoning_start_time:
                # Update the duration of the most recent reasoning action
                for action in reversed(self.actions):
                    if action.action_type == "reasoning" and action.turn == self.current_turn:
                        action.duration = (datetime.now() - self.reasoning_start_time).total_seconds()
                        break
                
                logger.debug(f"Reasoning ended: {len(self.current_reasoning)} chars total")
            
            # Don't clear current_reasoning yet - it might be needed for tool context
            
        except Exception as e:
            logger.error(f"Error ending reasoning capture: {e}")
    
    def capture_message_event(self, message_data: Dict) -> None:
        """
        Capture events from message data that may contain tool information.
        
        Args:
            message_data: Message data from callback event
        """
        try:
            if not isinstance(message_data, dict) or "content" not in message_data:
                return
            
            content = message_data["content"]
            if not isinstance(content, list):
                return
            
            # Process content blocks for tool information
            for block in content:
                if not isinstance(block, dict):
                    continue
                
                # Handle tool use blocks
                if "toolUse" in block:
                    self.capture_tool_use(block["toolUse"])
                
                # Handle tool result blocks
                elif "toolResult" in block:
                    self.capture_tool_result(block["toolResult"])
                    
        except Exception as e:
            logger.error(f"Error capturing message event: {e}")
    
    def start_new_turn(self) -> None:
        """Start a new conversation turn."""
        self.current_turn += 1
        self.current_reasoning = ""
        self.reasoning_start_time = None
        
        # Update session state
        self._sync_to_session_state()
        
        logger.debug(f"Started new turn: {self.current_turn}")
    
    def get_actions_for_turn(self, turn: int) -> List[ActionEvent]:
        """
        Get all actions for a specific conversation turn.
        
        Args:
            turn: Turn number
            
        Returns:
            List[ActionEvent]: Actions for the specified turn
        """
        return [action for action in self.actions if action.turn == turn]
    
    def get_all_actions(self) -> List[ActionEvent]:
        """
        Get all captured actions.
        
        Returns:
            List[ActionEvent]: All captured actions
        """
        return self.actions.copy()
    
    def clear_history(self) -> None:
        """Clear all action history."""
        self.actions.clear()
        self.pending_tool_uses.clear()
        self.current_turn = 0
        self.current_reasoning = ""
        self.reasoning_start_time = None
        self._action_counter = 0
        
        # Clear session state
        self._sync_to_session_state()
        
        logger.debug("Cleared action history")
    
    def get_action_summary(self) -> Dict[str, Any]:
        """
        Get a summary of captured actions.
        
        Returns:
            Dict[str, Any]: Summary statistics
        """
        total_actions = len(self.actions)
        tool_uses = len([a for a in self.actions if a.action_type == "tool_use"])
        reasoning_events = len([a for a in self.actions if a.action_type == "reasoning"])
        
        # Calculate average tool execution time
        completed_tools = [a for a in self.actions if a.action_type == "tool_use" and a.duration is not None]
        avg_tool_duration = sum(a.duration for a in completed_tools) / len(completed_tools) if completed_tools else 0
        
        # Count tools by source
        tool_sources = {}
        for action in self.actions:
            if action.action_type == "tool_use" and action.tool_source:
                tool_sources[action.tool_source] = tool_sources.get(action.tool_source, 0) + 1
        
        return {
            "total_actions": total_actions,
            "tool_uses": tool_uses,
            "reasoning_events": reasoning_events,
            "turns": self.current_turn,
            "avg_tool_duration": avg_tool_duration,
            "tool_sources": tool_sources,
            "pending_tools": len(self.pending_tool_uses)
        }