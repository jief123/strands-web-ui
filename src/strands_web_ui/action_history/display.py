"""
Action History Display for Strands Web UI

This module provides a comprehensive UI component for rendering action history in Streamlit.
It creates a collapsible sidebar layout that displays all agent actions with tool type identification,
conversation turn grouping, timestamps, and duration calculations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import streamlit as st
import json

from .capture import ActionEvent, ActionHistoryCapture
from ..utils.session_state_manager import SessionStateManager

logger = logging.getLogger(__name__)


class ActionHistoryDisplay:
    """
    UI component class for rendering action history in Streamlit.
    
    This class provides:
    - Collapsible sidebar layout that doesn't disrupt main chat interface
    - Action rendering with tool type identification (SDK, Custom, MCP)
    - Visual organization with conversation turn grouping
    - Timestamps and duration calculations for tool execution
    """
    
    # Tool type icons and colors
    TOOL_ICONS = {
        "strands_sdk": "🔧",
        "custom": "⚙️", 
        "mcp": "🔌",
        "unknown": "❓"
    }
    
    TOOL_COLORS = {
        "strands_sdk": "#1f77b4",  # Blue
        "custom": "#ff7f0e",       # Orange
        "mcp": "#2ca02c",          # Green
        "unknown": "#d62728"       # Red
    }
    
    ACTION_ICONS = {
        "tool_use": "🛠️",
        "tool_result": "✅",
        "reasoning": "🧠"
    }
    
    def __init__(self, container=None):
        """
        Initialize the ActionHistoryDisplay component.
        
        Args:
            container: Streamlit container to render in (optional)
        """
        self.container = container
        self.session_manager = SessionStateManager
        
        # Initialize session state
        self.session_manager.initialize_session_state()
    
    def render_action_history(self, actions: Optional[List[ActionEvent]] = None) -> None:
        """
        Render the complete action history in the UI.
        
        Args:
            actions: List of actions to render (if None, gets from session state)
        """
        try:
            # Get actions from session state if not provided
            if actions is None:
                actions = self.session_manager.get_action_history()
            
            # Get UI state
            ui_state = self.session_manager.get_ui_state()
            
            # Use provided container or create sidebar
            display_container = self.container if self.container else st.sidebar
            
            with display_container:
                # Header with toggle controls
                self._render_header(ui_state, len(actions))
                
                # Only render content if action history is enabled
                if ui_state.get("show_action_history", True):
                    if actions:
                        # Group actions by turn
                        actions_by_turn = self._group_actions_by_turn(actions)
                        
                        # Render action summary
                        if ui_state.get("action_history_expanded", False):
                            self._render_action_summary(actions)
                        
                        # Render actions by turn
                        self._render_actions_by_turn(actions_by_turn)
                    else:
                        st.info("No actions captured yet. Actions will appear here as the agent works.")
                
        except Exception as e:
            logger.error(f"Error rendering action history: {e}")
            st.error("Error displaying action history")
    
    def _render_header(self, ui_state: Dict[str, Any], total_actions: int) -> None:
        """
        Render the action history header with controls.
        
        Args:
            ui_state: Current UI state
            total_actions: Total number of actions
        """
        try:
            # Main header with action count and help
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.subheader(f"Action History ({total_actions})")
            
            with col2:
                # Help button
                if st.button("❓", help="Show action history help", key="show_help"):
                    self._show_inline_help()
            
            with col3:
                # Toggle visibility button
                show_history = ui_state.get("show_action_history", True)
                if st.button("👁️" if show_history else "👁️‍🗨️", 
                           help="Toggle action history visibility - Shows/hides all agent actions and tool usage",
                           key="toggle_action_history"):
                    self.session_manager.set_ui_state(show_action_history=not show_history)
                    st.rerun()
            
            # Expandable controls (only if history is visible)
            if ui_state.get("show_action_history", True):
                expanded = ui_state.get("action_history_expanded", False)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    if st.button("📊 Summary" if not expanded else "📋 Simple", 
                               help="Toggle detailed summary - Shows statistics and performance metrics for all actions",
                               key="toggle_summary"):
                        self.session_manager.set_ui_state(action_history_expanded=not expanded)
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", help="Clear history - Removes all captured actions from current session", key="clear_history"):
                        self._clear_action_history()
                        st.rerun()
                
                with col3:
                    if st.button("🔄", help="Refresh - Updates the action history display", key="refresh_history"):
                        st.rerun()
                
                st.divider()
        
        except Exception as e:
            logger.error(f"Error rendering header: {e}")
    
    def _show_inline_help(self) -> None:
        """Show inline help information about action history features."""
        try:
            with st.expander("📖 Action History Help", expanded=True):
                st.markdown("""
                ### What is Action History?
                
                Action History shows every action the agent takes during your conversation:
                - **🛠️ Tool Usage**: Every tool the agent uses (calculator, file operations, etc.)
                - **🧠 Reasoning**: The agent's thinking process before taking actions
                - **📊 Performance**: Timing and success/failure information
                
                ### Understanding the Display
                
                **Turn Organization**: Actions are grouped by conversation turns
                - Each user message starts a new turn
                - Most recent turn is expanded by default
                
                **Action Types**:
                - 🔧 **Strands SDK Tools**: Built-in tools (calculator, editor, file operations)
                - 🔌 **MCP Tools**: External tools from Model Context Protocol servers
                - ⚙️ **Custom Tools**: Agent-defined tools for specific tasks
                
                **Status Indicators**:
                - 🟢 Green dot = Success
                - 🔴 Red dot = Failed
                - Duration shows how long each tool took
                
                ### Using the Controls
                
                - **👁️ Toggle**: Show/hide the entire action history
                - **📊 Summary**: View statistics and performance metrics
                - **🗑️ Clear**: Remove all captured actions
                - **🔄 Refresh**: Update the display
                
                ### Tips for Better Understanding
                
                1. **Watch the sequence**: See the order of agent actions
                2. **Check timing**: Identify slow operations
                3. **Review failures**: Understand what went wrong
                4. **Follow reasoning**: See why the agent chose specific tools
                
                ### Privacy Note
                
                Action history is stored only in your browser session and is cleared when you start a new conversation.
                """)
        except Exception as e:
            logger.error(f"Error showing inline help: {e}")
    
    def _render_action_summary(self, actions: List[ActionEvent]) -> None:
        """
        Render a summary of action statistics.
        
        Args:
            actions: List of actions to summarize
        """
        try:
            with st.expander("📊 Action Summary", expanded=True):
                # Calculate statistics
                stats = self._calculate_action_stats(actions)
                
                # Display key metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Actions", stats["total_actions"])
                    st.metric("Tool Uses", stats["tool_uses"])
                
                with col2:
                    st.metric("Reasoning Events", stats["reasoning_events"])
                    st.metric("Avg Duration", f"{stats['avg_duration']:.2f}s")
                
                with col3:
                    st.metric("Current Turn", stats["current_turn"])
                    st.metric("Completed Tools", stats["completed_tools"])
                
                # Tool source breakdown
                if stats["tool_sources"]:
                    st.write("**Tool Sources:**")
                    for source, count in stats["tool_sources"].items():
                        icon = self.TOOL_ICONS.get(source, "❓")
                        st.write(f"{icon} {source.replace('_', ' ').title()}: {count}")
                
                # Recent activity
                if stats["recent_actions"]:
                    st.write("**Recent Activity:**")
                    for action in stats["recent_actions"][-3:]:  # Show last 3
                        time_str = action.timestamp.strftime("%H:%M:%S")
                        icon = self.ACTION_ICONS.get(action.action_type, "📝")
                        tool_name = action.tool_name or "N/A"
                        st.write(f"{icon} {time_str} - {tool_name}")
        
        except Exception as e:
            logger.error(f"Error rendering action summary: {e}")
    
    def _group_actions_by_turn(self, actions: List[ActionEvent]) -> Dict[int, List[ActionEvent]]:
        """
        Group actions by conversation turn.
        
        Args:
            actions: List of actions to group
            
        Returns:
            Dict[int, List[ActionEvent]]: Actions grouped by turn
        """
        actions_by_turn = {}
        for action in actions:
            turn = action.turn
            if turn not in actions_by_turn:
                actions_by_turn[turn] = []
            actions_by_turn[turn].append(action)
        
        # Sort actions within each turn by timestamp
        for turn in actions_by_turn:
            actions_by_turn[turn].sort(key=lambda a: a.timestamp)
        
        return actions_by_turn
    
    def _render_actions_by_turn(self, actions_by_turn: Dict[int, List[ActionEvent]]) -> None:
        """
        Render actions organized by conversation turn.
        
        Args:
            actions_by_turn: Actions grouped by turn
        """
        try:
            # Sort turns in descending order (most recent first)
            sorted_turns = sorted(actions_by_turn.keys(), reverse=True)
            
            for turn in sorted_turns:
                turn_actions = actions_by_turn[turn]
                
                # Turn header
                turn_title = f"Turn {turn}" if turn > 0 else "Initial"
                turn_count = len(turn_actions)
                
                with st.expander(f"🔄 {turn_title} ({turn_count} actions)", 
                               expanded=(turn == max(sorted_turns))):  # Expand most recent turn
                    
                    # Render each action in the turn
                    for i, action in enumerate(turn_actions):
                        self._render_single_action(action, i, len(turn_actions))
                        
                        # Add separator between actions (except for last one)
                        if i < len(turn_actions) - 1:
                            st.markdown("---")
        
        except Exception as e:
            logger.error(f"Error rendering actions by turn: {e}")
    
    def _render_single_action(self, action: ActionEvent, index: int, total_in_turn: int) -> None:
        """
        Render a single action event.
        
        Args:
            action: Action event to render
            index: Index of action in turn
            total_in_turn: Total actions in this turn
        """
        try:
            # Action header with icon and basic info
            action_icon = self.ACTION_ICONS.get(action.action_type, "📝")
            time_str = action.timestamp.strftime("%H:%M:%S")
            
            # Create action header
            if action.action_type == "tool_use":
                self._render_tool_action(action, action_icon, time_str)
            elif action.action_type == "reasoning":
                self._render_reasoning_action(action, action_icon, time_str)
            else:
                self._render_generic_action(action, action_icon, time_str)
        
        except Exception as e:
            logger.error(f"Error rendering single action: {e}")
            st.error(f"Error displaying action: {action.id}")
    
    def _render_tool_action(self, action: ActionEvent, icon: str, time_str: str) -> None:
        """
        Render a tool use action with detailed information.
        
        Args:
            action: Tool action to render
            icon: Action icon
            time_str: Formatted timestamp
        """
        try:
            # Tool header with source identification
            tool_icon = self._get_tool_specific_icon(action.tool_name, action.tool_source)
            tool_color = self.TOOL_COLORS.get(action.tool_source, "#666666")
            
            # Main action info
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Enhanced tool display with category information
                tool_category = self._get_tool_category(action.tool_name, action.tool_source)
                source_display = self._get_source_display(action.tool_source, action.input_data)
                
                st.markdown(f"""
                <div style="padding: 8px; border-left: 3px solid {tool_color}; background-color: rgba(128,128,128,0.1);">
                    <strong>{icon} {tool_icon} {action.tool_name or 'Unknown Tool'}</strong>
                    {f'<span style="color: {tool_color}; font-size: 0.8em;"> ({tool_category})</span>' if tool_category else ''}<br>
                    <small>🕒 {time_str} | 📍 {source_display}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Duration and status
                if action.duration is not None:
                    st.metric("Duration", f"{action.duration:.2f}s", delta=None)
                
                if action.status:
                    status_color = "green" if action.status == "success" else "red"
                    st.markdown(f"<span style='color: {status_color}'>●</span> {action.status}", 
                              unsafe_allow_html=True)
            
            # Tool-specific input rendering
            if action.input_data:
                st.markdown("**📥 Input Parameters:**")
                with st.container():
                    self._render_tool_specific_input(action.tool_name, action.tool_source, action.input_data)
            
            # Tool-specific output rendering
            if action.output_data:
                st.markdown("**📤 Output Results:**")
                with st.container():
                    self._render_tool_specific_output(action.tool_name, action.tool_source, action.output_data)
            
            # Associated reasoning context
            if action.reasoning_context:
                st.markdown("**🧠 Reasoning Context:**")
                st.text_area("Reasoning Context", value=action.reasoning_context, height=100, disabled=True, key=f"reasoning_{action.id}", label_visibility="collapsed")
        
        except Exception as e:
            logger.error(f"Error rendering tool action: {e}")
    
    def _render_reasoning_action(self, action: ActionEvent, icon: str, time_str: str) -> None:
        """
        Render a reasoning action.
        
        Args:
            action: Reasoning action to render
            icon: Action icon
            time_str: Formatted timestamp
        """
        try:
            # Reasoning header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="padding: 8px; border-left: 3px solid #9467bd; background-color: rgba(148,103,189,0.1);">
                    <strong>{icon} Agent Reasoning</strong><br>
                    <small>🕒 {time_str}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if action.duration is not None:
                    st.metric("Duration", f"{action.duration:.2f}s", delta=None)
            
            # Reasoning content
            reasoning_text = ""
            if action.input_data and "reasoning_text" in action.input_data:
                reasoning_text = action.input_data["reasoning_text"]
            
            if reasoning_text:
                # Show reasoning content directly without nested expander
                if len(reasoning_text) > 200:
                    st.markdown("**Reasoning (preview):**")
                    preview = reasoning_text[:200] + "..."
                    st.text(preview)
                    st.markdown("**Full Reasoning:**")
                    st.text_area("Full Reasoning", value=reasoning_text, height=150, disabled=True, key=f"full_reasoning_{action.id}", label_visibility="collapsed")
                else:
                    st.markdown("**Reasoning:**")
                    st.text(reasoning_text)
        
        except Exception as e:
            logger.error(f"Error rendering reasoning action: {e}")
    
    def _render_generic_action(self, action: ActionEvent, icon: str, time_str: str) -> None:
        """
        Render a generic action (fallback for unknown action types).
        
        Args:
            action: Action to render
            icon: Action icon
            time_str: Formatted timestamp
        """
        try:
            st.markdown(f"""
            <div style="padding: 8px; border-left: 3px solid #666666; background-color: rgba(128,128,128,0.1);">
                <strong>{icon} {action.action_type.replace('_', ' ').title()}</strong><br>
                <small>🕒 {time_str} | ID: {action.id}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Show any available data
            if action.input_data:
                with st.expander("📥 Data", expanded=False):
                    self._render_structured_data(action.input_data)
        
        except Exception as e:
            logger.error(f"Error rendering generic action: {e}")
    
    def _render_structured_data(self, data: Any) -> None:
        """
        Render structured data (JSON, dict, etc.) in a readable format.
        
        Args:
            data: Data to render
        """
        try:
            if isinstance(data, dict):
                # Handle special cases for better display
                if "content" in data and isinstance(data["content"], list):
                    # Tool result content
                    for i, content_item in enumerate(data["content"]):
                        if isinstance(content_item, dict):
                            if "text" in content_item:
                                st.text_area(f"Text Content {i+1}", 
                                           value=content_item["text"], 
                                           height=100, 
                                           disabled=True,
                                           key=f"content_{hash(str(content_item))}_{i}")
                            elif "json" in content_item:
                                st.json(content_item["json"])
                            else:
                                st.json(content_item)
                        else:
                            st.text(str(content_item))
                else:
                    # Regular dictionary
                    if len(str(data)) > 500:
                        # Large data - use JSON viewer
                        st.json(data)
                    else:
                        # Small data - use formatted display
                        for key, value in data.items():
                            if isinstance(value, (str, int, float, bool)):
                                st.write(f"**{key}:** {value}")
                            else:
                                st.write(f"**{key}:**")
                                st.json(value)
            elif isinstance(data, list):
                st.json(data)
            elif isinstance(data, str):
                if len(data) > 200:
                    st.text_area("Text Data", value=data, height=100, disabled=True, key=f"text_{hash(data)}", label_visibility="collapsed")
                else:
                    st.text(data)
            else:
                st.write(str(data))
        
        except Exception as e:
            logger.error(f"Error rendering structured data: {e}")
            st.text(str(data))
    
    def _calculate_action_stats(self, actions: List[ActionEvent]) -> Dict[str, Any]:
        """
        Calculate statistics for action summary.
        
        Args:
            actions: List of actions to analyze
            
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        try:
            total_actions = len(actions)
            tool_uses = len([a for a in actions if a.action_type == "tool_use"])
            reasoning_events = len([a for a in actions if a.action_type == "reasoning"])
            
            # Calculate durations
            completed_tools = [a for a in actions if a.action_type == "tool_use" and a.duration is not None]
            avg_duration = sum(a.duration for a in completed_tools) / len(completed_tools) if completed_tools else 0
            
            # Tool sources
            tool_sources = {}
            for action in actions:
                if action.action_type == "tool_use" and action.tool_source:
                    source = action.tool_source
                    tool_sources[source] = tool_sources.get(source, 0) + 1
            
            # Current turn
            current_turn = max((a.turn for a in actions), default=0)
            
            return {
                "total_actions": total_actions,
                "tool_uses": tool_uses,
                "reasoning_events": reasoning_events,
                "completed_tools": len(completed_tools),
                "avg_duration": avg_duration,
                "tool_sources": tool_sources,
                "current_turn": current_turn,
                "recent_actions": sorted(actions, key=lambda a: a.timestamp)
            }
        
        except Exception as e:
            logger.error(f"Error calculating action stats: {e}")
            return {
                "total_actions": 0,
                "tool_uses": 0,
                "reasoning_events": 0,
                "completed_tools": 0,
                "avg_duration": 0,
                "tool_sources": {},
                "current_turn": 0,
                "recent_actions": []
            }
    
    def _clear_action_history(self) -> None:
        """Clear all action history."""
        try:
            # Clear through session manager
            self.session_manager.start_new_conversation()
            
            # Also clear the action capture instance
            action_capture = self.session_manager.get_action_capture()
            action_capture.clear_history()
            
            st.success("Action history cleared!")
            logger.info("Action history cleared by user")
        
        except Exception as e:
            logger.error(f"Error clearing action history: {e}")
            st.error("Error clearing action history")
    
    def render_compact_summary(self) -> None:
        """
        Render a compact summary suitable for main interface integration.
        
        This method provides a minimal display that can be embedded in the main
        chat interface without taking up much space.
        """
        try:
            actions = self.session_manager.get_action_history()
            
            if actions:
                stats = self._calculate_action_stats(actions)
                
                # Compact display
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Actions", stats["total_actions"], delta=None)
                
                with col2:
                    st.metric("Tools", stats["tool_uses"], delta=None)
                
                with col3:
                    st.metric("Turn", stats["current_turn"], delta=None)
                
                with col4:
                    if st.button("📋", help="View full action history"):
                        self.session_manager.set_ui_state(show_action_history=True)
                        st.rerun()
        
        except Exception as e:
            logger.error(f"Error rendering compact summary: {e}")
    
    def get_action_timeline(self, actions: Optional[List[ActionEvent]] = None) -> List[Tuple[datetime, str, str]]:
        """
        Get a timeline of actions for visualization.
        
        Args:
            actions: List of actions (if None, gets from session state)
            
        Returns:
            List[Tuple[datetime, str, str]]: Timeline entries (timestamp, type, description)
        """
        try:
            if actions is None:
                actions = self.session_manager.get_action_history()
            
            timeline = []
            for action in sorted(actions, key=lambda a: a.timestamp):
                description = ""
                if action.action_type == "tool_use":
                    description = f"{action.tool_name} ({action.tool_source})"
                elif action.action_type == "reasoning":
                    description = "Agent reasoning"
                else:
                    description = action.action_type.replace("_", " ").title()
                
                timeline.append((action.timestamp, action.action_type, description))
            
            return timeline
        
        except Exception as e:
            logger.error(f"Error getting action timeline: {e}")
            return []
    
    def _get_tool_specific_icon(self, tool_name: Optional[str], tool_source: str) -> str:
        """
        Get a specific icon for the tool based on its name and source.
        
        Args:
            tool_name: Name of the tool
            tool_source: Source of the tool (strands_sdk, custom, mcp)
            
        Returns:
            str: Icon for the tool
        """
        if not tool_name:
            return self.TOOL_ICONS.get(tool_source, "❓")
        
        # Strands SDK tool icons
        strands_tool_icons = {
            "calculator": "🧮",
            "editor": "📝",
            "file_read": "📖",
            "file_write": "💾",
            "python_repl": "🐍",
            "shell": "💻",
            "http_request": "🌐",
            "environment": "🌍",
            "think": "💭",
            "workflow": "🔄"
        }
        
        # MCP tool icons (common ones)
        mcp_tool_icons = {
            "filesystem": "📁",
            "playwright": "🎭",
            "browser": "🌐",
            "database": "🗄️",
            "git": "📚"
        }
        
        if tool_source == "strands_sdk":
            return strands_tool_icons.get(tool_name, "🔧")
        elif tool_source == "mcp":
            return mcp_tool_icons.get(tool_name, "🔌")
        elif tool_source == "custom":
            return "⚙️"
        else:
            return "❓"
    
    def _get_tool_category(self, tool_name: Optional[str], tool_source: str) -> Optional[str]:
        """
        Get the category/type of the tool for display purposes.
        
        Args:
            tool_name: Name of the tool
            tool_source: Source of the tool
            
        Returns:
            Optional[str]: Category description
        """
        if not tool_name:
            return None
        
        # Strands SDK tool categories
        strands_categories = {
            "calculator": "Math & Computation",
            "editor": "Text Editing",
            "file_read": "File Operations",
            "file_write": "File Operations", 
            "python_repl": "Code Execution",
            "shell": "System Commands",
            "http_request": "Network",
            "environment": "System Info",
            "think": "Reasoning",
            "workflow": "Automation"
        }
        
        if tool_source == "strands_sdk":
            return strands_categories.get(tool_name, "SDK Tool")
        elif tool_source == "mcp":
            return "MCP Tool"
        elif tool_source == "custom":
            return "Custom Tool"
        else:
            return None
    
    def _get_source_display(self, tool_source: str, input_data: Optional[Dict]) -> str:
        """
        Get a formatted display string for the tool source.
        
        Args:
            tool_source: Source of the tool
            input_data: Input data that might contain MCP server info
            
        Returns:
            str: Formatted source display
        """
        if tool_source == "mcp" and input_data:
            # Try to extract MCP server information
            server_name = input_data.get("server_name") or input_data.get("mcp_server")
            if server_name:
                return f"MCP ({server_name})"
        
        return tool_source.replace('_', ' ').title()
    
    def _render_tool_specific_input(self, tool_name: Optional[str], tool_source: str, input_data: Dict) -> None:
        """
        Render tool input parameters with tool-specific formatting.
        
        Args:
            tool_name: Name of the tool
            tool_source: Source of the tool
            input_data: Input parameters
        """
        try:
            if tool_source == "strands_sdk" and tool_name:
                self._render_strands_sdk_input(tool_name, input_data)
            elif tool_source == "mcp":
                self._render_mcp_input(tool_name, input_data)
            elif tool_source == "custom":
                self._render_custom_tool_input(tool_name, input_data)
            else:
                self._render_structured_data(input_data)
        except Exception as e:
            logger.error(f"Error rendering tool-specific input: {e}")
            self._render_structured_data(input_data)
    
    def _render_tool_specific_output(self, tool_name: Optional[str], tool_source: str, output_data: Dict) -> None:
        """
        Render tool output with tool-specific formatting.
        
        Args:
            tool_name: Name of the tool
            tool_source: Source of the tool
            output_data: Output data
        """
        try:
            if tool_source == "strands_sdk" and tool_name:
                self._render_strands_sdk_output(tool_name, output_data)
            elif tool_source == "mcp":
                self._render_mcp_output(tool_name, output_data)
            elif tool_source == "custom":
                self._render_custom_tool_output(tool_name, output_data)
            else:
                self._render_structured_data(output_data)
        except Exception as e:
            logger.error(f"Error rendering tool-specific output: {e}")
            self._render_structured_data(output_data)
    
    def _render_strands_sdk_input(self, tool_name: str, input_data: Dict) -> None:
        """
        Render Strands SDK tool input with specific formatting.
        
        Args:
            tool_name: Name of the Strands SDK tool
            input_data: Input parameters
        """
        try:
            if tool_name == "calculator":
                expression = input_data.get("expression", "")
                st.code(f"Expression: {expression}", language="python")
            
            elif tool_name == "file_read":
                path = input_data.get("path", "")
                mode = input_data.get("mode", "read")
                st.write(f"**Path:** `{path}`")
                st.write(f"**Mode:** {mode}")
                if "pattern" in input_data:
                    st.write(f"**Pattern:** `{input_data['pattern']}`")
            
            elif tool_name == "file_write":
                path = input_data.get("path", "")
                content_preview = str(input_data.get("content", ""))[:100]
                st.write(f"**Path:** `{path}`")
                st.write(f"**Content Preview:** {content_preview}...")
                if "mode" in input_data:
                    st.write(f"**Mode:** {input_data['mode']}")
            
            elif tool_name == "python_repl":
                code = input_data.get("code", "")
                st.code(code, language="python")
            
            elif tool_name == "shell":
                command = input_data.get("command", "")
                st.code(f"$ {command}", language="bash")
                if "working_directory" in input_data:
                    st.write(f"**Working Directory:** `{input_data['working_directory']}`")
            
            elif tool_name == "http_request":
                url = input_data.get("url", "")
                method = input_data.get("method", "GET")
                st.write(f"**URL:** `{url}`")
                st.write(f"**Method:** {method}")
                if "headers" in input_data:
                    st.write("**Headers:**")
                    st.json(input_data["headers"])
                if "data" in input_data:
                    st.write("**Request Data:**")
                    st.json(input_data["data"])
            
            elif tool_name == "editor":
                operation = input_data.get("operation", "")
                st.write(f"**Operation:** {operation}")
                if "path" in input_data:
                    st.write(f"**Path:** `{input_data['path']}`")
                if "content" in input_data:
                    content_preview = str(input_data["content"])[:100]
                    st.write(f"**Content Preview:** {content_preview}...")
            
            else:
                # Generic Strands SDK tool
                self._render_structured_data(input_data)
        
        except Exception as e:
            logger.error(f"Error rendering Strands SDK input for {tool_name}: {e}")
            self._render_structured_data(input_data)
    
    def _render_strands_sdk_output(self, tool_name: str, output_data: Dict) -> None:
        """
        Render Strands SDK tool output with specific formatting.
        
        Args:
            tool_name: Name of the Strands SDK tool
            output_data: Output data
        """
        try:
            if tool_name == "calculator":
                result = output_data.get("result")
                if result is not None:
                    st.metric("Result", str(result))
                else:
                    self._render_structured_data(output_data)
            
            elif tool_name in ["file_read", "file_write"]:
                if "content" in output_data:
                    content = output_data["content"]
                    if isinstance(content, str) and len(content) > 500:
                        st.text_area("File Content", value=content, height=200, disabled=True, key=f"file_content_{hash(content)}")
                    else:
                        st.text(content)
                else:
                    self._render_structured_data(output_data)
            
            elif tool_name == "python_repl":
                if "stdout" in output_data:
                    st.write("**Output:**")
                    st.code(output_data["stdout"], language="text")
                if "stderr" in output_data and output_data["stderr"]:
                    st.write("**Errors:**")
                    st.code(output_data["stderr"], language="text")
                if "result" in output_data:
                    st.write("**Result:**")
                    st.json(output_data["result"])
            
            elif tool_name == "shell":
                if "stdout" in output_data:
                    st.write("**Output:**")
                    st.code(output_data["stdout"], language="text")
                if "stderr" in output_data and output_data["stderr"]:
                    st.write("**Errors:**")
                    st.code(output_data["stderr"], language="text")
                if "exit_code" in output_data:
                    exit_code = output_data["exit_code"]
                    color = "green" if exit_code == 0 else "red"
                    st.markdown(f"**Exit Code:** <span style='color: {color}'>{exit_code}</span>", unsafe_allow_html=True)
            
            elif tool_name == "http_request":
                if "status_code" in output_data:
                    status_code = output_data["status_code"]
                    color = "green" if 200 <= status_code < 300 else "red"
                    st.markdown(f"**Status Code:** <span style='color: {color}'>{status_code}</span>", unsafe_allow_html=True)
                if "headers" in output_data:
                    st.write("**Response Headers:**")
                    st.json(output_data["headers"])
                if "content" in output_data:
                    content = output_data["content"]
                    if isinstance(content, str) and len(content) > 500:
                        st.text_area("Response Content", value=content, height=200, disabled=True, key=f"http_content_{hash(content)}")
                    else:
                        st.text(content)
            
            else:
                # Generic Strands SDK tool output
                self._render_structured_data(output_data)
        
        except Exception as e:
            logger.error(f"Error rendering Strands SDK output for {tool_name}: {e}")
            self._render_structured_data(output_data)
    
    def _render_mcp_input(self, tool_name: Optional[str], input_data: Dict) -> None:
        """
        Render MCP tool input with server source information.
        
        Args:
            tool_name: Name of the MCP tool
            input_data: Input parameters
        """
        try:
            # Show MCP server information if available
            server_name = input_data.get("server_name") or input_data.get("mcp_server")
            if server_name:
                st.write(f"**MCP Server:** {server_name}")
            
            # Show tool-specific parameters
            tool_params = {k: v for k, v in input_data.items() 
                          if k not in ["server_name", "mcp_server"]}
            
            if tool_params:
                st.write("**Parameters:**")
                for key, value in tool_params.items():
                    if isinstance(value, (str, int, float, bool)):
                        st.write(f"**{key}:** {value}")
                    else:
                        st.write(f"**{key}:**")
                        st.json(value)
            else:
                self._render_structured_data(input_data)
        
        except Exception as e:
            logger.error(f"Error rendering MCP input: {e}")
            self._render_structured_data(input_data)
    
    def _render_mcp_output(self, tool_name: Optional[str], output_data: Dict) -> None:
        """
        Render MCP tool output with appropriate formatting.
        
        Args:
            tool_name: Name of the MCP tool
            output_data: Output data
        """
        try:
            # Handle common MCP output patterns
            if "content" in output_data:
                content = output_data["content"]
                if isinstance(content, list):
                    for i, item in enumerate(content):
                        if isinstance(item, dict) and "text" in item:
                            st.text_area(f"Content {i+1}", value=item["text"], height=100, disabled=True, key=f"mcp_content_{hash(str(item))}_{i}")
                        else:
                            st.json(item)
                else:
                    st.text(str(content))
            
            elif "result" in output_data:
                result = output_data["result"]
                if isinstance(result, (str, int, float, bool)):
                    st.metric("Result", str(result))
                else:
                    st.json(result)
            
            else:
                # Generic MCP output
                self._render_structured_data(output_data)
        
        except Exception as e:
            logger.error(f"Error rendering MCP output: {e}")
            self._render_structured_data(output_data)
    
    def _render_custom_tool_input(self, tool_name: Optional[str], input_data: Dict) -> None:
        """
        Render custom agent-defined tool input.
        
        Args:
            tool_name: Name of the custom tool
            input_data: Input parameters
        """
        try:
            st.write(f"**Custom Tool:** {tool_name or 'Unknown'}")
            
            # Show parameters in a structured way
            if input_data:
                st.write("**Parameters:**")
                for key, value in input_data.items():
                    if isinstance(value, (str, int, float, bool)):
                        st.write(f"**{key}:** {value}")
                    else:
                        st.write(f"**{key}:**")
                        st.json(value)
            else:
                st.info("No input parameters")
        
        except Exception as e:
            logger.error(f"Error rendering custom tool input: {e}")
            self._render_structured_data(input_data)
    
    def _render_custom_tool_output(self, tool_name: Optional[str], output_data: Dict) -> None:
        """
        Render custom agent-defined tool output.
        
        Args:
            tool_name: Name of the custom tool
            output_data: Output data
        """
        try:
            # Generic custom tool output rendering
            self._render_structured_data(output_data)
        
        except Exception as e:
            logger.error(f"Error rendering custom tool output: {e}")
            self._render_structured_data(output_data)
    
    def _get_source_display(self, tool_source: str, input_data: Optional[Dict]) -> str:
        """
        Get a formatted display string for the tool source.
        
        Args:
            tool_source: Source of the tool
            input_data: Input data that might contain MCP server info
            
        Returns:
            str: Formatted source display
        """
        if tool_source == "mcp" and input_data:
            # Try to extract MCP server information
            server_name = input_data.get("server_name") or input_data.get("mcp_server")
            if server_name:
                return f"MCP ({server_name})"
        
        return tool_source.replace('_', ' ').title()
    
    def _render_tool_specific_input(self, tool_name: Optional[str], tool_source: str, input_data: Dict) -> None:
        """
        Render tool input parameters with tool-specific formatting.
        
        Args:
            tool_name: Name of the tool
            tool_source: Source of the tool
            input_data: Input parameters
        """
        try:
            if tool_source == "strands_sdk" and tool_name:
                self._render_strands_sdk_input(tool_name, input_data)
            elif tool_source == "mcp":
                self._render_mcp_input(tool_name, input_data)
            elif tool_source == "custom":
                self._render_custom_tool_input(tool_name, input_data)
            else:
                self._render_structured_data(input_data)
        except Exception as e:
            logger.error(f"Error rendering tool-specific input: {e}")
            self._render_structured_data(input_data)
    
    def _render_tool_specific_output(self, tool_name: Optional[str], tool_source: str, output_data: Dict) -> None:
        """
        Render tool output with tool-specific formatting.
        
        Args:
            tool_name: Name of the tool
            tool_source: Source of the tool
            output_data: Output data
        """
        try:
            if tool_source == "strands_sdk" and tool_name:
                self._render_strands_sdk_output(tool_name, output_data)
            elif tool_source == "mcp":
                self._render_mcp_output(tool_name, output_data)
            elif tool_source == "custom":
                self._render_custom_tool_output(tool_name, output_data)
            else:
                self._render_structured_data(output_data)
        except Exception as e:
            logger.error(f"Error rendering tool-specific output: {e}")
            self._render_structured_data(output_data)
    
    def _render_strands_sdk_input(self, tool_name: str, input_data: Dict) -> None:
        """
        Render Strands SDK tool input with specific formatting for each tool type.
        
        Args:
            tool_name: Name of the Strands SDK tool
            input_data: Input parameters
        """
        try:
            # Handle case where input_data might be a string instead of dict
            if isinstance(input_data, str):
                st.text_area("Input", value=input_data, height=100, disabled=True, 
                           key=f"sdk_input_str_{hash(input_data)}", label_visibility="collapsed")
                return
            
            # Ensure input_data is a dictionary
            if not isinstance(input_data, dict):
                st.write(f"**Input:** {str(input_data)}")
                return
            
            # Tool-specific input rendering
            if tool_name == "calculator":
                expression = input_data.get("expression", "")
                if expression:
                    st.code(f"Expression: {expression}", language="text")
                else:
                    self._render_structured_data(input_data)
            
            elif tool_name == "file_read":
                file_path = input_data.get("file_path") or input_data.get("path")
                if file_path:
                    st.code(f"📁 File: {file_path}")
                else:
                    self._render_structured_data(input_data)
            
            elif tool_name == "file_write":
                file_path = input_data.get("file_path") or input_data.get("path")
                content = input_data.get("content", "")
                if file_path:
                    st.code(f"📁 File: {file_path}")
                if content and len(content) > 100:
                    st.text_area("Content Preview", value=content[:100] + "...", 
                               height=60, disabled=True, 
                               key=f"file_write_preview_{hash(content)}", 
                               label_visibility="collapsed")
                elif content:
                    st.text(f"Content: {content}")
                
                if not file_path and not content:
                    self._render_structured_data(input_data)
            
            elif tool_name == "python_repl":
                code = input_data.get("code", "")
                if code:
                    st.code(code, language="python")
                else:
                    self._render_structured_data(input_data)
            
            elif tool_name == "shell":
                command = input_data.get("command", "")
                if command:
                    st.code(f"$ {command}", language="bash")
                else:
                    self._render_structured_data(input_data)
            
            elif tool_name == "http_request":
                url = input_data.get("url", "")
                method = input_data.get("method", "GET")
                if url:
                    st.write(f"**{method}** [{url}]({url})")
                    
                    # Show headers if present
                    headers = input_data.get("headers")
                    if headers:
                        st.write("**Headers:**")
                        st.json(headers)
                    
                    # Show body if present
                    body = input_data.get("body") or input_data.get("data")
                    if body:
                        st.write("**Body:**")
                        if isinstance(body, str) and len(body) > 200:
                            st.text_area("Request Body", value=body, height=100, 
                                       disabled=True, key=f"http_body_{hash(body)}", 
                                       label_visibility="collapsed")
                        else:
                            st.json(body)
                else:
                    self._render_structured_data(input_data)
            
            elif tool_name == "editor":
                operation = input_data.get("operation", "")
                file_path = input_data.get("file_path", "")
                if operation and file_path:
                    st.write(f"**Operation:** {operation}")
                    st.code(f"📁 File: {file_path}")
                    
                    # Show additional parameters based on operation
                    if operation in ["replace", "insert"]:
                        content = input_data.get("new_content") or input_data.get("content")
                        if content:
                            st.text_area("Content", value=content, height=100, 
                                       disabled=True, key=f"editor_content_{hash(content)}", 
                                       label_visibility="collapsed")
                else:
                    self._render_structured_data(input_data)
            
            elif tool_name == "think":
                query = input_data.get("query", "")
                if query:
                    st.text_area("Thinking Query", value=query, height=80, 
                               disabled=True, key=f"think_query_{hash(query)}", 
                               label_visibility="collapsed")
                else:
                    self._render_structured_data(input_data)
            
            else:
                # Generic Strands SDK tool
                self._render_structured_data(input_data)
        
        except Exception as e:
            logger.error(f"Error rendering Strands SDK input for {tool_name}: {e}")
            self._render_structured_data(input_data)
    
    def _render_strands_sdk_output(self, tool_name: str, output_data: Dict) -> None:
        """
        Render Strands SDK tool output with specific formatting for each tool type.
        
        Args:
            tool_name: Name of the Strands SDK tool
            output_data: Output data
        """
        try:
            # Handle case where output_data might be a string
            if isinstance(output_data, str):
                if len(output_data) > 200:
                    st.text_area("Output", value=output_data, height=150, disabled=True, 
                               key=f"sdk_output_str_{hash(output_data)}", label_visibility="collapsed")
                else:
                    st.text(output_data)
                return
            
            # Ensure output_data is a dictionary
            if not isinstance(output_data, dict):
                st.write(f"**Output:** {str(output_data)}")
                return
            
            # Tool-specific output rendering
            if tool_name == "calculator":
                result = output_data.get("result")
                if result is not None:
                    st.metric("Result", str(result))
                else:
                    self._render_structured_data(output_data)
            
            elif tool_name == "file_read":
                content = output_data.get("content", "")
                if content:
                    if len(content) > 500:
                        st.text_area("File Content", value=content, height=200, disabled=True, 
                                   key=f"file_content_{hash(content)}", label_visibility="collapsed")
                    else:
                        st.text(content)
                else:
                    self._render_structured_data(output_data)
            
            elif tool_name == "file_write":
                success = output_data.get("success", False)
                message = output_data.get("message", "")
                if success:
                    st.success(f"✅ {message}" if message else "File written successfully")
                else:
                    st.error(f"❌ {message}" if message else "File write failed")
                
                if not message and not isinstance(success, bool):
                    self._render_structured_data(output_data)
            
            elif tool_name == "python_repl":
                stdout = output_data.get("stdout", "")
                stderr = output_data.get("stderr", "")
                
                if stdout:
                    st.write("**Output:**")
                    st.code(stdout, language="text")
                
                if stderr:
                    st.write("**Errors:**")
                    st.code(stderr, language="text")
                
                if not stdout and not stderr:
                    self._render_structured_data(output_data)
            
            elif tool_name == "shell":
                stdout = output_data.get("stdout", "")
                stderr = output_data.get("stderr", "")
                return_code = output_data.get("return_code")
                
                if return_code is not None:
                    status_color = "green" if return_code == 0 else "red"
                    st.markdown(f"**Exit Code:** <span style='color: {status_color}'>{return_code}</span>", 
                              unsafe_allow_html=True)
                
                if stdout:
                    st.write("**Output:**")
                    st.code(stdout, language="bash")
                
                if stderr:
                    st.write("**Errors:**")
                    st.code(stderr, language="bash")
                
                if not stdout and not stderr and return_code is None:
                    self._render_structured_data(output_data)
            
            elif tool_name == "http_request":
                status_code = output_data.get("status_code")
                content = output_data.get("content", "")
                
                if status_code:
                    status_color = "green" if 200 <= status_code < 300 else "red"
                    st.markdown(f"**Status:** <span style='color: {status_color}'>{status_code}</span>", 
                              unsafe_allow_html=True)
                
                if content:
                    if len(content) > 500:
                        st.text_area("Response Content", value=content, height=200, disabled=True, 
                                   key=f"http_content_{hash(content)}", label_visibility="collapsed")
                    else:
                        st.text(content)
                
                if not status_code and not content:
                    self._render_structured_data(output_data)
            
            elif tool_name == "think":
                thoughts = output_data.get("thoughts", "")
                if thoughts:
                    st.text_area("Thoughts", value=thoughts, height=120, disabled=True, 
                               key=f"think_output_{hash(thoughts)}", label_visibility="collapsed")
                else:
                    self._render_structured_data(output_data)
            
            else:
                # Generic Strands SDK tool
                self._render_structured_data(output_data)
        
        except Exception as e:
            logger.error(f"Error rendering Strands SDK output for {tool_name}: {e}")
            self._render_structured_data(output_data)
    
    def _render_mcp_input(self, tool_name: Optional[str], input_data: Dict) -> None:
        """
        Render MCP tool input with appropriate formatting.
        
        Args:
            tool_name: Name of the MCP tool
            input_data: Input parameters
        """
        try:
            # Show MCP server information if available
            server_name = input_data.get("server_name") or input_data.get("mcp_server")
            if server_name:
                st.write(f"**MCP Server:** {server_name}")
            
            # Show tool-specific parameters
            tool_params = {k: v for k, v in input_data.items() 
                          if k not in ["server_name", "mcp_server"]}
            
            if tool_params:
                st.write("**Parameters:**")
                for key, value in tool_params.items():
                    if isinstance(value, (str, int, float, bool)):
                        st.write(f"**{key}:** {value}")
                    else:
                        st.write(f"**{key}:**")
                        st.json(value)
            else:
                self._render_structured_data(input_data)
        
        except Exception as e:
            logger.error(f"Error rendering MCP input: {e}")
            self._render_structured_data(input_data)
    
    def _render_mcp_output(self, tool_name: Optional[str], output_data: Dict) -> None:
        """
        Render MCP tool output with appropriate formatting.
        
        Args:
            tool_name: Name of the MCP tool
            output_data: Output data
        """
        try:
            # Handle common MCP output patterns
            if "content" in output_data:
                content = output_data["content"]
                if isinstance(content, list):
                    for i, item in enumerate(content):
                        if isinstance(item, dict) and "text" in item:
                            st.text_area(f"Content {i+1}", value=item["text"], height=100, disabled=True, 
                                       key=f"mcp_content_{hash(str(item))}_{i}", label_visibility="collapsed")
                        else:
                            st.json(item)
                else:
                    st.text(str(content))
            
            elif "result" in output_data:
                result = output_data["result"]
                if isinstance(result, (str, int, float, bool)):
                    st.metric("Result", str(result))
                else:
                    st.json(result)
            
            else:
                # Generic MCP output
                self._render_structured_data(output_data)
        
        except Exception as e:
            logger.error(f"Error rendering MCP output: {e}")
            self._render_structured_data(output_data)
    
    def _render_custom_tool_input(self, tool_name: Optional[str], input_data: Dict) -> None:
        """
        Render custom agent-defined tool input.
        
        Args:
            tool_name: Name of the custom tool
            input_data: Input parameters
        """
        try:
            st.write(f"**Custom Tool:** {tool_name or 'Unknown'}")
            
            # Show parameters in a structured way
            if input_data:
                st.write("**Parameters:**")
                for key, value in input_data.items():
                    if isinstance(value, (str, int, float, bool)):
                        st.write(f"**{key}:** {value}")
                    else:
                        st.write(f"**{key}:**")
                        st.json(value)
            else:
                st.info("No input parameters")
        
        except Exception as e:
            logger.error(f"Error rendering custom tool input: {e}")
            self._render_structured_data(input_data)
    
    def _render_custom_tool_output(self, tool_name: Optional[str], output_data: Dict) -> None:
        """
        Render custom agent-defined tool output.
        
        Args:
            tool_name: Name of the custom tool
            output_data: Output data
        """
        try:
            # Generic custom tool output rendering
            self._render_structured_data(output_data)
        
        except Exception as e:
            logger.error(f"Error rendering custom tool output: {e}")
            self._render_structured_data(output_data)