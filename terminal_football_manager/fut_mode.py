from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
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
        self.stadium_name = f"{name} Arena"
        self.budget = budget
        self.players = []
        self.stadium_level = 1
        self.division = 10
        self.points = 0
        self.games_played_in_season = 0
        self.next_match_time = None 
        self.transfer_market = [] # List of Auction objects
        self.my_bids = [] # Tracks auctions the user has bid on

    def to_dict(self):
        return {
            "name": self.name,
            "stadium_name": self.stadium_name,
            "budget": self.budget,
            "players": [p.to_dict() for p in self.players],
            "stadium_level": self.stadium_level,
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
        club.stadium_name = data.get("stadium_name", f"{club.name} Arena")
        club.stadium_level = data.get("stadium_level", 1)
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
        if not self.players:
            return 0
        sorted_players = sorted(self.players, key=lambda p: p.ovr, reverse=True)
        top_11_ovr = [p.ovr for p in sorted_players[:11]]
        return sum(top_11_ovr) / len(top_11_ovr) if top_11_ovr else 0

class Auction:
    def __init__(self, player, seller_name, start_bid, end_time):
        self.player = player
        self.seller_name = seller_name
        self.current_bid = start_bid
        self.highest_bidder = None
        self.end_time = end_time

    def to_dict(self):
        return {
            "player": self.player.to_dict(),
            "seller_name": self.seller_name,
            "current_bid": self.current_bid,
            "highest_bidder": self.highest_bidder,
            "end_time": self.end_time.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            Player.from_dict(data["player"]),
            data["seller_name"],
            data["current_bid"],
            datetime.fromisoformat(data["end_time"])
        )

def simulate_market_activity(fut_club):
    """Simulates rival bids on active auctions."""
    now = datetime.now()
    
    # 1. Simulate new listings if market is empty-ish
    if len(fut_club.transfer_market) < 5:
        for _ in range(random.randint(1, 3)):
            new_player = _generate_random_player(70, 85)
            end_time = now + timedelta(hours=random.randint(1, 24))
            start_bid = new_player.market_value // 2
            auction = Auction(new_player, f"Manager_{random.randint(100, 999)}", start_bid, end_time)
            fut_club.transfer_market.append(auction)

    # 2. Simulate rival bids on existing auctions
    for auc in fut_club.transfer_market:
        if auc.end_time > now:
            time_left = (auc.end_time - now).total_seconds()
            bid_chance = 0.1
            if time_left < 3600: bid_chance += 0.2
            if auc.current_bid < auc.player.market_value * 0.8: bid_chance += 0.3
            
            if random.random() < bid_chance:
                increment = int(auc.current_bid * random.uniform(0.05, 0.15))
                auc.current_bid += increment
                auc.highest_bidder = f"Manager_{random.randint(100, 999)}"

    # 3. Clean up expired auctions
    active_auctions = []
    for auc in fut_club.transfer_market:
        if auc.end_time > now:
            active_auctions.append(auc)
        else:
            if auc.highest_bidder == "YOU":
                fut_club.add_player(auc.player)
                console.print(Panel(f"[bold green]WON AUCTION![/bold green] You signed {auc.player.name} for €{auc.current_bid:,}!", style="green"))
            elif auc in fut_club.my_bids:
                console.print(Panel(f"[bold red]LOST AUCTION[/bold red] {auc.player.name} sold to {auc.highest_bidder} for €{auc.current_bid:,}.", style="red"))
    
    fut_club.transfer_market = active_auctions

def train_players(fut_club):
    while True:
        console.print("\n[bold blue]--- Training Ground ---[/bold blue]")
        console.print(f"Budget: [green]€{fut_club.budget:,}[/green]")
        eligible = [p for p in fut_club.players if p.injury_days == 0]
        for i, p in enumerate(eligible[:10]):
             console.print(f"[{i+1}] {p.name} (OVR: {p.ovr})")
        
        choice = console.input("[bold yellow]Select player to train (or 0 to back): [/bold yellow]")
        if choice == '0': break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(eligible):
                player = eligible[idx]
                if fut_club.budget >= 5000:
                    fut_club.budget -= 5000
                    attr = random.choice(list(player.attributes.keys()))
                    player.attributes[attr] += random.randint(1, 3)
                    if random.random() < 0.2: player.ovr += 1
                    console.print(f"[green]Trained {player.name}![/green]")
                else:
                    console.print("[red]Not enough coins![/red]")
        except ValueError:
            console.print("[red]Invalid input.[/red]")

def run_transfer_market(fut_club):
    while True:
        simulate_market_activity(fut_club)
        console.print("\n[bold blue]--- FUT Transfer Market ---[/bold blue]")
        console.print(f"Your Budget: [green]€{fut_club.budget:,}[/green]")
        console.print("1. Browse Auctions\n2. List a Player\n3. Back")
        choice = console.input("[bold yellow]Choice: [/bold yellow]")
        if choice == '1':
            table = Table(title="Live Auctions")
            table.add_column("ID"); table.add_column("Player"); table.add_column("Current Bid")
            for i, auc in enumerate(fut_club.transfer_market):
                table.add_row(str(i+1), auc.player.name, f"€{auc.current_bid:,}")
            console.print(table)
            # Bid logic here...
        elif choice == '2':
            # Sell logic here...
            pass
        elif choice == '3': break

def _generate_random_player(min_ovr, max_ovr):
    pos = random.choice(POSITIONS)
    age = random.randint(17, 35)
    country = random.choice(COUNTRIES)
    first_name = random.choice(NATIONAL_FIRST_NAMES.get(country, FIRST_NAMES))
    last_name = random.choice(NATIONAL_LAST_NAMES.get(country, LAST_NAMES))
    ovr = random.randint(min_ovr, max_ovr)
    player_attributes = {attr: max(10, min(150, int(ovr * (1 + weight)))) for attr, weight in ATTRIBUTE_WEIGHTS.get(pos, {}).items()}
    return Player(f"{first_name} {last_name}", pos, age, ovr, player_attributes, country)

def open_starter_pack(fut_club):
    console.print("\n[bold magenta]Opening your Starter Pack...[/bold magenta]")
    time.sleep(1)
    for _ in range(15): fut_club.add_player(_generate_random_player(50, 64))
    for _ in range(5): fut_club.add_player(_generate_random_player(65, 74))
    for _ in range(2): fut_club.add_player(_generate_random_player(75, 80))
    console.print(Panel("[bold green]Starter Pack Opened! 22 players added.[/bold green]"))

def run_fut_mode(fut_club=None):
    if fut_club is None:
        console.print("\n[bold blue]--- Creating Your FUT Identity ---[/bold blue]")
        team_name = console.input("[bold yellow]Team Name: [/bold yellow]")
        stadium_name = console.input("[bold yellow]Stadium Name: [/bold yellow]")
        fut_club = FutClub(team_name, 100_000)
        fut_club.stadium_name = stadium_name
        open_starter_pack(fut_club)
        save_game("FUT", fut_club.to_dict())

    while True:
        now = datetime.now()
        console.print(f"\n[bold blue]--- FUT Menu (Div {fut_club.division}) ---[/bold blue]")
        console.print(f"Budget: €{fut_club.budget:,} | OVR: {fut_club.get_team_ovr():.1f}")
        console.print("1. Play Season Match\n2. Transfer Market\n3. Training\n4. Save & Exit")
        choice = console.input("[bold yellow]Choice: [/bold yellow]")
        if choice == '1':
            if fut_club.next_match_time and now < fut_club.next_match_time:
                console.print(f"[red]Wait for rest.[/red]")
                continue
            # Match logic...
            fut_club.next_match_time = now + timedelta(days=1)
        elif choice == '2': run_transfer_market(fut_club)
        elif choice == '3': train_players(fut_club)
        elif choice == '4':
            save_game("FUT", fut_club.to_dict())
            break
