#!/usr/bin/env python3
"""
Strands Agent Streamlit Demo with MCP Integration

This example demonstrates how to create a simple chat interface for a Strands agent using Streamlit
with Model Context Protocol (MCP) server integration.

Run with:
    streamlit run app.py
"""

import os
import time
import logging
import streamlit as st
from strands import Agent, tool
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager

from strands_web_ui.mcp_server_manager import MCPServerManager
from strands_web_ui.handlers.streamlit_handler import StreamlitHandler
from strands_web_ui.utils.config_loader import load_config, load_mcp_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define some example tools
@tool
def search_knowledge_base(query: str) -> dict:
    """
    Search the knowledge base for information.
    
    Args:
        query: The search query
        
    Returns:
        Relevant information from the knowledge base
    """
    # Simulate search delay
    time.sleep(1)
    return {
        "status": "success",
        "content": [{"text": f"Found information about: {query}. This is simulated knowledge base content."}]
    }

def initialize_agent(config, mcp_manager=None):
    """
    Initialize the Strands agent with the given configuration.
    
    Args:
        config: Agent configuration
        mcp_manager: MCP server manager for additional tools
        
    Returns:
        Agent: Initialized Strands agent
    """
    # Create model based on config
    model_config = config.get("model", {})
    
    # Add native thinking parameter if enabled
    additional_request_fields = {}
    agent_config = config.get("agent", {})
    if agent_config.get("enable_native_thinking", False):
        # Get thinking budget from config or use default
        thinking_budget = agent_config.get("thinking_budget", 16000)
        # Get max_tokens from model config or use default (1.5x thinking budget)
        max_tokens = model_config.get("max_tokens", int(thinking_budget * 1.5))
        
        additional_request_fields = {
            "max_tokens": max_tokens,
            "thinking": {
                "type": "enabled",
                "budget_tokens": thinking_budget
            }
        }
    
    model = BedrockModel(
        model_id=model_config.get("model_id", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"),
        region=model_config.get("region", "us-east-1"),
        additional_request_fields=additional_request_fields
    )
    
    # Get tools from MCP servers if available
    tools = [search_knowledge_base]
    if mcp_manager:
        mcp_tools = mcp_manager.get_all_tools()
        tools.extend(mcp_tools)
    
    # Create conversation manager with window size from config
    conversation_config = config.get("conversation", {})
    window_size = conversation_config.get("window_size", 20)
    conversation_manager = SlidingWindowConversationManager(window_size=window_size)
    
    # Initialize agent with conversation manager
    return Agent(
        model=model,
        system_prompt=agent_config.get("system_prompt"),
        tools=tools,
        max_parallel_tools=agent_config.get("max_parallel_tools", os.cpu_count() or 1),
        record_direct_tool_call=agent_config.get("record_direct_tool_call", True),
        load_tools_from_directory=agent_config.get("hot_reload_tools", True),
        conversation_manager=conversation_manager,
        callback_handler=None  # Will be set per interaction
    )

def extract_response_text(response):
    """
    Extract text from the agent's response object.
    
    Args:
        response: Agent response object
        
    Returns:
        str: Extracted text from the response
    """
    # If it's an AgentResult object
    if hasattr(response, 'message'):
        message = response.message
        if isinstance(message, dict) and 'content' in message:
            content = message['content']
            if isinstance(content, list):
                return ''.join(block.get('text', '') for block in content 
                              if isinstance(block, dict) and 'text' in block)
    
    # Handle dictionary format
    if isinstance(response, dict):
        if 'message' in response:
            message = response['message']
            if isinstance(message, dict) and 'content' in message:
                content = message['content']
                if isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict) and 'text' in content[0]:
                        return content[0]['text']
        elif 'final_message' in response:
            final_message = response['final_message']
            if isinstance(final_message, dict) and 'content' in final_message:
                content_blocks = final_message['content']
                return ''.join(block.get('text', '') for block in content_blocks 
                              if isinstance(block, dict) and 'text' in block)
    
    # If we have a get_message_as_string method, use it
    if hasattr(response, 'get_message_as_string'):
        return response.get_message_as_string()
    
    # Fallback
    return str(response)

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Strands Agent Chat with MCP Integration",
        page_icon="🤖",
        layout="wide"
    )
    
    # Load configuration
    config = load_config()
    
    # Initialize MCP server manager
    if "mcp_manager" not in st.session_state:
        st.session_state.mcp_manager = MCPServerManager()
        # Load MCP server configurations
        st.session_state.mcp_manager.load_config("config/mcp_config.json")
    
    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        st.session_state.agent = initialize_agent(config, st.session_state.mcp_manager)
        
    if "processing" not in st.session_state:
        st.session_state.processing = False
    
    if "config" not in st.session_state:
        st.session_state.config = config
        
    if "thinking_history" not in st.session_state:
        st.session_state.thinking_history = []
    
    st.title("🤖 Strands Agent Chat with MCP Integration")
    st.markdown("""
    This demo showcases a Strands agent with streaming responses, tool execution, and MCP server integration.
    You can connect to MCP servers to extend the agent's capabilities with additional tools.
    """)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Agent Configuration")
        
        system_prompt = st.text_area(
            "System Prompt",
            value=config["agent"]["system_prompt"],
            height=100
        )
        
        # Add region selection
        region = st.selectbox(
            "AWS Region",
            options=["us-east-1", "us-west-2", "eu-central-1", "ap-southeast-1"],
            index=0
        )
        
        # Add model selection
        model_id = st.selectbox(
            "Model",
            options=[
                "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                "anthropic.claude-3-sonnet-20240229-v1:0",
                "anthropic.claude-3-haiku-20240307-v1:0"
            ],
            index=0
        )
        
        # Add native thinking toggle
        enable_native_thinking = st.checkbox(
            "Enable Native Thinking",
            value=config["agent"].get("enable_native_thinking", True)
        )
        
        # Add conversation window size slider
        window_size = st.slider(
            "Conversation Window Size",
            min_value=5,
            max_value=50,
            value=config["conversation"].get("window_size", 20),
            step=1,
            help="Maximum number of messages to keep in conversation history"
        )
        
        if st.button("Apply Configuration"):
            # Update config
            config["model"]["region"] = region
            config["model"]["model_id"] = model_id
            config["agent"]["system_prompt"] = system_prompt
            config["agent"]["enable_native_thinking"] = enable_native_thinking
            config["conversation"]["window_size"] = window_size
            
            # Update session state
            st.session_state.config = config
            st.session_state.agent = initialize_agent(config, st.session_state.mcp_manager)
            st.success("Configuration applied!")
        
        st.divider()
        
        # MCP Server Configuration
        st.header("MCP Server Configuration")
        
        # Display configured servers
        mcp_manager = st.session_state.mcp_manager
        server_ids = mcp_manager.get_server_ids()
        
        if server_ids:
            for server_id in server_ids:
                status = mcp_manager.get_server_status(server_id)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if status.get('connected', False):
                        st.write(f"✅ {server_id}")
                    else:
                        st.write(f"⚪ {server_id}")
                
                with col2:
                    if status.get('connected', False):
                        if st.button(f"Disconnect", key=f"disconnect_{server_id}"):
                            if mcp_manager.disconnect_server(server_id):
                                st.success(f"Disconnected from {server_id}")
                                # Reinitialize agent with updated tools
                                st.session_state.agent = initialize_agent(
                                    st.session_state.config, 
                                    mcp_manager
                                )
                            else:
                                st.error(f"Failed to disconnect from {server_id}")
                    else:
                        if st.button(f"Connect", key=f"connect_{server_id}"):
                            if mcp_manager.connect_server(server_id):
                                st.success(f"Connected to {server_id}")
                                # Reinitialize agent with new tools
                                st.session_state.agent = initialize_agent(
                                    st.session_state.config, 
                                    mcp_manager
                                )
                            else:
                                st.error(f"Failed to connect to {server_id}")
                
                # Display server details
                with st.expander(f"Server details: {server_id}"):
                    st.write(f"Command: {status.get('command', 'N/A')}")
                    st.write(f"Args: {', '.join(status.get('args', []))}")
                    st.write(f"Status: {'Connected' if status.get('connected', False) else 'Disconnected'}")
        else:
            st.info("No MCP servers configured. Edit the mcp_config.json file to add servers.")
        
        # Reload configuration button
        if st.button("Reload MCP Configuration"):
            if mcp_manager.load_config("config/mcp_config.json"):
                st.success("MCP configuration reloaded")
            else:
                st.error("Failed to reload MCP configuration")
    
    # Display conversation history with thinking processes
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # If this is an assistant message, check if there's thinking history for the previous question
            if message["role"] == "assistant" and i > 0:  # Make sure there's a previous message
                # Find thinking content for the previous question (user message)
                for thinking_item in st.session_state.thinking_history:
                    if thinking_item["question_idx"] == i-1:  # i-1 is the index of the user message
                        # Display the thinking content
                        with st.expander("💭 Thinking Process", expanded=False):
                            st.markdown(f"""
                            <div style="background-color: rgba(67, 97, 238, 0.1); padding: 10px; border-left: 4px solid #4361ee; border-radius: 4px; color: var(--text-color, currentColor);">
                            {thinking_item["content"]}
                            </div>
                            """, unsafe_allow_html=True)
                        break
    
    # Get user input
    user_input = st.chat_input("Ask something...", disabled=st.session_state.processing)
    
    if user_input:
        # Set processing flag to prevent multiple submissions
        st.session_state.processing = True
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Create a placeholder for the streaming response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # Get UI config
            ui_config = st.session_state.config.get("ui", {})
            update_interval = ui_config.get("update_interval", 0.1)
            
            # Create improved stream handler
            stream_handler = StreamlitHandler(
                placeholder=response_placeholder,
                update_interval=update_interval
            )
            
            try:
                # Use the existing agent instance from session state
                # This ensures conversation history is maintained
                agent = st.session_state.agent
                
                # Set the callback handler for this interaction
                agent.callback_handler = stream_handler
                
                # Process with agent - this will trigger streaming through the handler
                response = agent(user_input)
                
                # Extract the final response text
                response_text = extract_response_text(response)
                
                # If no streaming occurred, show the full response
                if not stream_handler.message_container:
                    response_placeholder.markdown(response_text)
                else:
                    # Ensure the final complete response is displayed
                    response_placeholder.markdown(stream_handler.message_container)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response_text or stream_handler.message_container})
                
                # Make sure thinking content is preserved after the response
                if stream_handler.thinking_container and not stream_handler.thinking_preserved:
                    stream_handler._preserve_thinking_content()
                
            except Exception as e:
                # Handle errors gracefully
                error_message = f"Error: {str(e)}"
                response_placeholder.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            
            finally:
                # Reset processing flag
                st.session_state.processing = False

if __name__ == "__main__":
    main()
