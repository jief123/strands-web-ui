#!/usr/bin/env python3
"""
Debug script to test action capture functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from strands_web_ui.utils import SessionStateManager
from strands_web_ui.action_history import ActionEvent
from datetime import datetime

def test_action_capture():
    print("🔍 Testing Action Capture...")
    
    # Initialize session state
    SessionStateManager.initialize_session_state()
    
    # Create a test action
    test_action = ActionEvent(
        id="debug_001",
        turn=1,
        timestamp=datetime.now(),
        action_type="tool_use",
        tool_name="calculator",
        tool_source="strands_sdk",
        tool_use_id="debug_001",
        input_data={"expression": "132 * 23"},
        output_data={"result": 3036},
        status="success",
        duration=0.15
    )
    
    print(f"Created test action: {test_action.tool_name}")
    
    # Add to session state
    SessionStateManager.add_action(test_action)
    print("Added action to session state")
    
    # Retrieve actions
    actions = SessionStateManager.get_action_history()
    print(f"Retrieved {len(actions)} actions from session state")
    
    if actions:
        action = actions[0]
        print(f"Action details: {action.tool_name} - {action.input_data} -> {action.output_data}")
    
    # Get summary
    summary = SessionStateManager.get_session_summary()
    print(f"Session summary: {summary}")
    
    return len(actions) > 0

if __name__ == "__main__":
    success = test_action_capture()
    print(f"✅ Test {'passed' if success else 'failed'}")