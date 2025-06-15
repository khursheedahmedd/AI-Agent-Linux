# Sadain CLI - AI Terminal Assistant

Sadain is a terminal-based AI assistant designed to help you with shell commands, answer questions, and eventually act as an intelligent agent in your terminal. Built with Trae AI IDE and powered by Novita's advanced language models.

This is an early version focusing on core functionality with Novita and LangGraph.

## Prerequisites

- Python 3.9+
- A Novita AI API Key (Get it from: https://novita.ai/settings/key-management)
- For voice mode:
  - PyAudio
  - A working microphone
  - Internet connection (for speech recognition)

## Installation

1.  **Clone the repository:**

    ```bash
    https://github.com/khursheedahmedd/sadain-cli.git
    cd sadain-cli
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

5.  **Set your Novita AI API Key:**
    - Create a file named `.env` in the project root (`sadain_cli/.env`) OR in `~/.config/sadain/.env`
    - Add your API key to it:
      ```
      NOVITA_API_KEY="your_actual_novita_api_key"
      ```
    - Alternatively, Sadain will prompt you for the key on first run if it's not found.

## Technology Stack

- **Trae AI IDE**: Built and developed using Trae AI IDE for enhanced development experience
- **Novita AI**: Powered by Novita's advanced language models for natural language processing
- **LangGraph**: For building and managing complex AI workflows
- **Python**: Core programming language
- **Typer**: For building the CLI interface
- **Rich**: For beautiful terminal formatting

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

**Undo Feature:**

```bash
sadain --undo
```

**Command History:**

```bash
sadain --history
```

## Features

- Chat-based interaction powered by Novita's advanced language models
- Command execution in agent mode
- Voice command support
- Cross-platform compatibility
- Context-aware responses
- Rich terminal formatting
- Error handling and recovery
- File operation safety
- API key management
- Command history
- Undo support

## Voice Mode Tips

- Speak clearly and at a moderate pace
- Ensure your microphone is properly configured
- Use voice mode in a quiet environment for better recognition
- You can say "quit" or "exit" to end the voice session
- The assistant will respond both in text and voice
- Voice mode works best for queries and simple commands

## Requirements

- Python 3.9+
- Novita AI API key (set as NOVITA_API_KEY environment variable)
- For voice mode:
  - Working microphone
  - Internet connection
  - PyAudio
  - SpeechRecognition
  - pyttsx3

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT License

## Acknowledgments

- Built with [Trae AI IDE](https://trae.ai)
- Powered by [Novita AI](https://novita.ai)
- Inspired by the need for a more intelligent terminal assistant
