"""
Clean Response Handler for Strands agents.

This handler provides a cleaner approach to handling MCP tool responses
by suppressing reasoning content and only displaying final responses.
"""

import time
import logging
import streamlit as st
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CleanResponseHandler:
    """
    A simplified callback handler that filters out reasoning content
    and only displays clean final responses.
    """
    
    def __init__(self, placeholder, update_interval=0.1):
        """
        Initialize the clean response handler.
        
        Args:
            placeholder: Streamlit placeholder for displaying content
            update_interval: Time between UI updates (seconds)
        """
        self.placeholder = placeholder
        self.update_interval = update_interval
        self.last_update_time = time.time()
        
        # Content management
        self.final_response = ""
        self.thinking_content = ""
        self.thinking_placeholder = None
        
        # State tracking
        self.tools_active = False
        self.reasoning_active = False
        self.response_started = False
        
        # Initialize thinking history in session state
        if "thinking_content" not in st.session_state:
            st.session_state.thinking_content = ""
    
    def __call__(self, **kwargs):
        """
        Process events from the Strands agent.
        
        Args:
            **kwargs: Event data from the agent
        """
        # Handle initialization
        if "init_event_loop" in kwargs:
            self._reset_state()
            self.placeholder.markdown("_Thinking..._")
            return
        
        # Handle reasoning/thinking events
        if "reasoningText" in kwargs:
            self._handle_reasoning(kwargs["reasoningText"])
            return
        
        if "reasoning_signature" in kwargs:
            self._end_reasoning()
            return
        
        # Handle tool events
        if "tool_use" in kwargs:
            self._start_tool_usage()
            return
        
        if "tool_result" in kwargs:
            self._handle_tool_result()
            return
        
        # Handle final message - this is what we want to display
        if "message" in kwargs:
            self._handle_final_message(kwargs["message"])
            return
        
        # Handle text streaming - only if not in reasoning/tool mode
        if not self.tools_active and not self.reasoning_active:
            self._handle_text_content(kwargs)
    
    def _reset_state(self):
        """Reset handler state for new interaction."""
        self.final_response = ""
        self.thinking_content = ""
        self.tools_active = False
        self.reasoning_active = False
        self.response_started = False
        self.thinking_placeholder = None
    
    def _handle_reasoning(self, reasoning_text):
        """Handle reasoning/thinking content."""
        self.reasoning_active = True
        
        # Extract text from reasoning
        if isinstance(reasoning_text, dict) and "text" in reasoning_text:
            text = reasoning_text["text"]
        else:
            text = str(reasoning_text)
        
        self.thinking_content += text
        
        # Display thinking content in expandable section
        if not self.thinking_placeholder:
            with self.placeholder.expander("💭 Agent Thinking", expanded=False):
                self.thinking_placeholder = st.empty()
        
        if self.thinking_placeholder:
            self.thinking_placeholder.markdown(f"""
            <div style="background-color: rgba(67, 97, 238, 0.1); padding: 10px; border-left: 4px solid #4361ee; border-radius: 4px;">
            {self.thinking_content}
            </div>
            """, unsafe_allow_html=True)
    
    def _end_reasoning(self):
        """End reasoning phase."""
        self.reasoning_active = False
        
        # Store thinking content in session state
        if self.thinking_content and len(st.session_state.messages) > 0:
            question_idx = len(st.session_state.messages) - 1
            if "thinking_history" not in st.session_state:
                st.session_state.thinking_history = []
            st.session_state.thinking_history.append({
                "question_idx": question_idx,
                "content": self.thinking_content
            })
    
    def _start_tool_usage(self):
        """Start tool usage phase - suppress all text output."""
        self.tools_active = True
        # Clear any accumulated content that might be reasoning
        self.final_response = ""
    
    def _handle_tool_result(self):
        """Handle tool result - keep tools active until final response."""
        # Tools remain active until we get the final message
        pass
    
    def _handle_final_message(self, message):
        """Handle the final message from the agent."""
        self.tools_active = False
        self.reasoning_active = False
        
        # Extract clean text from the message
        clean_text = self._extract_clean_text(message)
        
        if clean_text:
            self.final_response = clean_text
            self.placeholder.markdown(clean_text)
    
    def _extract_clean_text(self, message):
        """Extract clean text from agent message, filtering out reasoning."""
        if not message:
            return ""
        
        text_content = ""
        
        # Handle different message formats
        if isinstance(message, dict) and "content" in message:
            content = message["content"]
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        text_content += block["text"]
        elif isinstance(message, str):
            text_content = message
        
        # Apply aggressive filtering to remove any remaining reasoning
        return self._filter_reasoning_content(text_content)
    
    def _filter_reasoning_content(self, text):
        """Filter out reasoning patterns from text."""
        if not text:
            return text
        
        import re
        
        # Remove common reasoning patterns
        reasoning_patterns = [
            r"I'll use the browser tool to search.*?(?=\n|$)",
            r"Let me search for.*?(?=\n|$)",
            r"I'll search for.*?(?=\n|$)",
            r"Let me try.*?(?=\n|$)",
            r"Let me click.*?(?=\n|$)",
            r"I'll click.*?(?=\n|$)",
            r"Now let me.*?(?=\n|$)",
            r"Let me now.*?(?=\n|$)",
            r"Based on the search results.*?Let me.*?(?=\n|$)",
            r"I'm receiving large responses.*?Let me.*?(?=\n|$)",
        ]
        
        filtered_text = text
        for pattern in reasoning_patterns:
            filtered_text = re.sub(pattern, "", filtered_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up extra whitespace and newlines
        filtered_text = re.sub(r'\n\s*\n', '\n\n', filtered_text)
        filtered_text = filtered_text.strip()
        
        return filtered_text
    
    def _handle_text_content(self, kwargs):
        """Handle streaming text content - only when not in reasoning/tool mode."""
        text_chunk = None
        
        # Extract text from various event formats
        if "content_block_delta" in kwargs:
            delta = kwargs["content_block_delta"]
            if "delta" in delta and "text" in delta["delta"]:
                text_chunk = delta["delta"]["text"]
        elif "data" in kwargs:
            data = kwargs["data"]
            if isinstance(data, str):
                text_chunk = data
            elif isinstance(data, dict) and "delta" in data:
                delta = data["delta"]
                if isinstance(delta, dict) and "text" in delta:
                    text_chunk = delta["text"]
        elif "delta" in kwargs:
            delta = kwargs["delta"]
            if isinstance(delta, dict) and "text" in delta:
                text_chunk = delta["text"]
        
        # Only add clean text content
        if text_chunk and not self._is_reasoning_fragment(text_chunk):
            self.final_response += text_chunk
            self._update_display()
    
    def _is_reasoning_fragment(self, text):
        """Check if text fragment is likely reasoning content."""
        if not text or len(text.strip()) < 3:
            return False
        
        text_lower = text.lower().strip()
        
        # Common reasoning fragments
        reasoning_fragments = [
            "search for", "use the browser", "click the", "let me", "i'll",
            "try another", "now let", "based on", "search query", "search button",
            "samsung", "galaxy", "genai", "cases", "latest", "phones"
        ]
        
        # If text is short and contains reasoning fragments, filter it
        if len(text.strip()) < 50:
            for fragment in reasoning_fragments:
                if fragment in text_lower:
                    return True
        
        return False
    
    def _update_display(self):
        """Update the display if enough time has passed."""
        current_time = time.time()
        if current_time - self.last_update_time > self.update_interval:
            if self.final_response.strip():
                self.placeholder.markdown(self.final_response)
            self.last_update_time = current_time