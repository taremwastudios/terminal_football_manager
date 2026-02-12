from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.columns import Columns
from rich.text import Text
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
        self.season_fixtures = [] # List of (Opponent Name, Opponent OVR)
        self.season_end_time = None

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
            "season_end_time": self.season_end_time.isoformat() if self.season_end_time else None,
            "transfer_market": [a.to_dict() for a in self.transfer_market],
            "season_fixtures": self.season_fixtures,
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
        end_time = data.get("season_end_time")
        club.season_end_time = datetime.fromisoformat(end_time) if end_time else None
        club.transfer_market = [Auction.from_dict(a) for a in data.get("transfer_market", [])]
        club.season_fixtures = data.get("season_fixtures", [])
        club.my_bids = data.get("my_bids", [])
        for p_data in data["players"]:
            club.players.append(Player.from_dict(p_data))
        return club

    def add_player(self, player):
        self.players.append(player)
        player.team = self 

    def add_budget(self, amount):
        self.budget += int(amount)

    def get_team_ovr(self):
        if not self.players: return 0
        top_11 = sorted(self.players, key=lambda p: p.ovr, reverse=True)[:11]
        return sum(p.ovr for p in top_11) / len(top_11)

class Auction:
    def __init__(self, player, seller_name, start_bid, end_time):
        self.player = player
        self.seller_name = seller_name
        self.current_bid = int(start_bid)
        self.highest_bidder = None
        self.end_time = end_time

    def to_dict(self):
        return {"player": self.player.to_dict(), "seller_name": self.seller_name, "current_bid": self.current_bid, "highest_bidder": self.highest_bidder, "end_time": self.end_time.isoformat()}

    @classmethod
    def from_dict(cls, data):
        auc = cls(Player.from_dict(data["player"]), data["seller_name"], data["current_bid"], datetime.fromisoformat(data["end_time"]))
        auc.highest_bidder = data.get("highest_bidder")
        return auc

def init_season(fut_club):
    """Generates 10 fixtures for the division and sets season end time."""
    fut_club.season_fixtures = []
    base_ovr = 50 + (10 - fut_club.division) * 5
    for i in range(10):
        opp_name = f"{random.choice(COUNTRIES)} United"
        opp_ovr = base_ovr + random.randint(-3, 7)
        fut_club.season_fixtures.append([opp_name, opp_ovr])
    
    fut_club.season_end_time = datetime.now() + timedelta(days=7)
    fut_club.games_played_in_season = 0
    fut_club.points = 0

def view_match_status(fut_club):
    if not fut_club.season_fixtures or not fut_club.season_end_time:
        init_season(fut_club)

    now = datetime.now()
    time_left = fut_club.season_end_time - now
    if time_left.total_seconds() <= 0:
        # Season concluded
        console.print(Panel(f"[bold gold1]SEASON CONCLUDED![/bold gold1]\nPoints: {fut_club.points}\nResult: Processing Rewards...", border_style="yellow"))
        init_season(fut_club) # Reset for next
        return

    # Lobby Data
    avg_stamina = sum(p.stamina for p in fut_club.players) / len(fut_club.players) if fut_club.players else 0
    next_opp_name, next_opp_ovr = fut_club.season_fixtures[fut_club.games_played_in_season] if fut_club.games_played_in_season < 10 else ("None", 0)
    
    # UI Layout
    status_table = Table.grid(expand=True)
    status_table.add_column(style="cyan", justify="left")
    status_table.add_column(style="white", justify="right")
    
    status_table.add_row("Division:", f"[bold]{fut_club.division}[/bold]")
    status_table.add_row("Season Points:", f"[bold yellow]{fut_club.points}[/bold yellow]")
    status_table.add_row("Games Played:", f"{fut_club.games_played_in_season}/10")
    status_table.add_row("Season Concludes in:", f"[bold red]{str(time_left).split('.')[0]}[/bold red]")
    
    lineup_table = Table(title="Starting XI", box=None)
    lineup_table.add_column("Pos"); lineup_table.add_column("Name"); lineup_table.add_column("OVR"); lineup_table.add_column("Fit")
    top_11 = sorted(fut_club.players, key=lambda p: p.ovr, reverse=True)[:11]
    for p in top_11:
        lineup_table.add_row(p.position, p.name, str(p.ovr), f"{p.stamina}%")

    next_match_panel = Panel(
        f"[bold]NEXT OPPONENT:[/bold]\n[cyan]{next_opp_name}[/cyan]\nOVR: [bold]{next_opp_ovr}[/bold]\n\n"
        f"Venue: {fut_club.stadium_name}\n"
        f"Status: [bold green]MATCH READY[/bold green]" if (not fut_club.next_match_time or now >= fut_club.next_match_time) else "[bold red]RESTING[/bold red]",
        title="Fixture Scouting", border_style="blue"
    )

    console.print(Panel(status_table, title=f"Division {fut_club.division} - Live Presence", border_style="magenta"))
    console.print(Columns([next_match_panel, lineup_table]))

    if fut_club.games_played_in_season < 10:
        if not fut_club.next_match_time or now >= fut_club.next_match_time:
            if console.input("\n[bold green]Proceed to Kickoff? (y/n): [/bold green]").lower() == 'y':
                user_sim = Team(fut_club.name); user_sim.players = fut_club.players
                opp_sim = Team(next_opp_name); opp_sim.players = [_generate_random_player(next_opp_ovr-5, next_opp_ovr+5) for _ in range(11)]
                
                h_g, a_g = simulate_match(user_sim, opp_sim, user_team_ref=user_sim)
                
                if h_g > a_g: fut_club.points += 3
                elif h_g == a_g: fut_club.points += 1
                
                fut_club.games_played_in_season += 1
                fut_club.next_match_time = now + timedelta(minutes=10) # Cooldown
                # Drain Stamina
                for p in fut_club.players: p.stamina = max(10, p.stamina - random.randint(10, 25))
                save_game("FUT", fut_club.to_dict())
        else:
            wait = fut_club.next_match_time - now
            console.print(f"[yellow]Squad is recovering. Next match available in {str(wait).split('.')[0]}.[/yellow]")

def run_transfer_market(fut_club):
    # (Restored full logic as per previous turn)
    while True:
        simulate_market_activity(fut_club)
        console.print(f"\n[bold blue]--- FUT Transfer Market ---[/bold blue] | Budget: €{fut_club.budget:,}")
        console.print("1. Browse Auctions\n2. List a Player\n3. Back")
        choice = console.input("Action: ")
        if choice == '1':
            table = Table(title="Live Market")
            table.add_column("ID"); table.add_column("Player"); table.add_column("OVR"); table.add_column("Current Bid"); table.add_column("Bidder")
            for i, a in enumerate(fut_club.transfer_market):
                table.add_row(str(i+1), a.player.name, str(a.player.ovr), f"€{a.current_bid:,}", a.highest_bidder or "None")
            console.print(table)
            idx_in = console.input("Select ID to Bid (0 back): ")
            if idx_in.isdigit() and 0 < int(idx_in) <= len(fut_club.transfer_market):
                auc = fut_club.transfer_market[int(idx_in)-1]
                min_bid = int(auc.current_bid * 1.1)
                if fut_club.budget >= min_bid:
                    fut_club.budget -= min_bid
                    auc.current_bid = min_bid
                    auc.highest_bidder = "YOU"
                    console.print("[bold green]Highest bidder![/bold green]")
                else: console.print("[red]Insufficient coins.[/red]")
        elif choice == '2':
            for i, p in enumerate(fut_club.players): console.print(f"[{i+1}] {p.name} (OVR: {p.ovr})")
            idx_in = console.input("Select ID to List: ")
            if idx_in.isdigit():
                idx = int(idx_in) - 1
                if 0 <= idx < len(fut_club.players):
                    p = fut_club.players.pop(idx)
                    fut_club.transfer_market.append(Auction(p, "YOU", p.market_value//2, datetime.now() + timedelta(hours=24)))
                    console.print(f"[green]{p.name} listed![/green]")
        elif choice == '3': break

def _generate_random_player(min_ovr, max_ovr):
    ovr = random.randint(min_ovr, max_ovr)
    country = random.choice(COUNTRIES)
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    p = Player(name, random.choice(POSITIONS), random.randint(18, 35), ovr, {a: 70 for a in ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"]}, country)
    p.stamina = 100
    return p

def run_fut_mode(fut_club=None):
    if fut_club is None:
        name = console.input("Club Name: ")
        stadium = console.input("Stadium Name: ")
        fut_club = FutClub(name, 100_000)
        fut_club.stadium_name = stadium
        # Open Starter rewards
        for _ in range(22): fut_club.add_player(_generate_random_player(50, 80))
        init_season(fut_club)
        save_game("FUT", fut_club.to_dict())
    
    while True:
        simulate_market_activity(fut_club)
        console.print(f"\n[bold magenta]{fut_club.name}[/bold magenta] | Stadium: [cyan]{fut_club.stadium_name}[/cyan]")
        console.print(f"Budget: €{fut_club.budget:,} | OVR: {fut_club.get_team_ovr():.1f}")
        console.print("1. View Match Status\n2. Transfer Market\n3. Training Ground\n4. Store (Packs)\n5. Save & Exit")
        choice = console.input("Action: ")
        if choice == '1': view_match_status(fut_club)
        elif choice == '2': run_transfer_market(fut_club)
        elif choice == '3':
            # Training logic...
            for i, p in enumerate(fut_club.players): console.print(f"[{i+1}] {p.name} ({p.ovr}) Stamina: {p.stamina}%")
            idx_in = console.input("Train ID: ")
            if idx_in.isdigit():
                idx = int(idx_in)-1
                if 0 <= idx < len(fut_club.players):
                    fut_club.budget -= 5000; fut_club.players[idx].ovr += 1
                    console.print("[green]Stats Improved![/green]")
        elif choice == '4':
            console.print("1. Basic Pack (€10k)\n2. Gold Pack (€25k)")
            p_choice = console.input("Select: ")
            if p_choice == '1':
                if fut_club.budget >= 10000:
                    fut_club.budget -= 10000
                    p = _generate_random_player(60, 75)
                    fut_club.add_player(p)
                    console.print(f"[gold1]Gained {p.name}![/gold1]")
            elif p_choice == '2':
                if fut_club.budget >= 25000:
                    fut_club.budget -= 25000
                    p = _generate_random_player(75, 88)
                    fut_club.add_player(p)
                    console.print(f"[gold1]Gained {p.name}![/gold1]")
        elif choice == '5':
            save_game("FUT", fut_club.to_dict())
            break
