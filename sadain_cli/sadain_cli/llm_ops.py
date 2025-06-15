from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from .config import load_api_key
from rich.console import Console
from .utils import get_current_context


console = Console()

class GroqLLM:
    def __init__(self, model_name="llama3-8b-8192", temperature=0.1):
        self.api_key = load_api_key()
        if not self.api_key:
            raise ValueError("Groq API Key not found or provided.")
        
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=model_name,
            temperature=temperature
        )
        self.output_parser = StrOutputParser()

    def get_chat_chain(self, system_prompt: str):
        """Create a chat chain with the given system prompt."""
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        return prompt_template | self.llm | self.output_parser

    def invoke_chat(self, system_prompt: str, user_input: str, chat_history: list = None):
        """Invoke the chat with the given system prompt and user input."""
        if chat_history is None:
            chat_history = []
        
        try:
            chain = self.get_chat_chain(system_prompt)
            response = chain.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            return response
        except Exception as e:
            console.print(f"[bold red]Error communicating with Groq API: {e}[/bold red]")
            return None

if __name__ == "__main__":
    try:
        groq_llm = GroqLLM()
        
        system_prompt_chat = "You are a helpful AI assistant."
        response_chat = groq_llm.invoke_chat(system_prompt_chat, "What is the capital of France?")
        if response_chat:
            console.print(f"[bold green]Chat Response:[/bold green]\n{response_chat}")

        system_prompt_agent = """
You are an expert Linux terminal assistant. Your goal is to understand the user's request
and provide ONE or MORE shell commands to achieve it.

If the user asks a question that doesn't require a command, answer it directly.

IMPORTANT FORMATTING:
If you provide shell commands, enclose EACH command in its own triple backticks block, like this:
```bash
echo "This is one command"
 ls -la

If you need to explain something or ask for clarification, do so outside of the backtick blocks.
Do not add any conversational fluff before or after the command blocks if commands are the primary output.
Just provide the commands.
User's current context:
{context}
"""
        current_context = get_current_context()
        user_query = "List all python files in the current directory and then count them."
        response_agent = groq_llm.invoke_chat(
                system_prompt_agent.format(context=current_context),
                user_query
            )
        if response_agent:
            console.print(f"\n[bold green]Agent Command Suggestion Response:[/bold green]\n{response_agent}")

    except ValueError as e:
        console.print(f"[bold red]{e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")