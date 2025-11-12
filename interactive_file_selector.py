#!/usr/bin/env python3
"""Interactive file selector for .xxp files in library-experiments."""

import os
from pathlib import Path
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from eexp_engine import client
import eexp_config

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


def main():
    """Main function."""
    # Set base path to library-experiments
    base_path = Path(__file__).parent / "exp_engine" / "library-experiments"

    if not base_path.exists():
        console.print(f"[bold red]Error:[/bold red] Directory not found: {base_path}")
        return

    console.print("[bold magenta]🔍 Interactive .xxp File Selector[/bold magenta]")
    console.print("[dim]Use arrow keys to navigate, Enter to select[/dim]\n")

    selected_file = navigate_and_select(base_path)

    if selected_file:
        console.print(f"\n[bold]Final selection:[/bold] [green]{selected_file}[/green]")
        return selected_file
    else:
        console.print("[yellow]No file selected.[/yellow]")
        return None


if __name__ == "__main__":
    selected = main()
    if selected:
         exp_name = selected.stem
    client.run(selected, exp_name, config=eexp_config)

