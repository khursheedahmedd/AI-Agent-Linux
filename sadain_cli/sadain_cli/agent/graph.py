from langgraph.graph import StateGraph, END
from .nodes import (
    AgentState, 
    generate_initial_response, 
    parse_commands, 
    execute_parsed_commands,
    format_final_output
)
from rich.console import Console

console = Console()

def should_execute_commands(state: AgentState) -> str:
    if state["is_agent_mode"] and state["extracted_commands"]:
        return "execute"
    return "format_direct"


def create_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Define the nodes
    graph.add_node("generate_response", generate_initial_response)
    graph.add_node("parse_commands", parse_commands)
    graph.add_node("execute_commands", execute_parsed_commands)
    graph.add_node("format_output", format_final_output)

    # Set the entry point
    graph.set_entry_point("generate_response")

    # Define the edges
    graph.add_edge("generate_response", "parse_commands")
    
    # Conditional edge after parsing commands
    graph.add_conditional_edges(
        "parse_commands",
        should_execute_commands,
        {
            "execute": "execute_commands",
            "format_direct": "format_output", # If not agent mode or no commands, go to format
        }
    )
    
    graph.add_edge("execute_commands", "format_output")
    graph.add_edge("format_output", END)

    # Compile the graph
    app = graph.compile()
    return app

if __name__ == '__main__':
    # Test graph compilation
    app = create_agent_graph()
    console.print("[green]LangGraph app compiled successfully![/green]")
    # You can visualize it if you have graphviz and pygraphviz installed:
    # from IPython.display import Image, display
    # display(Image(app.get_graph().draw_mermaid_png()))