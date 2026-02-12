from rich.console import Console
from rich.panel import Panel
from rich.table import Table
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
        self.transfer_market = [] 
        self.my_bids = [] 

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

def simulate_market_activity(fut_club):
    now = datetime.now()
    if len(fut_club.transfer_market) < 10:
        for _ in range(3):
            p = _generate_random_player(60, 90)
            fut_club.transfer_market.append(Auction(p, "AI_Manager", p.market_value//2, now + timedelta(hours=random.randint(1, 48))))
    
    for auc in fut_club.transfer_market[:]:
        if auc.end_time <= now:
            if auc.highest_bidder == "YOU":
                fut_club.add_player(auc.player)
                console.print(f"[bold green]Auction Won! {auc.player.name} added to squad.[/bold green]")
            elif auc.seller_name == "YOU" and auc.highest_bidder:
                fut_club.add_budget(auc.current_bid)
                console.print(f"[bold green]Player Sold! You received €{auc.current_bid:,} for {auc.player.name}.[/bold green]")
            fut_club.transfer_market.remove(auc)
        elif random.random() < 0.1 and auc.seller_name == "YOU": # AI bids on user's player
            auc.current_bid = int(auc.current_bid * 1.1)
            auc.highest_bidder = f"AI_{random.randint(1,999)}"

def open_player_pack(fut_club, pack_name):
    pack = PLAYER_PACKS.get(pack_name)
    if not pack or fut_club.budget < pack.price:
        console.print("[red]Insufficient funds![/red]")
        return
    fut_club.budget -= pack.price
    console.print(f"Opening {pack_name}...")
    time.sleep(1)
    p_data = random.choice(get_players_by_ovr_range(pack.guaranteed_ovr_range[0], pack.guaranteed_ovr_range[1]))
    new_p = Player(p_data.name, p_data.position, p_data.age, random.randint(pack.guaranteed_ovr_range[0], pack.guaranteed_ovr_range[1]), {a: 80 for a in ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"]}, p_data.country)
    fut_club.add_player(new_p)
    console.print(Panel(f"You got [bold cyan]{new_p.name}[/bold cyan] (OVR: {new_p.ovr})!", border_style="green"))

def run_transfer_market(fut_club):
    while True:
        simulate_market_activity(fut_club)
        console.print("\n[bold blue]--- Transfer Market ---[/bold blue]")
        console.print("1. Browse Auctions\n2. List a Player\n3. Back")
        choice = console.input("Choice: ")
        if choice == '1':
            table = Table(title="Auctions")
            table.add_column("ID"); table.add_column("Player"); table.add_column("OVR"); table.add_column("Bid")
            for i, a in enumerate(fut_club.transfer_market):
                table.add_row(str(i+1), a.player.name, str(a.player.ovr), f"€{a.current_bid:,}")
            console.print(table)
            idx = int(console.input("Bid on ID (0 to cancel): ")) - 1
            if 0 <= idx < len(fut_club.transfer_market):
                auc = fut_club.transfer_market[idx]
                bid = int(auc.current_bid * 1.1)
                if fut_club.budget >= bid:
                    fut_club.budget -= bid
                    auc.current_bid = bid
                    auc.highest_bidder = "YOU"
                    console.print("[green]Bid placed![/green]")
        elif choice == '2':
            for i, p in enumerate(fut_club.players): console.print(f"[{i+1}] {p.name} (OVR: {p.ovr})")
            idx = int(console.input("List ID: ")) - 1
            if 0 <= idx < len(fut_club.players):
                p = fut_club.players.pop(idx)
                fut_club.transfer_market.append(Auction(p, "YOU", p.market_value//2, datetime.now() + timedelta(hours=24)))
                console.print("[green]Player listed![/green]")
        elif choice == '3': break

def train_players(fut_club):
    while True:
        console.print("\n[bold blue]--- Training Ground ---[/bold blue]")
        for i, p in enumerate(fut_club.players):
            console.print(f"[{i+1}] {p.name} (OVR: {p.ovr})")
        choice = console.input("Select player (0 to back): ")
        if choice == '0': break
        idx = int(choice) - 1
        if 0 <= idx < len(fut_club.players):
            p = fut_club.players[idx]
            if fut_club.budget >= 5000:
                fut_club.budget -= 5000
                p.ovr += 1
                console.print(f"[green]{p.name} OVR increased to {p.ovr}![/green]")
            else: console.print("[red]Need €5,000![/red]")

def _generate_random_player(min_ovr, max_ovr):
    country = random.choice(COUNTRIES)
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    return Player(name, random.choice(POSITIONS), random.randint(18, 35), random.randint(min_ovr, max_ovr), {a: 70 for a in ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"]}, country)

def open_starter_pack(fut_club):
    for _ in range(22): fut_club.add_player(_generate_random_player(50, 80))

def run_fut_mode(fut_club=None):
    if fut_club is None:
        name = console.input("Team Name: ")
        fut_club = FutClub(name, 100_000)
        open_starter_pack(fut_club)
    
    while True:
        simulate_market_activity(fut_club)
        console.print(f"\n[bold magenta]{fut_club.name} Central[/bold magenta]")
        console.print(f"Budget: €{fut_club.budget:,} | OVR: {fut_club.get_team_ovr():.1f}")
        if fut_club.next_match_time and datetime.now() < fut_club.next_match_time:
            console.print(f"[yellow]Next Match in: {fut_club.next_match_time - datetime.now()}[/yellow]")
        
        console.print("1. View Match Status\n2. Transfer Market\n3. Training\n4. Store (Packs)\n5. Save & Exit")
        choice = console.input("Choice: ")
        if choice == '1':
            if fut_club.next_match_time and datetime.now() < fut_club.next_match_time:
                console.print("[yellow]No matches live. Check back later![/yellow]")
            else:
                console.print("[bold green]MATCH DAY![/bold green]")
                # Simulate a match against random OVR
                simulate_match(Team(fut_club.name), Team("Rival FC"), user_team_ref=Team(fut_club.name))
                fut_club.next_match_time = datetime.now() + timedelta(minutes=30) # 30 min cooldown for testing
        elif choice == '2': run_transfer_market(fut_club)
        elif choice == '3': train_players(fut_club)
        elif choice == '4':
            for p_name, p_data in PLAYER_PACKS.items(): console.print(f"- {p_name}: €{p_data.price:,}")
            p_choice = console.input("Buy pack (name) or 'back': ")
            if p_choice != 'back': open_player_pack(fut_club, p_choice)
        elif choice == '5':
            save_game("FUT", fut_club.to_dict())
            break
