from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import random
import time

from .models import Player, Team
from .constants import ATTRIBUTE_WEIGHTS, POSITIONS, COUNTRIES, NATIONAL_FIRST_NAMES

console = Console()

# --- Commentary Database ---
COMMENTARY = {
    "START": ["Kickoff! The atmosphere is electric at {stadium}.", "The referee blows the whistle and we are underway!"],
    "CHANCE": [
        "{player} finds some space in the box!",
        "A brilliant through ball by {player} splits the defense!",
        "{player} is clear on goal! What a chance!",
        "It's a goalmouth scramble!"
    ],
    "SAVE": [
        "What a save by {keeper}! He tipped it over the bar!",
        "{keeper} stands tall and denies the striker!",
        "Incredible reflexes from {keeper} to keep it out!",
        "The keeper gathers the ball safely."
    ],
    "WOODWORK": [
        "It hits the post! So close for {player}!",
        "Rattling the crossbar! {player} cannot believe his luck.",
        "The woodwork denies {player} a certain goal!"
    ],
    "GOAL": [
        "GOAL!!! {player} smashes it into the bottom corner!",
        "GOAL! A simple tap-in for {player} after a defensive error!",
        "GOAL! {player} curls it beautifully into the top bins!",
        "UNBELIEVABLE! {player} with a screamer from 30 yards out!"
    ],
    "FOUL": [
        "Reckless challenge by {player}! The ref is reaching for his pocket.",
        "A tactical foul by {player} to stop the counter-attack.",
        "A nasty clash between {player} and his opponent."
    ],
    "INJURY": [
        "{player} is down and looks in serious pain.",
        "The medical staff are on for {player}. This doesn't look good.",
        "{player} is hobbling. He might have to come off."
    ],
    "END": ["The referee blows for full time!", "It's all over! A hard-fought battle ends here."]
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
        console.print("\n[bold blue]--- League Table ---[/bold blue]")
        table = Table(
            title=f"[bold green]League Standings[/bold green]",
            show_header=True,
            header_style="bold magenta",
            show_lines=True
        )
        table.add_column("#", style="dim")
        table.add_column("Team", style="cyan", min_width=20)
        table.add_column("P", justify="right")
        table.add_column("Pts", justify="right", style="bold yellow")

        for i, team in enumerate(self.table, 1):
            table.add_row(str(i), team.name, str(team.games_played), str(team.points))
        console.print(table)

def generate_fixtures(teams):
    teams_copy = list(teams)
    if len(teams_copy) % 2 != 0: teams_copy.append(None)
    num_teams = len(teams_copy)
    matchdays = []
    for day in range(num_teams - 1):
        round_fixtures = []
        for i in range(num_teams // 2):
            home, away = teams_copy[i], teams_copy[num_teams - 1 - i]
            if home and away: round_fixtures.append((home, away))
        matchdays.append(round_fixtures)
        teams_copy.insert(1, teams_copy.pop())
    return matchdays

def simulate_match(home_team, away_team, is_international_match=False, user_team_ref=None):
    if home_team is None or away_team is None:
        return 0, 0

    is_user_involved = user_team_ref and (home_team == user_team_ref or away_team == user_team_ref)
    stadium = getattr(home_team, 'stadium_name', "The Stadium")

    if is_user_involved:
        console.print(Panel(f"[bold green]{home_team.name} vs {away_team.name}[/bold green]\n[cyan]Venue: {stadium}[/cyan]", border_style="blue"))
        console.print(random.choice(COMMENTARY["START"]).format(stadium=stadium))

    home_goals, away_goals = 0, 0
    home_ovr = home_team.get_team_ovr()
    away_ovr = away_team.get_team_ovr()

    # Minute-by-minute loop
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        if is_user_involved:
            match_task = progress.add_task(f"[yellow]Kickoff...", total=90)
        
        for minute in range(1, 91):
            if is_user_involved:
                progress.update(match_task, advance=1, description=f"[yellow]Minute {minute}' - Score: {home_goals}-{away_goals}")
                if minute % 15 == 0: time.sleep(0.3)

            if random.random() < 0.12: # Event chance
                attacking_team = home_team if random.random() < (home_ovr / (home_ovr + away_ovr)) else away_team
                defending_team = away_team if attacking_team == home_team else home_team
                player = random.choice(attacking_team.players)
                keeper = defending_team.get_starting_goalkeeper()

                sub_event = random.random()
                if sub_event < 0.6: # Chance
                    luck = random.uniform(0.7, 1.3)
                    streak = 1.2 if getattr(player, 'match_streak', 0) >= 3 else 1.0
                    if random.random() < (player.ovr / 180) * luck * streak:
                        if is_user_involved: console.print(f"{minute}' [bold red]{random.choice(COMMENTARY['GOAL']).format(player=player.name)}[/bold red]")
                        if attacking_team == home_team: home_goals += 1
                        else: away_goals += 1
                        player.season_goals += 1
                        player.match_streak = getattr(player, 'match_streak', 0) + 1
                    else:
                        if is_user_involved: console.print(f"{minute}' [cyan]{random.choice(COMMENTARY['SAVE']).format(keeper=keeper.name if keeper else 'Keeper')}[/cyan]")
                elif sub_event < 0.1: # Injury
                    if is_user_involved: console.print(f"{minute}' [bold red]INJURY! {player.name} is down![/bold red]")
                    player.injury_days = random.randint(5, 20)

    if is_user_involved:
        console.print(f"[bold red]Full Time: {home_team.name} {home_goals} - {away_goals} {away_team.name}[/bold red]")

    # Update Team Stats
    home_team.games_played += 1; away_team.games_played += 1
    home_team.goals_for += home_goals; home_team.goals_against += away_goals
    away_team.goals_for += away_goals; away_team.goals_against += home_goals
    if home_goals > away_goals:
        home_team.wins += 1; home_team.points += 3; away_team.losses += 1
    elif away_goals > home_goals:
        away_team.wins += 1; away_team.points += 3; home_team.losses += 1
    else:
        home_team.draws += 1; home_team.points += 1; away_team.draws += 1; away_team.points += 1
    
    return home_goals, away_goals

def reset_all_team_stats(teams):
    for team in teams:
        team.points = 0; team.games_played = 0; team.wins = 0; team.draws = 0; team.losses = 0; team.goals_for = 0; team.goals_against = 0

def reset_player_season_stats(teams):
    for team in teams:
        for player in team.players:
            player.season_goals = 0; player.season_clean_sheets = 0
