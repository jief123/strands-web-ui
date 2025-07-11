# Strands Web UI

A comprehensive Streamlit-based web interface for Strands Agents featuring advanced thinking process visualization, MCP integration, and audio transcription capabilities.

## Features

- 🤖 **Interactive Chat Interface**: Real-time streaming responses with configurable update intervals
- 💭 **Native Thinking Visualization**: Advanced visualization of agent thinking processes with configurable thinking budgets
- 📊 **Action History Display**: Comprehensive real-time tracking of all agent actions, tool usage, and reasoning processes
- 🔧 **Comprehensive Tool Integration**: Pre-built tools from Strands SDK including calculator, editor, file operations, Python REPL, shell, and workflow tools
- 🔌 **MCP Server Integration**: Full Model Context Protocol support for extended capabilities with dynamic server management
- 🎤 **Advanced Audio Transcription**: Multi-language audio transcription (MP3/WAV) with AWS Transcribe integration
- ⚙️ **Flexible Configuration**: JSON-based configuration system for models, agents, tools, and UI settings
- 💬 **Smart Conversation Management**: Sliding window conversation history with configurable window sizes
- 🌐 **Multi-Model Support**: Support for Claude 3.5 Sonnet, Haiku, Amazon Nova, and Meta Llama models
- 🎛️ **Real-time Configuration**: Dynamic model and tool configuration through the sidebar interface

## Installation

### Prerequisites

- Python 3.10 or higher
- AWS credentials configured for Bedrock and Transcribe services
- [Streamlit](https://streamlit.io/) >= 1.30.0
- [Strands Agents SDK](https://github.com/strands-agents/sdk-python) >= 0.1.1
- [MCP](https://github.com/model-context-protocol/mcp) >= 0.1.0

### Core Dependencies

```bash
pip install streamlit>=1.30.0
pip install strands-agents>=0.1.1
pip install mcp>=0.1.0
```

### Audio Transcription Dependencies (Optional)

For audio transcription features:

```bash
pip install boto3>=1.26.0
pip install pydub>=0.25.1
pip install amazon-transcribe>=0.6.0
```

### Installation Methods

#### Install from Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/jief123/strands-web-ui.git
cd strands-web-ui

# Install all dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

#### Quick Install (All Dependencies)

```bash
# Install all dependencies at once
pip install streamlit>=1.30.0 strands-agents>=0.1.1 mcp>=0.1.0 boto3>=1.26.0 pydub>=0.25.1 amazon-transcribe>=0.6.0
```

## Usage

### Quick Start

After installation, you can run the application:

```bash
# Method 1: Run directly with Streamlit
streamlit run app.py

# Method 2: Run from the source directory
cd src/strands_web_ui
streamlit run app.py

# Method 3: Run as a module (if installed)
python -m streamlit run src/strands_web_ui/app.py
```

### AWS Configuration

Ensure your AWS credentials are configured for Bedrock and Transcribe services:

```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### First Run

1. Start the application with `streamlit run app.py`
2. Configure your preferred model and settings in the sidebar
3. Enable desired tools from the tool configuration section
4. Start chatting with the agent!

## Configuration

The application uses a comprehensive JSON-based configuration system located in the `config` directory:

- `config/config.json`: Main configuration file with model, agent, tools, and UI settings
- `config/mcp_config.json`: MCP server configuration for external tool integration

### Model Configuration

Configure the model provider, model ID, region, token limits, and streaming behavior:

```json
{
  "model": {
    "provider": "bedrock",
    "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "region": "us-west-2",
    "max_tokens": 24000,
    "enable_streaming": true
  }
}
```

**Supported Models:**
- `us.anthropic.claude-3-7-sonnet-20250219-v1:0` (Claude 3.5 Sonnet)
- `us.anthropic.claude-3-5-sonnet-20241022-v2:0` (Claude 3.5 Sonnet v2)
- `anthropic.claude-3-haiku-20240307-v1:0` (Claude 3 Haiku)
- `us.anthropic.claude-3-5-haiku-20241022-v1:0` (Claude 3.5 Haiku)
- `us.amazon.nova-premier-v1:0` (Amazon Nova Premier)
- `us.amazon.nova-pro-v1:0` (Amazon Nova Pro)
- `us.amazon.nova-lite-v1:0` (Amazon Nova Lite)
- `us.meta.llama4-maverick-17b-instruct-v1:0` (Meta Llama 4 Maverick)
- `us.meta.llama4-scout-17b-instruct-v1:0` (Meta Llama 4 Scout)

### Agent Configuration

Configure the system prompt, tool execution, and native thinking capabilities:

```json
{
  "agent": {
    "system_prompt": "You are a helpful assistant that provides concise, accurate information.",
    "max_parallel_tools": 4,
    "record_direct_tool_call": true,
    "hot_reload_tools": true,
    "enable_native_thinking": true,
    "thinking_budget": 16000
  }
}
```

**Key Settings:**
- `enable_native_thinking`: Enable Claude's native thinking capabilities
- `thinking_budget`: Token budget allocated for thinking processes
- `max_parallel_tools`: Maximum number of tools that can run simultaneously
- `hot_reload_tools`: Enable dynamic tool reloading

### Tools Configuration

Configure which pre-built tools are available to the agent:

```json
{
  "tools": {
    "enabled": [
      "calculator",
      "editor", 
      "environment",
      "file_read",
      "file_write",
      "http_request",
      "python_repl",
      "shell",
      "think",
      "workflow"
    ],
    "options": {
      "python_repl": {
        "timeout": 10
      },
      "http_request": {
        "max_retries": 3
      }
    }
  }
}
```

**Available Tools:**
- `calculator`: Mathematical calculations
- `editor`: Text editing operations
- `environment`: Environment variable access
- `file_read`/`file_write`: File system operations
- `http_request`: HTTP requests and API calls
- `python_repl`: Python code execution
- `shell`: Command line operations
- `think`: Structured thinking processes
- `workflow`: Workflow management

### Conversation Management

Configure conversation history and window management:

```json
{
  "conversation": {
    "window_size": 20,
    "summarize_overflow": true
  }
}
```

### UI Configuration

Configure user interface behavior:

```json
{
  "ui": {
    "update_interval": 0.1
  }
}
```

## Audio Transcription Feature

Strands Web UI includes advanced audio transcription capabilities using AWS Transcribe:

### Supported Features

- 🎤 **Multi-format Support**: MP3 and WAV audio files
- 🌍 **Multi-language Detection**: Automatic language detection with support for:
  - English (en-US)
  - Indonesian (id-ID) 
  - Chinese (zh-CN)
  - Japanese (ja-JP)
  - Korean (ko-KR)
  - Thai (th-TH)
- 🔄 **Real-time Processing**: Live transcription with progress indicators
- 🤖 **Agent Integration**: Transcribed text is automatically combined with user input

### Usage

1. Click the "📎 Attach Audio File" button in the chat interface
2. Upload your MP3 or WAV file
3. Select language detection options and AWS region
4. Add your text prompt (optional)
5. The audio will be transcribed and processed together with your text input

### Configuration

Audio transcription requires AWS Transcribe service access. Configure your AWS region in the upload dialog or set it globally in your AWS configuration.

## Action History Feature

Comprehensive real-time tracking and visualization of all agent actions, providing complete transparency into the agent's workflow and decision-making process.

### What is Action History?

Action History captures and displays:
- **🛠️ Tool Usage**: Every tool the agent uses (Strands SDK tools, MCP tools, custom tools)
- **🧠 Reasoning Events**: The agent's thinking process before taking actions
- **📊 Performance Metrics**: Timing information, success/failure status, and execution duration
- **🔄 Turn Organization**: Actions grouped by conversation turns for easy navigation

### Key Features

#### Real-Time Display
- Actions appear instantly as the agent works
- Live updates without page refresh
- Turn-based organization for easy navigation
- Expandable/collapsible sections for focused viewing

#### Tool Categorization
- **🔧 Strands SDK Tools**: Built-in tools (calculator, editor, file operations, Python REPL, shell, workflow)
- **🔌 MCP Tools**: External tools from Model Context Protocol servers with server identification
- **⚙️ Custom Tools**: Agent-defined tools for specific tasks

#### Rich Visualization
- Tool-specific input/output formatting
- Syntax highlighting for code and commands
- File path displays and content previews
- HTTP request/response formatting
- Mathematical expression rendering

#### Performance Analysis
- Execution time for each tool
- Success/failure indicators
- Tool usage statistics and patterns
- Average duration calculations
- Error tracking and analysis

### Usage

#### Getting Started
1. The Action History panel appears automatically in the sidebar
2. Ask the agent to perform tasks that use tools (e.g., "Calculate 15 * 23" or "Read the README file")
3. Watch actions populate in real-time as the agent works
4. Click on action cards to see detailed input/output information

#### Interactive Controls
- **👁️ Toggle**: Show/hide the entire action history panel
- **📊 Summary**: View detailed statistics and performance metrics
- **🗑️ Clear**: Remove all captured actions from current session
- **🔄 Refresh**: Update the display
- **❓ Help**: Access inline help and feature explanations

#### Understanding the Display

**Turn Organization**: Actions are grouped by conversation turns
- Each user message starts a new turn
- Most recent turn is expanded by default
- Historical turns can be expanded for review

**Action Cards**: Each action shows:
- Tool name and category with appropriate icons
- Execution timestamp and duration
- Success/failure status with color coding
- Input parameters and output results
- Associated reasoning context when available

**Status Indicators**:
- 🟢 Green dot = Successful execution
- 🔴 Red dot = Failed execution
- Duration shows execution time in seconds

### Tool-Specific Features

#### Calculator Tool
- Mathematical expression display
- Result metrics with formatted output
- Error handling for invalid expressions

#### File Operations
- File path display with folder icons
- Content preview for large files
- Success/failure indicators for write operations

#### Python REPL
- Syntax-highlighted code display
- Separate stdout/stderr output sections
- Error message formatting

#### Shell Commands
- Command display with bash syntax highlighting
- Exit code indicators with color coding
- Separate output and error streams

#### HTTP Requests
- Clickable URL links
- Request method and headers display
- Response status codes with color coding
- Response content preview

#### MCP Tools
- Server source identification
- Tool-specific parameter formatting
- Server connection status indicators

### Configuration and Customization

#### Display Preferences
The Action History display can be customized through the UI:
- Panel visibility (show/hide)
- Summary mode (detailed statistics vs. simple view)
- Auto-expansion settings
- Compact mode for large datasets

#### Performance Settings
For optimal performance with long conversations:
- Automatic cleanup of old actions
- Configurable action limits
- Lazy loading for large datasets
- Memory usage optimization

### Privacy and Data Handling

#### Data Storage
- Action history is stored only in your browser session
- No data is sent to external servers
- History is automatically cleared when starting new conversations
- Data does not persist between browser sessions

#### Security Considerations
- Tool parameters and results are displayed in the UI
- Be aware of sensitive information visibility
- Clear history when working with confidential data
- No external logging of action data

### Troubleshooting

#### Common Issues

**Actions Not Appearing**:
- Ensure the Action History panel is expanded (👁️ button)
- Verify the agent is actually using tools
- Try asking for a simple calculation: "What is 2+2?"

**Performance Issues**:
- Clear action history using the 🗑️ button
- Reduce conversation length
- Check browser memory usage

**Display Problems**:
- Refresh the page if display seems stuck
- Try a different browser (Chrome recommended)
- Check browser console for JavaScript errors

#### Getting Help
- Click the ❓ help button in the Action History header
- Review the inline tooltips and help text
- Check browser developer console for error messages

### Best Practices

#### For Developers
- Use Action History to debug complex agent workflows
- Monitor tool performance to optimize agent behavior
- Review error patterns to improve error handling
- Document common workflows based on action patterns

#### For Users
- Keep the panel open during complex tasks to monitor progress
- Review failed actions to understand what went wrong
- Use timing information to set realistic expectations
- Collapse completed turns to focus on current actions

## MCP Server Integration

Full Model Context Protocol (MCP) support for extending agent capabilities:

### Configuration

Configure MCP servers in `config/mcp_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"],
      "env": {}
    },
    "brave-search": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Management

- **Dynamic Connection**: Connect/disconnect servers through the sidebar interface
- **Tool Discovery**: Automatically discover and integrate tools from connected servers
- **Status Monitoring**: Real-time server status and connection monitoring
- **Configuration Reload**: Hot-reload MCP configuration without restarting the application

## Project Structure

```
strands_web_ui/
├── config/                          # Configuration files
│   ├── config.json                  # Main application configuration
│   └── mcp_config.json             # MCP server configurations
├── docs/                           # Documentation
│   ├── action_history_developer_guide.md # Developer guide for action history
│   ├── audio_transcription_guide.md
│   └── integrated_audio_feature.md
├── src/                            # Source code
│   └── strands_web_ui/
│       ├── __init__.py
│       ├── app.py                  # Main Streamlit application
│       ├── mcp_server_manager.py   # MCP server management
│       ├── action_history/         # Action history tracking system
│       │   ├── __init__.py
│       │   ├── capture.py          # Event capture and processing
│       │   └── display.py          # UI display components
│       ├── extensions/             # Feature extensions
│       │   ├── __init__.py
│       │   └── audio_transcriber.py # Audio transcription functionality
│       ├── handlers/               # Event handlers
│       │   ├── __init__.py
│       │   ├── streamlit_handler.py # Basic Streamlit event handling
│       │   ├── clean_response_handler.py # Clean UI display handler
│       │   └── enhanced_streamlit_handler.py # Composite handler with action capture
│       ├── tools/                  # Custom tools
│       │   └── __init__.py
│       └── utils/                  # Utility functions
│           ├── __init__.py
│           ├── config_loader.py    # Configuration loading
│           ├── custom_logger.py    # Logging utilities
│           ├── session_state_manager.py # Session state management
│           └── tool_loader.py      # Tool loading and management
├── static/                         # Static assets
├── tests/                          # Test files
├── workflows/                      # Workflow definitions
├── logs/                          # Application logs
├── repl_state/                    # Python REPL state persistence
├── app.py                         # Entry point (symlink to src/strands_web_ui/app.py)
├── requirements.txt               # Python dependencies
├── pyproject.toml                # Project configuration
├── introduction.md               # Project introduction (Chinese)
├── LICENSE                       # MIT License
├── README.md                     # This file
├── CONTRIBUTING.md              # Contribution guidelines
└── CODE_OF_CONDUCT.md          # Code of conduct
```

## Key Features in Detail

### Native Thinking Visualization

The application showcases Strands SDK's native thinking capabilities:

- **Real-time Thinking Display**: Watch the agent's reasoning process unfold in real-time
- **Configurable Thinking Budget**: Control how much computational power is allocated to thinking
- **Expandable Thinking Sections**: Click to expand and explore the agent's thought process
- **Thinking History**: Maintain a history of thinking processes for each conversation

### Advanced Tool Integration

Comprehensive integration with Strands SDK's pre-built tools:

- **Dynamic Tool Loading**: Tools are loaded based on configuration settings
- **Parallel Tool Execution**: Multiple tools can run simultaneously for efficiency
- **Tool Result Visualization**: Clear display of tool execution results
- **Hot Reload**: Tools can be enabled/disabled without restarting the application

### Streaming Response System

Sophisticated streaming implementation:

- **Real-time Updates**: Responses stream in real-time with configurable update intervals
- **Non-blocking UI**: Interface remains responsive during long operations
- **Progress Indicators**: Visual feedback for ongoing operations
- **Graceful Error Handling**: Robust error handling with user-friendly messages

### Configuration Management

Flexible configuration system:

- **JSON-based Configuration**: Easy-to-edit configuration files
- **Runtime Configuration**: Change settings through the UI without restarting
- **Configuration Validation**: Automatic validation of configuration parameters
- **Default Fallbacks**: Sensible defaults for all configuration options

## How It Works

This application demonstrates advanced integration patterns with the Strands SDK:

### 1. Agent Initialization
- Creates a BedrockModel with configurable parameters
- Sets up SlidingWindowConversationManager for context management
- Initializes the Agent with tools, system prompt, and callback handlers

### 2. Advanced Response Handling Architecture
- **EnhancedStreamlitHandler**: Composite handler that combines UI display with action history capture
- **CleanResponseHandler**: Provides clean UI display by filtering out reasoning content (default)
- **StreamlitHandler**: Basic streaming display option (alternative)
- **ActionCaptureHandler**: Captures all agent actions for real-time action history tracking
- Manages thinking process visualization separately from main responses
- Handles both streaming and non-streaming modes seamlessly

### 3. Tool Management
- Dynamically loads tools based on configuration
- Integrates both SDK tools and MCP server tools
- Provides real-time tool status and management

### 4. Audio Processing Pipeline
- Uploads and temporarily stores audio files
- Processes audio through AWS Transcribe
- Combines transcription results with user text input
- Provides comprehensive error handling and user feedback

### 5. MCP Integration
- Manages multiple MCP server connections
- Dynamically discovers and integrates external tools
- Provides real-time server status monitoring
- Handles server lifecycle management

The application serves as a comprehensive reference implementation for building production-ready Strands SDK applications with advanced features like audio processing, external tool integration, and sophisticated UI interactions.

## Development and Testing

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/jief123/strands-web-ui.git
cd strands-web-ui

# Install development dependencies
pip install -e .
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run the application
streamlit run app.py
```

### Testing Audio Integration

The project includes comprehensive audio integration tests:

```bash
# Run audio transcription tests
python test_audio_integration.py

# Test tool loading
python test_tool_loading.py
```

### Configuration Testing

Test different configurations by modifying `config/config.json`:

```bash
# Test with different models
# Test with different tool combinations  
# Test with different thinking budgets
# Test streaming vs non-streaming modes
```

## Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure AWS credentials are properly configured for Bedrock and Transcribe
2. **Audio Dependencies**: Install `pydub` and `amazon-transcribe` for audio features
3. **MCP Servers**: Verify MCP server commands and paths in `mcp_config.json`
4. **Model Access**: Ensure you have access to the specified Bedrock models in your AWS account

### Debug Mode

Enable debug logging by setting the log level in the application:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

- Adjust `thinking_budget` based on your use case
- Configure `max_parallel_tools` based on your system capabilities
- Tune `update_interval` for optimal streaming performance
- Use appropriate `window_size` for conversation management

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- Code style guidelines
- Testing requirements
- Pull request process
- Issue reporting

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Strands Agents SDK](https://github.com/strands-agents/sdk-python)
- Powered by [Streamlit](https://streamlit.io/)
- Integrates with [Model Context Protocol (MCP)](https://github.com/model-context-protocol/mcp)
- Audio transcription via AWS Transcribe
