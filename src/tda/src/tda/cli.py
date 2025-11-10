"""CLI entrypoint for Technical Debt Agent."""

import anyio
import click
import os
from pathlib import Path

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
    ResultMessage
)
from prompty import load
from rich.console import Console
from rich.markdown import Markdown

from .agent import techdebt_server
from .logging_config import setup_logging

# Create Rich console for markdown rendering
console = Console()


def load_system_prompt() -> str:
    """Load system prompt from prompty file.

    Returns:
        System prompt text extracted from the prompty file
    """
    prompty_path = Path(__file__).parent / "system_prompt.prompty"
    prompty_data = load(str(prompty_path))

    # Extract the system prompt from the Prompty object
    # The prompty.load returns a Prompty object with a content attribute
    content = prompty_data.content

    # Remove the "system:" prefix if present
    # Prompty format includes "system:" as a section marker in markdown
    if content.startswith("system:"):
        content = content[7:].strip()  # Remove "system:" and leading whitespace

    return content


@click.command()
@click.argument("query")
@click.option(
    "--cwd",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Working directory for the agent"
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Continue in interactive mode after initial query"
)
def main(query: str, cwd: str, interactive: bool):
    """Technical Debt Agent - AI agent for codebase analysis.

    Query Claude about technical debt in your .NET projects.

    Examples:

        tda "Give me a summary of style diagnostics"

        tda "What are the most common analyzer diagnostics?" --cwd /path/to/project

        tda "Give me diagnostics" --cwd /path/to/project -i

    Logs are written to: {tempdir}/tda.log
    Set TDA_LOG_LEVEL environment variable to control verbosity (DEBUG, INFO, WARNING, ERROR)
    """
    log_file = setup_logging()
    os.environ['TDA_LOG_FILE'] = log_file

    if interactive:
        anyio.run(run_agent_interactive, cwd, query)
    else:
        anyio.run(run_agent, query, cwd)

    # Print log file location at the end
    click.echo(f"Logs: {log_file}", err=True)


def create_agent_options(cwd: str) -> ClaudeAgentOptions:
    """Create Claude Agent options with system prompt and tools configured.

    Args:
        cwd: Working directory for the agent

    Returns:
        Configured ClaudeAgentOptions
    """
    custom_instructions = load_system_prompt()

    # Resolve cwd to absolute path for tool calls
    absolute_cwd = str(Path(cwd).resolve())

    # Add path context to system prompt
    path_context = f" The target codebase is located at: {absolute_cwd}. When calling extraction tools, use this path as the 'path' parameter."

    # Note: The SDK's append field doesn't support multiline strings
    # Convert to single line by collapsing whitespace
    single_line_instructions = " ".join(custom_instructions.split()) + path_context

    return ClaudeAgentOptions(
        mcp_servers={"techdebt": techdebt_server},
        allowed_tools=[
            "mcp__techdebt__extract_style_diagnostics",
            "mcp__techdebt__extract_analyzers_diagnostics"
        ],
        cwd=cwd,
        permission_mode="acceptEdits",
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": single_line_instructions
        }
    )


def display_response(message, first_message: bool = False):
    """Display agent response message with markdown rendering.

    Args:
        message: Message from the agent (AssistantMessage or ResultMessage)
        first_message: If True, don't add leading newline for text blocks
    """
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                if not first_message:
                    console.print()  # Add blank line before subsequent responses
                markdown = Markdown(block.text)
                console.print(markdown)
    elif isinstance(message, ResultMessage):
        if message.total_cost_usd:
            console.print(f"\n[dim]Cost: ${message.total_cost_usd:.4f}[/dim]")


async def run_agent_interactive(cwd: str, initial_query: str | None = None):
    """Run the agent in interactive mode for multi-turn conversations.

    Args:
        cwd: Working directory for the agent
        initial_query: Optional initial query to run before entering interactive mode
    """
    options = create_agent_options(cwd)
    absolute_cwd = str(Path(cwd).resolve())

    console.print("[bold cyan]Technical Debt Agent (Interactive Mode)[/bold cyan]")
    console.print(f"[dim]Working directory: {absolute_cwd}[/dim]")

    # Display model (from options or default)
    model_name = getattr(options, 'model', None) or 'claude-sonnet-4-5'
    console.print(f"[dim]Model: {model_name}[/dim]")
    console.print("[dim]Type 'exit' or 'quit' to end the session.[/dim]")

    async with ClaudeSDKClient(options=options) as client:
        # Run initial query if provided
        if initial_query:
            console.print(f"\n[bold green]You>[/bold green] {initial_query}\n")
            await client.query(initial_query)
            async for message in client.receive_response():
                display_response(message, first_message=True)

        # Enter interactive loop
        while True:
            try:
                console.print()
                console.print("[bold green]You>[/bold green] ", end="")
                user_query = input()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Goodbye![/dim]")
                break

            if user_query.lower() in ["exit", "quit"]:
                console.print("[dim]Goodbye![/dim]")
                break

            await client.query(user_query)
            async for message in client.receive_response():
                display_response(message)


async def run_agent(query: str, cwd: str):
    """Run the agent with a single query."""
    options = create_agent_options(cwd)

    async with ClaudeSDKClient(options=options) as client:
        await client.query(query)
        async for message in client.receive_response():
            display_response(message, first_message=True)


if __name__ == "__main__":
    main()
