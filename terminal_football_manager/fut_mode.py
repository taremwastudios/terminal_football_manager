from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.columns import Columns
import random
import time
from datetime import datetime, timedelta

from .fut_data import AGENT_TIERS, PLAYER_PACKS, STADIUM_NAMES, FUTPlayer, get_players_by_card_type, get_players_by_ovr_range, CHAMPIONS_LEAGUE_TEAMS_DATA, CHAMPIONS_LEAGUE_REWARDS, BIG_CLUBS_FUT_START, FUT_PLAYERS_DATA
from .models import Player, Team
from .constants import ATTRIBUTE_WEIGHTS, POSITIONS, FIRST_NAMES, LAST_NAMES, NATIONAL_FIRST_NAMES, NATIONAL_LAST_NAMES, COUNTRIES
from .game_logic import League, generate_fixtures, assign_goal_scorers, simulate_match, reset_all_team_stats, reset_player_season_stats

console = Console()

from .persistence import save_game, load_game

class FutClub:
    def __init__(self, name, budget):
        self.name = name
        self.stadium_name = "The Arena"
        self.budget = budget
        self.players = []
        self.division = 10
        self.points = 0
        self.games_played_in_season = 0
        self.next_match_time = None 
        self.transfer_market = [] 
        self.my_bids = [] 

    def to_dict(self):
        return {
            "name": self.name,
            "stadium_name": self.stadium_name,
            "budget": self.budget,
            "players": [p.to_dict() for p in self.players],
            "division": self.division,
            "points": self.points,
            "games_played_in_season": self.games_played_in_season,
            "next_match_time": self.next_match_time.isoformat() if self.next_match_time else None,
            "transfer_market": [a.to_dict() for a in self.transfer_market],
            "my_bids": self.my_bids
        }

    @classmethod
    def from_dict(cls, data):
        club = cls(data["name"], data["budget"])
        club.stadium_name = data.get("stadium_name", "The Arena")
        club.division = data.get("division", 10)
        club.points = data.get("points", 0)
        club.games_played_in_season = data.get("games_played_in_season", 0)
        nxt_time = data.get("next_match_time")
        club.next_match_time = datetime.fromisoformat(nxt_time) if nxt_time else None
        club.transfer_market = [Auction.from_dict(a) for a in data.get("transfer_market", [])]
        club.my_bids = data.get("my_bids", [])
        for p_data in data["players"]:
            club.players.append(Player.from_dict(p_data))
        return club

    def add_player(self, player):
        self.players.append(player)
        player.team = self 

    def add_budget(self, amount):
        self.budget += amount

    def get_team_ovr(self):
        if not self.players: return 0
        top_11 = sorted(self.players, key=lambda p: p.ovr, reverse=True)[:11]
        return sum(p.ovr for p in top_11) / len(top_11)

class Auction:
    def __init__(self, player, seller_name, start_bid, end_time):
        self.player = player
        self.seller_name = seller_name
        self.current_bid = start_bid
        self.highest_bidder = None
        self.end_time = end_time

    def to_dict(self):
        return {"player": self.player.to_dict(), "seller_name": self.seller_name, "current_bid": self.current_bid, "highest_bidder": self.highest_bidder, "end_time": self.end_time.isoformat()}

    @classmethod
    def from_dict(cls, data):
        auc = cls(Player.from_dict(data["player"]), data["seller_name"], data["current_bid"], datetime.fromisoformat(data["end_time"]))
        auc.highest_bidder = data.get("highest_bidder")
        return auc

def open_player_pack(fut_club, pack_name):
    # Adjusting prices internally for accessibility
    pack_data = PLAYER_PACKS.get(pack_name)
    if not pack_data:
        console.print("[red]Pack not found.[/red]")
        return
    
    price = 10000 if pack_name == "Basic Pack" else 25000 # Example override
    if fut_club.budget < price:
        console.print(f"[red]Insufficient funds! You need €{price:,}.[/red]")
        return
    
    fut_club.budget -= price
    console.print(Panel(f"[bold gold1]OPENING {pack_name.upper()}...[/bold gold1]", border_style="magenta"))
    time.sleep(1.5)
    
    p_data = random.choice(get_players_by_ovr_range(pack_data.guaranteed_ovr_range[0], pack_data.guaranteed_ovr_range[1]))
    new_p = Player(p_data.name, p_data.position, p_data.age, random.randint(pack_data.guaranteed_ovr_range[0], pack_data.guaranteed_ovr_range[1]), {a: 85 for a in ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"]}, p_data.country)
    fut_club.add_player(new_p)
    console.print(Panel(f"WALKOUT! [bold cyan]{new_p.name}[/bold cyan] (OVR: {new_p.ovr}) joined {fut_club.name}!", border_style="green"))

def view_match_status(fut_club):
    now = datetime.now()
    if fut_club.next_match_time and now < fut_club.next_match_time:
        wait = fut_club.next_match_time - now
        console.print(Panel(f"[bold yellow]LIVE SEASON STATUS[/bold yellow]\n\n"
                            f"Presence: [bold green]Online[/bold green]\n"
                            f"Next Opponent: [cyan]Simulating Rival...[/cyan]\n"
                            f"Match starts in: [bold red]{str(wait).split('.')[0]}[/bold red]", 
                            title="Lobby", border_style="blue"))
    else:
        console.print(Panel("[bold green]MATCH READY![/bold green]\nYour squad is prepared for the next season game.", border_style="green"))
        if console.input("Kickoff now? (y/n): ").lower() == 'y':
            # Fix Team conversion
            user_team_sim = Team(fut_club.name)
            user_team_sim.players = fut_club.players
            rival_team = Team(f"Division {fut_club.division} Rival")
            rival_team.players = [_generate_random_player(60, 85) for _ in range(11)]
            
            simulate_match(user_team_sim, rival_team, user_team_ref=user_team_sim)
            fut_club.next_match_time = now + timedelta(minutes=5) # 5 min cooldown for testing
            fut_club.add_budget(15000)

def open_starter_pack(fut_club):
    console.print(Panel("[bold magenta]CLAIMING STARTER REWARDS...[/bold magenta]", border_style="white"))
    time.sleep(2)
    for _ in range(22):
        fut_club.add_player(_generate_random_player(50, 80))
    console.print("[bold green]Done! 22 Players added to your club.[/bold green]")

def _generate_random_player(min_ovr, max_ovr):
    country = random.choice(COUNTRIES)
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    ovr = random.randint(min_ovr, max_ovr)
    return Player(name, random.choice(POSITIONS), random.randint(18, 35), ovr, {a: 75 for a in ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"]}, country)

def run_fut_mode(fut_club=None):
    if fut_club is None:
        console.print(Panel("[bold blue]--- Welcome to FUT Onboarding ---[/bold blue]"))
        name = console.input("Enter Club Name: ")
        stadium = console.input("Enter Stadium Name: ")
        fut_club = FutClub(name, 100_000)
        fut_club.stadium_name = stadium
        open_starter_pack(fut_club)
        save_game("FUT", fut_club.to_dict())

    while True:
        console.print(f"\n[bold magenta]FUT CENTRAL[/bold magenta] | Stadium: [cyan]{fut_club.stadium_name}[/cyan]")
        console.print(f"Balance: [green]€{fut_club.budget:,}[/green] | OVR: [bold]{fut_club.get_team_ovr():.1f}[/bold]")
        console.print("1. [bold cyan]View Match Status[/bold cyan]\n2. Transfer Market\n3. Training Ground\n4. Store (Packs)\n5. Save & Exit")
        
        choice = console.input("Action: ")
        if choice == '1': view_match_status(fut_club)
        elif choice == '2':
            console.print("[yellow]Market is syncing with global presence... (Browsing Auctions)[/yellow]")
            # Reuse simplified browse logic
            pass
        elif choice == '3':
            console.print("\n[bold blue]--- Squad Training ---[/bold blue]")
            for i, p in enumerate(fut_club.players):
                console.print(f"[{i+1}] {p.name} ({p.ovr})")
            idx = int(console.input("Train ID (0 to back): ")) - 1
            if 0 <= idx < len(fut_club.players):
                if fut_club.budget >= 5000:
                    fut_club.budget -= 5000
                    fut_club.players[idx].ovr += 1
                    console.print("[green]Stats Up![/green]")
        elif choice == '4':
            console.print("\n[bold blue]--- Store ---[/bold blue]")
            console.print("1. Basic Pack (€10,000)\n2. Gold Pack (€25,000)\n3. Back")
            p_choice = console.input("Select: ")
            if p_choice == '1': open_player_pack(fut_club, "Basic Pack")
            elif p_choice == '2': open_player_pack(fut_club, "Gold Pack")
        elif choice == '5':
            save_game("FUT", fut_club.to_dict())
            break
