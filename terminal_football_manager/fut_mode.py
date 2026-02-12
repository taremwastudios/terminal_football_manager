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

def simulate_market_activity(fut_club):
    now = datetime.now()
    if len(fut_club.transfer_market) < 8:
        for _ in range(3):
            p = _generate_random_player(65, 88)
            fut_club.transfer_market.append(Auction(p, "AI_Manager", p.market_value//3, now + timedelta(hours=random.randint(1, 48))))
    
    for auc in fut_club.transfer_market[:]:
        if auc.end_time <= now:
            if auc.highest_bidder == "YOU":
                fut_club.add_player(auc.player)
                console.print(Panel(f"AUCTION WON! [bold green]{auc.player.name}[/bold green] is now in your squad.", title="Transfer Market"))
            elif auc.seller_name == "YOU" and auc.highest_bidder:
                fut_club.add_budget(auc.current_bid)
                console.print(Panel(f"PLAYER SOLD! €{auc.current_bid:,} credited for [bold cyan]{auc.player.name}[/bold cyan].", title="Transfer Market"))
            fut_club.transfer_market.remove(auc)
        elif random.random() < 0.05: # Random AI bid
            auc.current_bid = int(auc.current_bid * 1.1)
            auc.highest_bidder = f"Manager_{random.randint(1,999)}"

def open_player_pack(fut_club, pack_name):
    pack = PLAYER_PACKS.get(pack_name)
    if not pack: return
    
    if fut_club.budget < pack.price:
        console.print(f"[bold red]Insufficient funds! Balance: €{fut_club.budget:,}, Price: €{pack.price:,}[/bold red]")
        return
    
    fut_club.budget -= pack.price
    console.print(f"Opening {pack_name}...")
    time.sleep(1)
    p_data = random.choice(get_players_by_ovr_range(pack.guaranteed_ovr_range[0], pack.guaranteed_ovr_range[1]))
    ovr = random.randint(pack.guaranteed_ovr_range[0], pack.guaranteed_ovr_range[1])
    new_p = Player(p_data.name, p_data.position, p_data.age, ovr, {a: 80 for a in ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"]}, p_data.country)
    fut_club.add_player(new_p)
    console.print(Panel(f"WALKOUT! [bold gold1]{new_p.name}[/bold gold1] (OVR: {new_p.ovr}) joined the club!", border_style="yellow"))

def run_transfer_market(fut_club):
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
            idx = int(console.input("Select ID to List: ")) - 1
            if 0 <= idx < len(fut_club.players):
                p = fut_club.players.pop(idx)
                fut_club.transfer_market.append(Auction(p, "YOU", p.market_value//2, datetime.now() + timedelta(hours=24)))
                console.print(f"[green]{p.name} listed for auction![/green]")
        elif choice == '3': break

def view_match_status(fut_club):
    now = datetime.now()
    if fut_club.next_match_time and now < fut_club.next_match_time:
        wait = fut_club.next_match_time - now
        console.print(Panel(f"Presence: [bold green]Online[/bold green]\nMatch countdown: [bold red]{str(wait).split('.')[0]}[/bold red]", title="Lobby Status"))
    else:
        console.print(Panel("[bold green]MATCH READY![/bold green]", border_style="green"))
        if console.input("Kickoff Season Game? (y/n): ").lower() == 'y':
            sim_u = Team(fut_club.name); sim_u.players = fut_club.players
            sim_r = Team("Rival Squad"); sim_r.players = [_generate_random_player(65, 85) for _ in range(11)]
            simulate_match(sim_u, sim_r, user_team_ref=sim_u)
            fut_club.next_match_time = now + timedelta(minutes=15)
            fut_club.add_budget(10000)

def open_starter_pack(fut_club):
    console.print(Panel("[bold magenta]CLAIMING STARTER REWARDS...[/bold magenta]"))
    time.sleep(1.5)
    for _ in range(22): fut_club.add_player(_generate_random_player(50, 80))

def _generate_random_player(min_ovr, max_ovr):
    ovr = random.randint(min_ovr, max_ovr)
    country = random.choice(COUNTRIES)
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    return Player(name, random.choice(POSITIONS), random.randint(18, 35), ovr, {a: 70 for a in ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"]}, country)

def run_fut_mode(fut_club=None):
    if fut_club is None:
        name = console.input("Club Name: ")
        stadium = console.input("Stadium Name: ")
        fut_club = FutClub(name, 100_000)
        fut_club.stadium_name = stadium
        open_starter_pack(fut_club)
    
    while True:
        simulate_market_activity(fut_club)
        console.print(f"\n[bold magenta]{fut_club.name}[/bold magenta] | Stadium: [cyan]{fut_club.stadium_name}[/cyan]")
        console.print(f"Budget: €{fut_club.budget:,} | OVR: {fut_club.get_team_ovr():.1f}")
        console.print("1. View Match Status\n2. Transfer Market\n3. Training\n4. Store (Packs)\n5. Save & Exit")
        choice = console.input("Action: ")
        if choice == '1': view_match_status(fut_club)
        elif choice == '2': run_transfer_market(fut_club)
        elif choice == '3':
            for i, p in enumerate(fut_club.players): console.print(f"[{i+1}] {p.name} ({p.ovr})")
            idx = int(console.input("Train ID (0 back): ")) - 1
            if 0 <= idx < len(fut_club.players):
                if fut_club.budget >= 5000:
                    fut_club.budget -= 5000
                    fut_club.players[idx].ovr += 1
                    console.print("[green]Training successful![/green]")
        elif choice == '4':
            console.print("\n[bold blue]--- Store ---[/bold blue]")
            for p_name, p_data in PLAYER_PACKS.items(): console.print(f"- {p_name}: €{p_data.price:,}")
            p_choice = console.input("Pack Name (exactly) or 'back': ")
            if p_choice != 'back': open_player_pack(fut_club, p_choice)
        elif choice == '5':
            save_game("FUT", fut_club.to_dict())
            break
