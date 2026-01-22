from rich import theme
from rich.box import DOUBLE, HEAVY, ROUNDED, SIMPLE, Box
from rich.console import Console
from rich.panel import Panel
from rich.style import Style

custom_theme = theme.Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "green",
        "debug": "italic blue",
        "panel.border": "bright_cyan",
        "panel.title": "bold bright_white",
        "panel.success.border": "green",
        "panel.error.border": "red",
        "panel.warning.border": "yellow",
    }
)
console = Console(theme=custom_theme)


def info_panel(content, title=None, border_style="panel.border"):
    """Create a styled information panel."""
    return Panel(
        content, title=title, border_style=border_style, box=ROUNDED, expand=False
    )


def success_panel(content, title="Success"):
    """Create a success panel with green border."""
    return Panel(
        content,
        title=title,
        border_style="panel.success.border",
        box=ROUNDED,
        expand=False,
    )


def error_panel(content, title="Error"):
    """Create an error panel with red border."""
    return Panel(
        content, title=title, border_style="panel.error.border", box=HEAVY, expand=False
    )


def warning_panel(content, title="Warning"):
    """Create a warning panel with yellow border."""
    return Panel(
        content,
        title=title,
        border_style="panel.warning.border",
        box=SIMPLE,
        expand=False,
    )
