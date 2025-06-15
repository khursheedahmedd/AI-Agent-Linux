# Sadain CLI - AI Terminal Assistant

Sadain is a terminal-based AI assistant designed to help you with shell commands, answer questions, and eventually act as an intelligent agent in your terminal.

This is an early version focusing on core functionality with Groq and LangGraph.

## Prerequisites

- Python 3.9+
- A Groq API Key
- For voice mode:
  - PyAudio
  - A working microphone
  - Internet connection (for speech recognition)

## Installation

1.  **Clone the repository (if not installing from PyPI later):**

    ```bash
    # git clone https://github.com/yourusername/sadain-cli.git
    # cd sadain-cli
    ```

2.  **Set up a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Install the package locally for development:**

    ```bash
    pip install -e .
    ```

    This makes the `sadain` command available in your current environment.

5.  **Set your Groq API Key:**
    - Create a file named `.env` in the project root (`sadain_cli/.env`) OR in `~/.config/sadain/.env`
    - Add your API key to it:
      ```
      GROQ_API_KEY="your_actual_groq_api_key"
      ```
    - Alternatively, Sadain will prompt you for the key on first run if it's not found.

## Usage

**Chat Mode (default):**

```bash
sadain "What is the capital of Sweden?"
sadain "Explain the `tar` command with an example."
```

**Agent Mode:**

```bash
sadain -a "List all python files in the current directory"
sadain --agent "Create a new file called test.py"
```

**Voice Mode:**

```bash
sadain --voice
```

In voice mode:

1. Press Enter to start speaking
2. Speak your command
3. Press any key to stop listening
4. The assistant will respond both in text and voice

**Combining Modes:**

```bash
# Voice mode with agent capabilities
sadain --voice -a

# Voice mode with verbose output
sadain --voice -v

# Voice mode with context disabled
sadain --voice -c false
```

## Features

- Chat-based interaction
- Command execution in agent mode
- Voice command support
- Cross-platform compatibility
- Context-aware responses
- Rich terminal formatting
- Error handling and recovery
- File operation safety
- API key management

## Voice Mode Tips

- Speak clearly and at a moderate pace
- Ensure your microphone is properly configured
- Use voice mode in a quiet environment for better recognition
- You can say "quit" or "exit" to end the voice session
- The assistant will respond both in text and voice
- Voice mode works best for queries and simple commands
