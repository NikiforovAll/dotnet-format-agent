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

from .agent import techdebt_server
from .logging_config import setup_logging


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
def main(query: str, cwd: str):
    """Technical Debt Agent - AI agent for codebase analysis.

    Query Claude about technical debt in your .NET projects.

    Examples:

        tda "Give me a summary of style diagnostics in ../path/to/project"

        tda "What are the most common analyzer diagnostics?" --cwd /path/to/project

    Logs are written to: {tempdir}/tda.log
    Set TDA_LOG_LEVEL environment variable to control verbosity (DEBUG, INFO, WARNING, ERROR)
    """
    log_file = setup_logging()
    os.environ['TDA_LOG_FILE'] = log_file

    anyio.run(run_agent, query, cwd)

    # Print log file location at the end
    click.echo(f"Logs: {log_file}", err=True)


async def run_agent(query: str, cwd: str):
    """Run the agent with the given query."""
    custom_instructions = load_system_prompt()

    # Note: The SDK's append field doesn't support multiline strings
    # Convert to single line by collapsing whitespace
    single_line_instructions = " ".join(custom_instructions.split())

    options = ClaudeAgentOptions(
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

    async with ClaudeSDKClient(options=options) as client:
        await client.query(query)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        click.echo(block.text)
            elif isinstance(message, ResultMessage):
                if message.total_cost_usd:
                    click.echo(f"\n[Cost: ${message.total_cost_usd:.4f}]", err=True)


if __name__ == "__main__":
    main()
