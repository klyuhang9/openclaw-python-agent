from contextlib import contextmanager
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
from rich.syntax import Syntax
from rich.markdown import Markdown

try:
    from prompt_toolkit import prompt as _pt_prompt
    _HAS_PROMPT_TOOLKIT = True
except ImportError:
    _HAS_PROMPT_TOOLKIT = False


console = Console()


class Display:
    """Rich-based display utilities for the CLI agent."""

    def __init__(self):
        self.console = console

    @contextmanager
    def spinner(self, message: str = "Thinking..."):
        """Context manager that shows a spinner while work is in progress."""
        with Live(
            Spinner("dots", text=f" [dim]{message}[/dim]"),
            console=self.console,
            transient=True,
            refresh_per_second=10,
        ):
            yield

    def show_tool_call(self, tool_name: str, arguments: str) -> None:
        """Display a tool call being made."""
        self.console.print(
            Panel(
                f"[bold cyan]Tool:[/bold cyan] {tool_name}\n"
                f"[bold cyan]Args:[/bold cyan] {arguments}",
                title="[yellow]Tool Call[/yellow]",
                border_style="yellow",
                padding=(0, 1),
            )
        )

    def show_tool_result(self, tool_name: str, result: str, truncate: int = 2000) -> None:
        """Display a tool result in a Rich Panel."""
        display_result = result
        if len(result) > truncate:
            display_result = result[:truncate] + f"\n...[truncated, {len(result)} chars total]"

        self.console.print(
            Panel(
                display_result,
                title=f"[green]Result: {tool_name}[/green]",
                border_style="green",
                padding=(0, 1),
            )
        )

    def show_answer(self, content: str) -> None:
        """Display the final assistant answer."""
        self.console.print(
            Panel(
                Markdown(content),
                title="[bold blue]Assistant[/bold blue]",
                border_style="blue",
                padding=(1, 2),
            )
        )

    def show_welcome(self) -> None:
        """Display the welcome message."""
        self.console.print(
            Panel(
                "[bold]CLI Agent[/bold] — powered by [cyan]qwen3-397b[/cyan]\n\n"
                "Commands: [yellow]/screenshot <prompt>[/yellow]  "
                "[yellow]/skills[/yellow]  "
                "[yellow]/clear[/yellow]  "
                "[yellow]/help[/yellow]  "
                "[yellow]/quit[/yellow]",
                title="[bold magenta]Welcome[/bold magenta]",
                border_style="magenta",
                padding=(1, 2),
            )
        )

    def show_help(self) -> None:
        """Display help information."""
        self.console.print(
            Panel(
                "[bold yellow]/screenshot <prompt>[/bold yellow]  Take a screenshot and ask about it\n"
                "[bold yellow]/skills[/bold yellow]               List all available skills\n"
                "[bold yellow]/clear[/bold yellow]              Clear conversation history\n"
                "[bold yellow]/help[/bold yellow]               Show this help message\n"
                "[bold yellow]/quit[/bold yellow] or [bold yellow]/exit[/bold yellow]        Exit the program\n\n"
                "Type any message to chat with the AI assistant.\n"
                "The agent has access to tools: file system, shell, Python, web search, screenshots, and skills.",
                title="[bold cyan]Help[/bold cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    def show_error(self, message: str) -> None:
        """Display an error message."""
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def show_info(self, message: str) -> None:
        """Display an informational message."""
        self.console.print(f"[dim]{message}[/dim]")

    def show_cleared(self) -> None:
        """Display history cleared message."""
        self.console.print("[dim]Conversation history cleared.[/dim]")

    def prompt(self, used_tokens: int = 0, max_tokens: int = 0) -> str:
        """Display the user prompt and get input."""
        if used_tokens and max_tokens:
            pct = used_tokens / max_tokens * 100
            color = "green" if pct < 60 else "yellow" if pct < 85 else "red"
            self.console.print(
                f"[dim][{color}]{used_tokens:,}[/{color}] / {max_tokens:,} tokens[/dim]"
            )
        if _HAS_PROMPT_TOOLKIT:
            return _pt_prompt("You> ")
        return input("You> ")
