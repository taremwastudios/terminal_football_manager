import json
import os
from rich.console import Console
from .models import Player, Team
# We'll import mode-specific classes inside functions to avoid circular imports if needed

console = Console()

SAVE_FILE = "football_manager_save.json"

def save_game(mode, data):
    """
    Saves the game state with a mode identifier.
    data should be a dictionary containing mode-specific state.
    """
    full_data = {
        "mode": mode,
        "state": data
    }
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(full_data, f, indent=4)
        console.print(f"
[bold green]Game saved successfully! (Mode: {mode})[/bold green]")
    except Exception as e:
        console.print(f"
[bold red]Error saving game: {e}[/bold red]")

def load_game():
    """
    Loads the game state and returns (mode, state).
    """
    try:
        if not os.path.exists(SAVE_FILE):
            return None, None
        with open(SAVE_FILE, 'r') as f:
            full_data = json.load(f)
        mode = full_data.get("mode")
        state = full_data.get("state")
        console.print(f"
[bold green]Game loaded successfully! (Mode: {mode})[/bold green]")
        return mode, state
    except Exception as e:
        console.print(f"
[bold red]Error loading game: {e}[/bold red]")
        return None, None
