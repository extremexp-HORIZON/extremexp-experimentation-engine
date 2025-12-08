#!/usr/bin/env python3
"""Interactive file selector for .xxp files in library-experiments."""

import os
import sys
from pathlib import Path
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console

console = Console()


def get_folders_and_files(directory: Path):
    """Get all folders and .xxp files in a directory."""
    folders = []
    files = []

    try:
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                folders.append(item)
            elif item.is_file() and item.suffix == '.xxp':
                files.append(item)
    except PermissionError:
        console.print(f"[red]Permission denied: {directory}[/red]")

    return folders, files


def navigate_and_select(base_path: Path):
    """Navigate through folders and select a .xxp file."""
    current_path = base_path

    while True:
        folders, files = get_folders_and_files(current_path)

        # Build choices list
        choices = []

        # Add parent directory option if not at base
        if current_path != base_path:
            choices.append(Choice(value=("back", None), name="📁 .. (Go Back)"))

        # Add folders
        for folder in folders:
            choices.append(Choice(value=("folder", folder), name=f"📁 {folder.name}/"))

        # Add .xxp files
        for file in files:
            choices.append(Choice(value=("file", file), name=f"📄 {file.name}"))

        # Add exit option
        choices.append(Choice(value=("exit", None), name="❌ Exit"))

        if not choices or (len(choices) == 1 and choices[0].value[0] == "exit"):
            console.print("[yellow]No folders or .xxp files found.[/yellow]")
            if current_path != base_path:
                current_path = current_path.parent
                continue
            else:
                return None

        # Show current path
        console.print(f"\n[bold cyan]Current location:[/bold cyan] {current_path.relative_to(base_path.parent)}")

        # Prompt user
        result = inquirer.select(
            message="Select folder or file:",
            choices=choices,
            pointer="👉"
        ).execute()

        action, item = result

        if action == "exit":
            console.print("[yellow]Selection cancelled.[/yellow]")
            return None
        elif action == "back":
            current_path = current_path.parent
        elif action == "folder":
            current_path = item
        elif action == "file":
            console.print(f"\n[bold green]✓ Selected:[/bold green] {item.relative_to(base_path.parent)}")
            return item


def load_config():
    """Load eexp_config.py from the current working directory."""
    import importlib.util

    config_path = Path.cwd() / "eexp_config.py"

    if not config_path.exists():
        console.print(f"[bold red]Error:[/bold red] eexp_config.py not found in current directory: {Path.cwd()}")
        console.print("[yellow]Please run this command from your project root directory that contains eexp_config.py[/yellow]")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("eexp_config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    return config_module


def main():
    """Main function for CLI usage."""
    from eexp_engine import client

    # Load config from current working directory
    eexp_config = load_config()

    # Set base path to library-experiments relative to current directory
    base_path = Path.cwd() / eexp_config.EXPERIMENT_LIBRARY_PATH

    if not base_path.exists():
        console.print(f"[bold red]Error:[/bold red] Directory not found: {base_path}")
        console.print(f"[yellow]Make sure you're running this from the project root that contains exp_engine/library-experiments/[/yellow]")
        return

    console.print("[bold magenta]🔍 Experiment Selector[/bold magenta]")
    console.print("[dim]Use arrow keys to navigate, Enter to select[/dim]")

    selected_file = navigate_and_select(base_path)

    if selected_file:
        console.print(f"\n[bold]Final selection:[/bold] [green]{selected_file}[/green]")
        # Get the relative path from the experiment library, without the .xxp extension
        relative_path = selected_file.relative_to(base_path)
        exp_name = str(relative_path.with_suffix(''))  # Remove .xxp and convert to string
        console.print(f"[bold cyan]Running experiment:[/bold cyan] {exp_name}")
        client.run(selected_file, exp_name, eexp_config)
    else:
        console.print("[yellow]No file selected.[/yellow]")


def select_file():
    """Programmatic function to just select a file without running it."""
    # Set base path to library-experiments relative to current directory

    eexp_config = load_config()

    base_path = Path.cwd() / eexp_config.EXPERIMENT_LIBRARY_PATH

    if not base_path.exists():
        console.print(f"[bold red]Error:[/bold red] Directory not found: {base_path}")
        return None

    console.print("[bold magenta]🔍 Interactive .xxp File Selector[/bold magenta]")
    console.print("[dim]Use arrow keys to navigate, Enter to select[/dim]\n")

    selected_file = navigate_and_select(base_path)

    if selected_file:
        console.print(f"\n[bold]Final selection:[/bold] [green]{selected_file}[/green]")
        relative_path = selected_file.relative_to(base_path)
        exp_name = str(relative_path.with_suffix(''))  # Remove .xxp and convert to string
        return selected_file, exp_name
    else:
        console.print("[yellow]No file selected.[/yellow]")
        return None


if __name__ == "__main__":
    main()

