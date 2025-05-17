#!/usr/bin/env python3
"""
Custom Tools Example

This example demonstrates how to add custom tools to the Strands Web UI.
"""

import streamlit as st
from strands import tool

# Import the app module
from strands_web_ui.app import main, initialize_agent
from strands_web_ui.utils.config_loader import load_config

# Define custom tools
@tool
def fetch_weather(location: str) -> dict:
    """
    Fetch weather information for a location.
    
    Args:
        location: The location to get weather for
        
    Returns:
        Weather information for the location
    """
    # This is a mock implementation
    import random
    conditions = ["sunny", "cloudy", "rainy", "snowy"]
    temperatures = range(0, 35)
    
    return {
        "status": "success",
        "content": [{
            "text": f"Weather for {location}: {random.choice(conditions)}, {random.choice(temperatures)}°C"
        }]
    }

@tool
def calculate_mortgage(principal: float, interest_rate: float, years: int) -> dict:
    """
    Calculate monthly mortgage payment.
    
    Args:
        principal: Loan amount
        interest_rate: Annual interest rate (as a percentage)
        years: Loan term in years
        
    Returns:
        Monthly payment information
    """
    # Convert annual interest rate to monthly rate
    monthly_rate = interest_rate / 100 / 12
    # Calculate number of payments
    payments = years * 12
    # Calculate monthly payment
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** payments) / ((1 + monthly_rate) ** payments - 1)
    
    return {
        "status": "success",
        "content": [{
            "text": f"Monthly payment: ${monthly_payment:.2f}\nTotal cost: ${monthly_payment * payments:.2f}"
        }]
    }

# Override the main function to add custom tools
def custom_main():
    """Custom main function with additional tools."""
    # Load configuration
    config = load_config()
    
    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        # Initialize MCP server manager
        from strands_web_ui.mcp_server_manager import MCPServerManager
        mcp_manager = MCPServerManager()
        mcp_manager.load_config("config/mcp_config.json")
        
        # Add custom tools
        custom_tools = [fetch_weather, calculate_mortgage]
        
        # Initialize agent with custom tools
        agent = initialize_agent(config, mcp_manager)
        agent.tools.extend(custom_tools)
        
        st.session_state.agent = agent
        st.session_state.mcp_manager = mcp_manager
    
    # Call the original main function
    main()

if __name__ == "__main__":
    custom_main()
