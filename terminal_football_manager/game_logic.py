from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import random
import time

from .models import Player, Team
from .constants import ATTRIBUTE_WEIGHTS, POSITIONS, COUNTRIES, NATIONAL_FIRST_NAMES

console = Console()

# --- Constants & Prizes ---
AWARD_PRIZES = {
    "1st": 20_000_000,
    "2nd": 10_000_000,
    "3rd": 5_000_000,
    "TOTS_PLAYER": 2_000_000
}

NATIONAL_TEAM_NAMES = [
    "Brazil", "Germany", "Argentina", "France", "Italy", "Spain", "England", 
    "Portugal", "Belgium", "Netherlands", "Uruguay", "Croatia", "Mexico", 
    "USA", "Colombia", "Chile", "Sweden", "Switzerland", "Denmark", "Poland",
    "Senegal", "Nigeria", "Egypt", "Japan", "South Korea", "Australia"
]

COMMENTARY = {
    "START": ["Kickoff! The atmosphere is electric at {stadium}.", "The referee blows the whistle and we are underway!"],
    "CHANCE": ["{player} finds some space in the box!", "A brilliant through ball by {player} splits the defense!", "{player} is clear on goal!"],
    "SAVE": ["What a save by {keeper}!", "{keeper} stands tall and denies the striker!", "Incredible reflexes from {keeper}!"],
    "WOODWORK": ["It hits the post! So close for {player}!", "Rattling the crossbar!"],
    "GOAL": ["GOAL!!! {player} smashes it home!", "GOAL! A clinical finish by {player}!", "UNBELIEVABLE! {player} scores a worldie!"],
    "FOUL": ["Reckless challenge by {player}!", "A nasty clash between {player} and his opponent."],
    "INJURY": ["{player} is down and looks in pain.", "Medical staff are on for {player}."],
    "END": ["The referee blows for full time!", "It's all over!"]
}

class League:
    def __init__(self, teams):
        self.teams = {team.name: team for team in teams}
        self.table = []
        self.fixtures = []
        self.update_table()

    def update_table(self):
        self.table = sorted(list(self.teams.values()), key=lambda t: (t.points, t.goal_difference, t.goals_for), reverse=True)

    def print_table(self):
        table = Table(title="League Standings", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim")
        table.add_column("Team", style="cyan")
        table.add_column("P", justify="right")
        table.add_column("W", justify="right")
        table.add_column("D", justify="right")
        table.add_column("L", justify="right")
        table.add_column("GD", justify="right")
        table.add_column("Pts", justify="right", style="bold yellow")
        for i, team in enumerate(self.table, 1):
            table.add_row(str(i), team.name, str(team.games_played), str(team.wins), str(team.draws), str(team.losses), str(team.goal_difference), str(team.points))
        console.print(table)

def generate_fixtures(teams):
    """Generates Home and Away fixtures (Double Round Robin)."""
    teams_copy = list(teams)
    if len(teams_copy) % 2 != 0: teams_copy.append(None)
    num_teams = len(teams_copy)
    matchdays = []
    
    # First half of season
    for day in range(num_teams - 1):
        matchday = []
        for i in range(num_teams // 2):
            home, away = teams_copy[i], teams_copy[num_teams - 1 - i]
            if home and away: matchday.append((home, away))
        matchdays.append(matchday)
        teams_copy.insert(1, teams_copy.pop())
    
    # Second half (reverse fixtures)
    second_half = []
    for m in matchdays:
        reverse_m = [(away, home) for home, away in m]
        second_half.append(reverse_m)
    
    return matchdays + second_half

def assign_goal_scorers(team, goals):
    if not team.players: return
    for _ in range(goals):
        scorer = random.choice(team.players)
        scorer.season_goals += 1

def simulate_match(home_team, away_team, is_international_match=False, user_team_ref=None):
    if home_team is None or away_team is None: return 0, 0
    is_user_involved = user_team_ref and (home_team == user_team_ref or away_team == user_team_ref)
    stadium = getattr(home_team, 'stadium_name', f"{home_team.name} Stadium")
    
    if is_user_involved:
        console.print(Panel(f"[bold green]{home_team.name} vs {away_team.name}[/bold green]\n[cyan]Venue: {stadium}[/cyan]"))
    
    home_goals, away_goals = 0, 0
    home_ovr, away_ovr = home_team.get_team_ovr(), away_team.get_team_ovr()
    home_eligible = [p for p in home_team.players if p.injury_days == 0 and not p.is_banned]
    away_eligible = [p for p in away_team.players if p.injury_days == 0 and not p.is_banned]
    
    if not home_eligible: home_eligible = home_team.players
    if not away_eligible: away_eligible = away_team.players

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        task = progress.add_task("Match in progress...", total=90) if is_user_involved else None
        for minute in range(1, 91):
            if is_user_involved: 
                progress.update(task, advance=1, description=f"Minute {minute}' - {home_goals}:{away_goals}")
                if minute % 15 == 0: time.sleep(0.1)

            if random.random() < 0.1: # 10% event chance
                att_team = home_team if random.random() < (home_ovr/(home_ovr+away_ovr)) else away_team
                pool = home_eligible if att_team == home_team else away_eligible
                if not pool: continue
                player = random.choice(pool)
                
                if random.random() < (player.ovr / 220): # Scoring logic
                    if is_user_involved: console.print(f"{minute}' [bold red]GOAL! {player.name} scores for {att_team.name}![/bold red]")
                    if att_team == home_team: home_goals += 1
                    else: away_goals += 1
                    player.season_goals += 1
                elif is_user_involved and random.random() < 0.2:
                    console.print(f"{minute}' {player.name} misses a great opportunity!")

    home_team.games_played += 1; away_team.games_played += 1
    home_team.goals_for += home_goals; home_team.goals_against += away_goals
    away_team.goals_for += away_goals; away_team.goals_against += home_goals
    if home_goals > away_goals:
        home_team.wins += 1; home_team.points += 3; away_team.losses += 1
    elif away_goals > home_goals:
        away_team.wins += 1; away_team.points += 3; home_team.losses += 1
    else:
        home_team.draws += 1; home_team.points += 1; away_team.draws += 1; away_team.points += 1
    
    if is_user_involved:
        console.print(f"[bold green]FT: {home_team.name} {home_goals} - {away_goals} {away_team.name}[/bold green]")
    return home_goals, away_goals

def reset_all_team_stats(teams):
    for t in teams:
        t.points = 0; t.games_played = 0; t.wins = 0; t.draws = 0; t.losses = 0; t.goals_for = 0; t.goals_against = 0

def reset_player_season_stats(teams):
    for t in teams:
        for p in t.players: p.season_goals = 0; p.season_clean_sheets = 0

def present_season_awards(all_club_teams, user_team_ref):
    console.print(Panel("[bold gold1]END OF SEASON AWARDS[/bold gold1]", border_style="yellow"))
    all_players = []
    for t in all_club_teams: all_players.extend(t.players)
    
    top_scorer = max(all_players, key=lambda p: p.season_goals)
    best_player = max(all_players, key=lambda p: p.ovr)
    
    console.print(f"🏆 [bold cyan]Golden Boot:[/bold cyan] {top_scorer.name} ({top_scorer.season_goals} Goals)")
    console.print(f"🌟 [bold gold1]Player of the Season:[/bold gold1] {best_player.name} (OVR: {best_player.ovr})")
    
    # Financial rewards for user if they finished high
    if user_team_ref.points > 0:
        prize = AWARD_PRIZES["1st"] if user_team_ref.wins > 10 else 5_000_000
        user_team_ref.budget += prize
        console.print(f"[green]Your club received €{prize:,} in season rewards![/green]")

# --- Competition Simulation ---
def simulate_competition_group_stage(participants, name, user):
    console.print(Panel(f"[bold blue]{name} - Group Stage[/bold blue]"))
    # Return top teams for knockout
    return sorted(participants, key=lambda t: t.get_team_ovr(), reverse=True)[:8]

def simulate_competition_knockout_stage(qualifiers, name, prizes, user):
    if not qualifiers: return None
    console.print(Panel(f"[bold blue]{name} - Knockout Stage[/bold blue]"))
    winner = qualifiers[0]
    console.print(f"🏆 [bold green]{winner.name}[/bold green] has won the {name}!")
    return winner

def simulate_international_tournament(parts, name, prizes, user): return parts[0]
def simulate_knockout_cup(parts, name, prizes, user): 
    console.print(f"Simulating {name}...")
    return parts[0]
def simulate_home_away_cup(parts, name, prizes, user): 
    console.print(f"Simulating {name}...")
    return parts[0]
def simulate_world_cup(teams, user): 
    console.print(Panel("[bold yellow]WORLD CUP YEAR[/bold yellow]", border_style="red"))
def run_playoffs(relegated, challengers, user): return challengers[:2], relegated
def generate_sponsorship_offer(ovr): return int(10_000_000 * (ovr/80))
def calculate_merchandise_revenue(team, league): return int(2_000_000 * (team.get_team_ovr()/80))
def generate_national_team_squad(country, players): return [p for p in players if p.country == country][:23]
