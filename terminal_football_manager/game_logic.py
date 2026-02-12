from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import random

from .models import Player, Team
from .constants import ATTRIBUTE_WEIGHTS, POSITIONS, COUNTRIES, NATIONAL_FIRST_NAMES # Needed for generate_national_team_squad and generate_player

console = Console()

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
            title=f"[bold green]{self.table[0].league if self.table else 'N/A'} Standings[/bold green]",
            show_header=True,
            header_style="bold magenta",
            show_lines=True
        )
        table.add_column("#", style="dim")
        table.add_column("Team", style="cyan", min_width=20)
        table.add_column("P", justify="right")
        table.add_column("W", justify="right")
        table.add_column("D", justify="right")
        table.add_column("L", justify="right")
        table.add_column("GF", justify="right")
        table.add_column("GA", justify="right")
        table.add_column("GD", justify="right")
        table.add_column("Pts", justify="right", style="bold yellow")

        for i, team in enumerate(self.table, 1):
            table.add_row(
                str(i),
                team.name,
                str(team.games_played),
                str(team.wins),
                str(team.draws),
                str(team.losses),
                str(team.goals_for),
                str(team.goals_against),
                str(team.goal_difference),
                str(team.points)
            )
        console.print(table)

def generate_fixtures(teams):
    teams_copy = teams[:]
    
    if len(teams_copy) % 2 != 0:
        teams_copy.append(None) 
    
    num_teams = len(teams_copy)
    matchdays = []
    
    for day in range(num_teams - 1):
        round_fixtures = []
        for i in range(num_teams // 2):
            home = teams_copy[i]
            away = teams_copy[num_teams - 1 - i]
            if home and away:
                round_fixtures.append((home, away))
        matchdays.append(round_fixtures)
        
        teams_copy.insert(1, teams_copy.pop())

    all_fixtures = matchdays[:]
    for matchday in matchdays:
        all_fixtures.append([(away, home) for home, away in matchday])
        
    return all_fixtures

def assign_goal_scorers(team, goals):
    attackers = [p for p in team.players if p.position in ["CF", "SS", "RWF", "LWF"]]
    midfielders = [p for p in team.players if p.position in ["AMF", "CMF"]]
    
    possible_scorers = []
    possible_scorers.extend(attackers * 5)
    possible_scorers.extend(midfielders * 2)
    possible_scorers.extend([p for p in team.players if p.position not in ["GK"]])

    for _ in range(goals):
        if possible_scorers:
            random.choice(possible_scorers).season_goals += 1

import time

def simulate_match(home_team, away_team, is_international_match=False, user_team_ref=None):
    # Handle BYE teams (None) gracefully
    if home_team is None or away_team is None:
        return 0, 0 # No goals scored, no stats updated for a bye

    is_user_involved = user_team_ref and (home_team == user_team_ref or away_team == user_team_ref)

    if not is_international_match: 
        attendance = int(home_team.stadium_capacity * random.uniform(0.65, 1.0))
        revenue = attendance * 100 # Multiplied by 5x current value (20*5) for enhanced stadium revenue
        home_team.budget += revenue
        if is_user_involved and home_team == user_team_ref:
            console.print(f"[REVENUE] [green]{home_team.name}[/green] earned [yellow]€{revenue:,}[/yellow] from {attendance:,} fans.")

    home_ovr = home_team.get_team_ovr()
    away_ovr = away_team.get_team_ovr()

    # Commentary setup
    commentary_events = [
        "Kickoff! The match is underway.",
        f"A fierce battle in the midfield between {home_team.name} and {away_team.name}.",
        "Great defensive play by the backline.",
        "A dangerous cross into the box!",
        "The goalkeeper makes a stunning save!",
        "A tactical shift from the manager.",
        "The crowd is going wild!",
        "A yellow card is shown for a reckless challenge."
    ]

    if is_user_involved:
        console.print(f"\n[bold green]{home_team.name} vs {away_team.name}[/bold green]")
        for _ in range(3):
            console.print(f"[italic]{random.choice(commentary_events)}[/italic]")
            time.sleep(0.5)

    home_goals = random.randint(0, 2) 
    away_goals = random.randint(0, 2) 

    ovr_diff = home_ovr - away_ovr
    if ovr_diff > 20: 
        home_goals += random.randint(2, 4)
        away_goals += random.randint(0, 1) 
    elif ovr_diff > 10:
        home_goals += random.randint(1, 2)
    elif ovr_diff < -20: 
        away_goals += random.randint(2, 4)
        home_goals += random.randint(0, 1) 
    elif ovr_diff < -10:
        away_goals += random.randint(1, 2)
    
    home_goals += random.randint(0, 2)
    away_goals += random.randint(0, 2)

    home_goals = max(0, home_goals)
    away_goals = max(0, away_goals)

    assign_goal_scorers(home_team, home_goals)
    assign_goal_scorers(away_team, away_goals)

    if home_goals == 0:
        gk = away_team.get_starting_goalkeeper()
        if gk: gk.season_clean_sheets += 1
    if away_goals == 0:
        gk = home_team.get_starting_goalkeeper()
        if gk: gk.season_clean_sheets += 1

    home_team.games_played += 1
    away_team.games_played += 1
    home_team.goals_for += home_goals
    away_team.goals_for += away_goals
    home_team.goals_against += away_goals
    away_team.goals_against += home_goals

    if home_goals > away_goals:
        home_team.wins += 1; home_team.points += 3
        away_team.losses += 1
    elif away_goals > home_goals:
        away_team.wins += 1; away_team.points += 3
        home_team.losses += 1
    else:
        home_team.draws += 1; home_team.points += 1
        away_team.draws += 1; away_team.points += 1
    
    if is_user_involved:
        console.print(f"[bold red]Full Time: {home_team.name} {home_goals} - {away_goals} {away_team.name}[/bold red]")
    
    return home_goals, away_goals

def reset_all_team_stats(teams):
    for team in teams:
        team.points = 0; team.games_played = 0; team.wins = 0
        team.draws = 0; team.losses = 0; team.goals_for = 0; team.goals_against = 0

def reset_player_season_stats(teams):
    for team in teams:
        for player in team.players + team.youth_academy:
            player.season_goals = 0; player.season_clean_sheets = 0

# --- Awards Prize Structures (high rewards as requested) ---
AWARD_PRIZES = {
    "1st": 20_000_000,
    "2nd": 10_000_000,
    "3rd": 5_000_000,
    "TOTS_PLAYER": 2_000_000 # Each player in Team of the Season gets this for their club
}

def _get_award_winners(all_players, sort_key, filter_func=None, limit=3):
    """
    Helper function to get top players for an award.
    Args:
        all_players (list): List of all Player objects.
        sort_key (function): A lambda function to use as the key for sorting.
        filter_func (function, optional): A lambda function to filter players. Defaults to None.
        limit (int): The number of top players to return.
    Returns:
        list: A list of top Player objects.
    """
    if filter_func:
        filtered_players = [p for p in all_players if filter_func(p)]
    else:
        filtered_players = all_players
    
    if not filtered_players:
        return []

    # Sort in descending order based on the sort_key
    sorted_players = sorted(filtered_players, key=sort_key, reverse=True)
    return sorted_players[:limit]

def _display_and_award(award_name, winners, prize_structure, user_team_ref):
    """
    Helper function to display award winners and award prize money to their clubs.
    Args:
        award_name (str): The name of the award.
        winners (list): A list of Player objects who won the award.
        prize_structure (dict): Dictionary with "1st", "2nd", "3rd" prize amounts.
        user_team_ref (Team): The user's team object, to check for prize money notifications.
    """
    if not winners:
        console.print(Panel(f"[bold red]No eligible winners for {award_name} this season.[/bold red]", title="[bold yellow]Awards[/bold yellow]", border_style="red"));
        return
    
    award_content = []
    award_content.append(f"[bold blue]--- {award_name} ---[/bold blue]")

    for i, player in enumerate(winners):
        prize_amount = 0
        if i == 0: prize_amount = prize_structure.get("1st", 0)
        elif i == 1: prize_amount = prize_structure.get("2nd", 0)
        elif i == 2: prize_amount = prize_structure.get("3rd", 0)

        if player.team:
            player.team.budget += prize_amount
            prize_str = f"[yellow]€{prize_amount:,}[/yellow]" if prize_amount > 0 else "No prize"
            if user_team_ref and player.team == user_team_ref:
                award_content.append(f"  [bold]{i+1}st Place:[/bold] [cyan]{player.name}[/cyan] ([blue]{player.team.name}[/blue]) - OVR: [green]{player.ovr}[/green], {prize_str} awarded to [bold green]your club![/bold green]")
            else:
                award_content.append(f"  [bold]{i+1}st Place:[/bold] [cyan]{player.name}[/cyan] ([blue]{player.team.name}[/blue]) - OVR: [green]{player.ovr}[/green], {prize_str} awarded to their club.")
        else:
            award_content.append(f"  [bold]{i+1}st Place:[/bold] [cyan]{player.name}[/cyan] (Free Agent) - OVR: [green]{player.ovr}[/green]") # Should not happen if player.team is linked
    
    console.print(Panel("\n".join(award_content), title=f"[bold yellow]{award_name}[/bold yellow]", border_style="green"))


def present_season_awards(all_club_teams, user_team_ref): # Modified to accept all_club_teams
    console.print(Panel("[bold green]END OF SEASON AWARDS[/bold green]", title="[bold yellow]SEASON AWARDS[/bold yellow]", width=50, style="bold blue"))

    # Ensure all players have their team attribute set before processing awards
    all_players = []
    for team in all_club_teams:
        for p in team.players + team.youth_academy:
            p.team = team # Ensure player knows their team
            all_players.append(p)
    
    if not all_players:
        console.print(Panel("[bold red]No players available for awards.[/bold red]", title="[bold yellow]Awards[/bold yellow]", border_style="red"))
        return

    # --- Existing Awards ---
    # Golden Boot
    top_scorers = _get_award_winners(all_players, sort_key=lambda p: p.season_goals)
    _display_and_award("Golden Boot (Top Scorer)", top_scorers, AWARD_PRIZES, user_team_ref)
    
    # Golden Glove
    goalkeepers = [p for p in all_players if p.position == 'GK']
    golden_gloves = _get_award_winners(goalkeepers, sort_key=lambda p: p.season_clean_sheets)
    _display_and_award("Golden Glove (Most Clean Sheets)", golden_gloves, AWARD_PRIZES, user_team_ref)

    # Golden Ball (Player of the Season - based on OVR)
    golden_balls = _get_award_winners(all_players, sort_key=lambda p: p.ovr)
    _display_and_award("Golden Ball (Player of the Season)", golden_balls, AWARD_PRIZES, user_team_ref)

    # Young Player of the Year (U21)
    young_players = [p for p in all_players if p.age <= 21]
    young_player_winners = _get_award_winners(young_players, sort_key=lambda p: p.ovr)
    _display_and_award("Young Player of the Year (U21)", young_player_winners, AWARD_PRIZES, user_team_ref)

    # --- New Awards ---

    # True Captain
    eligible_captains = [p for p in all_players if p.team and p.team.get_team_ovr() > 90] # Filter for players on strong teams
    true_captains = _get_award_winners(eligible_captains, sort_key=lambda p: p.ovr)
    _display_and_award("True Captain Award", true_captains, AWARD_PRIZES, user_team_ref)

    # Under 17 Award
    under_17_players = [p for p in all_players if p.age <= 17]
    under_17_winners = _get_award_winners(under_17_players, sort_key=lambda p: p.ovr)
    _display_and_award("Under 17 Award", under_17_winners, AWARD_PRIZES, user_team_ref)

    # National Figure (Highest OVR from a significant country)
    national_figure_country = random.choice(list(NATIONAL_FIRST_NAMES.keys()))
    national_figure_players = [p for p in all_players if p.country == national_figure_country]
    national_figure_winners = _get_award_winners(national_figure_players, sort_key=lambda p: p.ovr)
    _display_and_award(f"National Figure ([cyan]{national_figure_country}[/cyan])", national_figure_winners, AWARD_PRIZES, user_team_ref)

    # FIFA Player Choice of the Year (Global)
    fifa_player_choice = _get_award_winners(all_players, sort_key=lambda p: p.ovr + (p.season_goals * 0.5) + (p.season_clean_sheets * 0.5 if p.position == 'GK' else 0)) # Mix of OVR and performance
    _display_and_award("FIFA Player Choice of the Year", fifa_player_choice, AWARD_PRIZES, user_team_ref)

    # UEFA Player Choice of the Year (European Tournaments)
    uefa_eligible_players = [p for p in all_players if p.team and p.team.league in ["Premier League", "La Liga", "Serie A", "Ligue 1"]]
    uefa_player_choice = _get_award_winners(uefa_eligible_players, sort_key=lambda p: p.ovr + (p.season_goals * 0.75) + (p.season_clean_sheets * 0.75 if p.position == 'GK' else 0))
    _display_and_award("UEFA Player Choice of the Year", uefa_player_choice, AWARD_PRIZES, user_team_ref)

    # The Football Awards (Overall best performer)
    the_football_award_winners = _get_award_winners(all_players, sort_key=lambda p: (p.ovr * 0.7) + (p.season_goals * 1.0) + (p.season_clean_sheets * 1.5 if p.position == 'GK' else 0))
    _display_and_award("The Football Awards", the_football_award_winners, AWARD_PRIZES, user_team_ref)

    # Team of the Season (Top 11 players across positions)
    console.print("\n[bold blue]--- Team of the Season ---[/bold blue]")
    tots_players = []
    positions_needed = {
        'GK': 1,
        'CB': 2, 'LB': 1, 'RB': 1, # Defenders
        'CMF': 2, 'AMF': 1, # Midfielders
        'LWF': 1, 'RWF': 1, 'CF': 1 # Forwards
    }

    # Populate Team of the Season by position
    for pos, count in positions_needed.items():
        eligible_for_pos = [p for p in all_players if p.position == pos and p not in tots_players]
        sorted_for_pos = sorted(eligible_for_pos, key=lambda p: (p.ovr * 0.8) + (p.season_goals * 0.5) + (p.season_clean_sheets * 1.0 if p.position == 'GK' else 0), reverse=True)
        tots_players.extend(sorted_for_pos[:count])
    
    # If not enough players to fill all positions, fill with remaining best overall
    if len(tots_players) < 11:
        remaining_players = [p for p in all_players if p not in tots_players]
        sorted_remaining = sorted(remaining_players, key=lambda p: p.ovr, reverse=True)
        tots_players.extend(sorted_remaining[:(11 - len(tots_players))])

    # Display and award for Team of the Season
    if tots_players:
        tots_players_sorted = sorted(tots_players, key=lambda p: p.ovr, reverse=True) # Sort again for consistent display
        tots_content = []
        for i, player in enumerate(tots_players_sorted):
            if player.team:
                player.team.budget += AWARD_PRIZES["TOTS_PLAYER"]
                if user_team_ref and player.team == user_team_ref:
                    tots_content.append(f"  [cyan]{player.name}[/cyan] ({player.position}, [blue]{player.team.name}[/blue]) - OVR: [green]{player.ovr}[/green] ([bold green]Your club awarded €{AWARD_PRIZES['TOTS_PLAYER']:,}[/bold green])")
                else:
                    tots_content.append(f"  [cyan]{player.name}[/cyan] ({player.position}, [blue]{player.team.name}[/blue]) - OVR: [green]{player.ovr}[/green]")
            else:
                tots_content.append(f"  [cyan]{player.name}[/cyan] ({player.position}) - OVR: [green]{player.ovr}[/green]")
        console.print(Panel("\n".join(tots_content), title="[bold yellow]Team of the Season[/bold yellow]", border_style="green"))
    else:
        console.print(Panel("[bold red]No players selected for Team of the Season.[/bold red]", title="[bold yellow]Team of the Season[/bold yellow]", border_style="red"))

    console.print("="*50, style="bold blue")


def simulate_competition_group_stage(all_participants, competition_name, user_team_ref):
    console.print(f"\n[bold blue]--- {competition_name} Group Stage ---[/bold blue]")
    
    # Make copies of teams for simulation to avoid modifying original stats
    sim_teams = [team.copy() for team in all_participants]
    reset_all_team_stats(sim_teams) # Reset stats for the copies for this competition

    # Randomly shuffle participants and divide into groups of 4
    random.shuffle(sim_teams)
    groups = [sim_teams[i:i + 4] for i in range(0, len(sim_teams), 4)]
    
    group_qualifiers = []

    for i, group_teams in enumerate(groups):
        group_name = chr(65 + i) # A, B, C...
        console.print(f"\n[bold yellow]--- {competition_name} - Group {group_name} ---[/bold yellow]")
        
        group_league = League(group_teams)
        group_fixtures = generate_fixtures(group_teams) # Each team plays each other twice = 6 matchdays per group
        
        for matchday_num in range(1, len(group_fixtures) + 1):
            if any(team == user_team_ref for team in group_teams): # Only prompt if user's team is in this group
                console.input(f"\n[bold green]Press Enter to simulate {competition_name} Group {group_name} Matchday {matchday_num}...[/bold green]")
            
            console.print(f"\n[bold yellow]--- Group {group_name} Matchday {matchday_num} Results ---[/bold yellow]")
            current_matchday_fixtures = group_fixtures[matchday_num-1] if matchday_num <= len(group_fixtures) else []

            for home, away in current_matchday_fixtures:
                if home is None or away is None: continue # Handle byes if any
                simulate_match(home, away, is_international_match=True, user_team_ref=user_team_ref)
            
            group_league.update_table()
            group_league.print_table()

        # After all group matches, determine qualifiers
        group_qualifiers.extend(group_league.table[:2]) # Top 2 teams qualify
        
    return group_qualifiers

def simulate_competition_knockout_stage(qualifiers, competition_name, prize_structure, user_team_ref):
    console.print(f"\n[bold blue]--- {competition_name} Knockout Stage ---[/bold blue]")
    
    current_round_teams = list(qualifiers)
    round_names = ["Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]
    
    # Ensure a power of 2 for knockout rounds, add byes if necessary
    if len(current_round_teams) > 16: # Simple cap for example
        current_round_teams = sorted(current_round_teams, key=lambda t: t.get_team_ovr(), reverse=True)[:16]
    
    winner = None
    runner_up = None
    
    round_idx = 0
    while len(current_round_teams) > 1:
        if round_idx < len(round_names):
            console.print(f"\n[bold yellow]--- {competition_name} - {round_names[round_idx]} ---[/bold yellow]")
        else:
            console.print(f"\n[bold yellow]--- {competition_name} - Round {round_idx + 1} ---[/bold yellow]") # Fallback for more rounds
            
        random.shuffle(current_round_teams)
        next_round_teams = []
        
        # Handle odd number of teams for byes or errors if logic is not perfect
        if len(current_round_teams) % 2 != 0:
            console.print(f"[bold yellow]Warning: Odd number of teams ({len(current_round_teams)}) for knockout round. One team gets a bye.[/bold yellow]")
            current_round_teams.sort(key=lambda t: t.get_team_ovr(), reverse=True)
            next_round_teams.append(current_round_teams.pop(0))

        for i in range(0, len(current_round_teams), 2):
            team1 = current_round_teams[i]
            team2 = current_round_teams[i+1]
            
            # Check if user's team is involved in this match
            is_user_match = (team1 == user_team_ref or team2 == user_team_ref)
            
            if is_user_match:
                console.input(f"\n[bold green]Press Enter to simulate match: {team1.name} vs {team2.name}...[/bold green]")

            home_goals, away_goals = simulate_match(team1, team2, is_international_match=True, user_team_ref=user_team_ref)
            console.print(f"[cyan]{team1.name}[/cyan] [bold red]{home_goals}[/bold red] - [bold red]{away_goals}[/bold red] [cyan]{team2.name}[/cyan]")
            
            current_winner = None
            current_loser = None
            if home_goals > away_goals:
                current_winner = team1
                current_loser = team2
            elif away_goals > home_goals:
                current_winner = team2
                current_loser = team1
            else: # Draw, simulate extra time/penalties
                if is_user_match:
                    console.print(f"[bold yellow]Match ends in a draw, going to penalties for {team1.name} vs {team2.name}...[/bold yellow]")
                if random.random() > 0.5:
                    current_winner = team1
                    current_loser = team2
                    if is_user_match: console.print(f"[bold green]{team1.name} wins after penalties![/bold green]")
                else:
                    current_winner = team2
                    current_loser = team1
                    if is_user_match: console.print(f"[bold green]{team2.name} wins after penalties![/bold green]")
            
            next_round_teams.append(current_winner)

            if round_idx == len(round_names) - 1: # This is the final match
                if current_winner == team1:
                    winner = team1
                    runner_up = team2
                else:
                    winner = team2
                    runner_up = team1
            
        current_round_teams = next_round_teams
        round_idx += 1
    
    # If the loop finishes, the last team in current_round_teams is the winner
    if not winner and current_round_teams: # Fallback in case loop logic missed setting winner for very small comps
        winner = current_round_teams[0]

    if winner:
        console.print(f"\n[bold green]--- {competition_name} Winner: {winner.name} ---[/bold green]")
        if hasattr(winner, 'trophies'):
            winner.trophies.append(competition_name)
    else:
        console.print(f"\n[bold red]--- No clear winner for {competition_name} ---[/bold red]")
        return # Exit if no winner was determined

    # Award prize money
    if user_team_ref.name == winner.name:
        user_team_ref.budget += prize_structure.get("winner", 0)
        console.print(f"[bold green]Congratulations! {user_team_ref.name} wins {competition_name} and awarded €{prize_structure.get('winner', 0):,}![/bold green]")
    elif runner_up and user_team_ref.name == runner_up.name:
        user_team_ref.budget += prize_structure.get("runner_up", 0)
        console.print(f"[bold green]Well done! {user_team_ref.name} is runner-up in {competition_name} and awarded €{prize_structure.get('runner_up', 0):,}![/bold green]")
    elif any(t.name == user_team_ref.name for t in qualifiers): # If user team participated but didn't win or runner-up
        user_team_ref.budget += prize_structure.get("participation", 0)
        console.print(f"[bold green]{user_team_ref.name} participated in {competition_name} and awarded €{prize_structure.get('participation', 0):,}![/bold green]")
        
    return winner

def simulate_international_tournament(qualified_teams, tournament_name, prize_structure, user_team_ref):
    """
    Simulates a simplified international tournament.
    Determines winner/runner-up based on OVR and awards prize money.
    """
    if not qualified_teams:
        console.print(f"[bold red]No teams qualified for {tournament_name}.[/bold red]")
        return

    console.print(f"\n[bold blue]--- {tournament_name} Simulation ---[/bold blue]")
    
    # Make copies of teams for simulation to avoid modifying original stats
    sim_teams = [team.copy() for team in qualified_teams]
    user_sim_team = next((st for st in sim_teams if st.name == user_team_ref.name), None)

    # Sort teams by OVR to simulate strength
    sorted_teams = sorted(sim_teams, key=lambda t: t.get_team_ovr(), reverse=True)

    if len(sorted_teams) < 2:
        console.print(f"[bold red]Not enough teams to simulate {tournament_name}.[/bold red]")
        # If user team is the only one, give them winner prize
        if user_sim_team:
            user_team_ref.budget += prize_structure.get("winner", 0) # Apply prize to original team
            console.print(f"[bold green]Congratulations! {user_team_ref.name} wins the {tournament_name} by default and awarded €{prize_structure.get('winner', 0):,}![/bold green]")
        return

    winner = sorted_teams[0]
    runner_up = sorted_teams[1]

    # Award prize money
    if user_sim_team == winner:
        user_team_ref.budget += prize_structure.get("winner", 0)
        console.print(f"[bold green]Congratulations! {user_team_ref.name} wins the {tournament_name} and awarded €{prize_structure.get('winner', 0):,}![/bold green]")
    elif user_sim_team == runner_up:
        user_team_ref.budget += prize_structure.get("runner_up", 0)
        console.print(f"[bold green]Well done! {user_team_ref.name} is runner-up in {tournament_name} and awarded €{prize_structure.get('runner_up', 0):,}![/bold green]")
    else:
        # Check if user team participated but didn't win/runner_up
        if user_team_ref in qualified_teams: # Check original list for participation
            user_team_ref.budget += prize_structure.get("participation", 0)
            console.print(f"[bold green]{user_team_ref.name} participated in {tournament_name} and awarded €{prize_structure.get('participation', 0):,}![/bold green]")

    console.print(f"[bold green]{winner.name}[/bold green] wins the [bold blue]{tournament_name}[/bold blue]!")
    console.print(f"[bold yellow]{runner_up.name}[/bold yellow] is the runner-up.")

def simulate_knockout_cup(participants, cup_name, prize_structure, user_team_ref):
    console.print(f"\n[bold blue]--- {cup_name} (Knockout) ---[/bold blue]")
    if len(participants) < 2:
        console.print(f"[bold red]Not enough participants for {cup_name}.[/bold red]")
        return

    # Make copies of teams for simulation to avoid modifying original stats
    sim_teams = [team.copy() for team in participants]
    user_sim_team = next((st for st in sim_teams if st.name == user_team_ref.name), None)

    current_round_teams = list(sim_teams)
    round_num = 1
    while len(current_round_teams) > 1:
        console.print(f"\n[bold yellow]--- {cup_name} - Round {round_num} ---[/bold yellow]")
        random.shuffle(current_round_teams)
        next_round_teams = []
        
        if len(current_round_teams) % 2 != 0: # Handle odd number of teams (bye)
            console.print(f"[bold yellow]{current_round_teams[0].name} gets a bye to the next round.[/bold yellow]")
            next_round_teams.append(current_round_teams.pop(0))

        for i in range(0, len(current_round_teams), 2):
            team1 = current_round_teams[i]
            team2 = current_round_teams[i+1]
            home_goals, away_goals = simulate_match(team1, team2, is_international_match=True, user_team_ref=user_team_ref)
            console.print(f"[cyan]{team1.name}[/cyan] [bold red]{home_goals}[/bold red] - [bold red]{away_goals}[/bold red] [cyan]{team2.name}[/cyan]")
            
            if home_goals > away_goals:
                next_round_teams.append(team1)
            elif away_goals > home_goals:
                next_round_teams.append(team2)
            else: # Draw, simulate extra time/penalties (simplified)
                console.print(f"[bold yellow]Match ends in a draw, going to penalties...[/bold yellow]")
                if random.random() > 0.5: # Random winner
                    console.print(f"[bold green]{team1.name} wins after penalties![/bold green]")
                    next_round_teams.append(team1)
                else:
                    console.print(f"[bold green]{team2.name} wins after penalties![/bold green]")
                    next_round_teams.append(team2)
        current_round_teams = next_round_teams
        round_num += 1

    winner = current_round_teams[0]
    console.print(f"\n[bold green]--- {cup_name} Winner: {winner.name} ---[/bold green]")
    if hasattr(winner, 'trophies'):
        winner.trophies.append(cup_name)
    if user_sim_team == winner:
        user_team_ref.budget += prize_structure.get("winner", 0)
        console.print(f"[bold green]Congratulations! {user_team_ref.name} wins {cup_name} and awarded €{prize_structure.get('winner', 0):,}![/bold green]")
    elif user_sim_team in sim_teams: # User team was runner-up (lost in final)
        if len(sim_teams) == 2 and user_sim_team != winner: # Special case for final
            user_team_ref.budget += prize_structure.get("runner_up", 0)
            console.print(f"[bold green]Well done! {user_team_ref.name} is runner-up in {cup_name} and awarded €{prize_structure.get('runner_up', 0):,}![/bold green]")

def simulate_home_away_cup(participants, cup_name, prize_structure, user_team_ref):
    console.print(f"\n[bold blue]--- {cup_name} (Home & Away) ---[/bold blue]")
    if len(participants) < 2:
        console.print(f"[bold red]Not enough participants for {cup_name}.[/bold red]")
        return

    # Make copies of teams for simulation to avoid modifying original stats
    sim_teams = [team.copy() for team in participants]
    user_sim_team = next((st for st in sim_teams if st.name == user_team_ref.name), None)

    current_round_teams = list(sim_teams)
    
    if len(current_round_teams) % 2 != 0:
        console.print(f"[bold yellow]Warning: Odd number of teams for {cup_name}. Skipping one team.[/bold yellow]")
        current_round_teams.pop()

    round_num = 1
    while len(current_round_teams) > 1:
        console.print(f"\n[bold yellow]--- {cup_name} - Round {round_num} ---[/bold yellow]")
        random.shuffle(current_round_teams)
        next_round_teams = []
        
        matches_this_round = []
        for i in range(0, len(current_round_teams), 2):
            matches_this_round.append((current_round_teams[i], current_round_teams[i+1]))

        for team1, team2 in matches_this_round:
            console.print(f"\n[bold magenta]--- {team1.name} vs {team2.name} ---[/bold magenta]")
            
            # Leg 1
            console.print("[bold cyan]Leg 1:[/bold cyan]")
            home_goals_1, away_goals_1 = simulate_match(team1, team2, is_international_match=True, user_team_ref=user_team_ref)
            console.print(f"[cyan]{team1.name}[/cyan] [bold red]{home_goals_1}[/bold red] - [bold red]{away_goals_1}[/bold red] [cyan]{team2.name}[/cyan]")

            # Leg 2
            console.print("[bold cyan]Leg 2:[/bold cyan]")
            home_goals_2, away_goals_2 = simulate_match(team2, team1, is_international_match=True, user_team_ref=user_team_ref) # Team2 is home
            console.print(f"[cyan]{team2.name}[/cyan] [bold red]{home_goals_2}[/bold red] - [bold red]{away_goals_2}[/bold red] [cyan]{team1.name}[/cyan]")

            # Aggregate score
            total_goals_team1 = home_goals_1 + away_goals_2
            total_goals_team2 = away_goals_1 + home_goals_2
            
            console.print(f"[bold yellow]Aggregate Score:[/bold yellow] [cyan]{team1.name}[/cyan] [bold red]{total_goals_team1}[/bold red] - [bold red]{total_goals_team2}[/bold red] [cyan]{team2.name}[/cyan]")

            if total_goals_team1 > total_goals_team2:
                next_round_teams.append(team1)
            elif total_goals_team2 > total_goals_team1:
                next_round_teams.append(team2)
            else: # Aggregate score is a draw, check away goals (simplified)
                console.print("[bold yellow]Aggregate score is level. Deciding on away goals (simplified)...[/bold yellow]")
                if away_goals_1 > away_goals_2: # Team 2 scored more away goals (in leg 1)
                    console.print(f"[bold green]{team2.name} wins on away goals![/bold green]")
                    next_round_teams.append(team2)
                elif away_goals_2 > away_goals_1: # Team 1 scored more away goals (in leg 2)
                    console.print(f"[bold green]{team1.name} wins on away goals![/bold green]")
                    next_round_teams.append(team1)
                else: # Still level, penalties
                    console.print("[bold yellow]Still level, going to penalties...[/bold yellow]")
                    if random.random() > 0.5:
                        console.print(f"[bold green]{team1.name} wins after penalties![/bold green]")
                        next_round_teams.append(team1)
                    else:
                        console.print(f"[bold green]{team2.name} wins after penalties![/bold green]")
                        next_round_teams.append(team2)
        current_round_teams = next_round_teams
        round_num += 1

    winner = current_round_teams[0]
    console.print(f"\n[bold green]--- {cup_name} Winner: {winner.name} ---[/bold green]")
    if hasattr(winner, 'trophies'):
        winner.trophies.append(cup_name)
    if user_sim_team == winner:
        user_team_ref.budget += prize_structure.get("winner", 0)
        console.print(f"[bold green]Congratulations! {user_team_ref.name} wins {cup_name} and awarded €{prize_structure.get('winner', 0):,}![/bold green]")
    elif user_sim_team in sim_teams: # User team was runner-up (lost in final)
        if len(sim_teams) == 2 and user_sim_team != winner: # Special case for final
            user_team_ref.budget += prize_structure.get("runner_up", 0)
            console.print(f"[bold green]Well done! {user_team_ref.name} is runner-up in {cup_name} and awarded €{prize_structure.get('runner_up', 0):,}![/bold green]")

def generate_sponsorship_offer(team_ovr):
    base_offer = 5_000_000 # Base sponsorship for an average team
    # Scale offer based on team OVR, with higher OVR getting disproportionately better offers
    offer = int(base_offer * (1 + (team_ovr / 100)**2)) 
    return max(10_000_000, offer) # Minimum offer

def calculate_merchandise_revenue(team, league_teams):
    base_merch = 2_000_000 # Base merchandise sales
    # Factor in team OVR for general popularity
    merch_revenue = base_merch * (1 + (team.get_team_ovr() / 100) * 0.5)

    # Factor in league position for current season popularity
    league_positions = {t.name: i for i, t in enumerate(league_teams)}
    if team.name in league_positions:
        position = league_positions[team.name]
        # Top teams get a bonus, lower teams get less or penalty
        if position < 3: # Top 3
            merch_revenue *= 1.5
        elif position < 8: # Top half
            merch_revenue *= 1.2
        else: # Bottom half
            merch_revenue *= 0.8
    
    return int(merch_revenue)

NATIONAL_TEAM_NAMES = [
    "Brazil", "Germany", "Argentina", "France", "Italy", "Spain", "England", 
    "Portugal", "Belgium", "Netherlands", "Uruguay", "Croatia", "Mexico", 
    "USA", "Colombia", "Chile", "Sweden", "Switzerland", "Denmark", "Poland",
    "Senegal", "Nigeria", "Egypt", "Japan", "South Korea", "Australia",
    "Canada", "Serbia", "Morocco", "Ghana", "Cameroon", "Ecuador"
]

def generate_national_team_squad(country_name, all_available_players):
    national_team_squad = []
    
    # Try to find existing players from clubs who match the country
    eligible_players = [p for p in all_available_players if p.country == country_name]
    eligible_players.sort(key=lambda p: p.ovr, reverse=True) # Get best players first

    # Fill with best available players up to a certain number (e.g., 23 players)
    for _ in range(min(23, len(eligible_players))):
        national_team_squad.append(eligible_players.pop(0))

    # If squad is not full, generate new strong players
    while len(national_team_squad) < 23:
        # National team players should be high OVR, similar to top club players, and match the national team's country
        national_team_squad.append(Player(
            name=f"{random.choice(['New', 'Young'])} {country_name} Talent", # Placeholder name
            position=random.choice(POSITIONS),
            age=random.randint(20, 30),
            ovr=random.randint(100, 150),
            attributes={attr: random.randint(10, 150) for attr in ATTRIBUTE_WEIGHTS[random.choice(POSITIONS)]}, # Placeholder attributes
            country=country_name
        ))
    
    # Ensure a goalkeeper is present (simplified)
    if not any(p.position == 'GK' for p in national_team_squad):
        # Remove lowest OVR outfield player if needed to make space for a GK
        if len(national_team_squad) == 23:
            # Find an outfield player to remove (e.g., lowest OVR non-GK)
            outfield_players = [p for p in national_team_squad if p.position != 'GK']
            if outfield_players:
                outfield_players.sort(key=lambda p: p.ovr)
                national_team_squad.remove(outfield_players[0])
            else: # If all players are GK, or somehow empty, just add without removing
                pass
        national_team_squad.append(Player(
            name=f"{country_name} GK",
            position='GK',
            age=random.randint(20, 30),
            ovr=random.randint(100, 150),
            attributes={attr: random.randint(10, 150) for attr in ATTRIBUTE_WEIGHTS['GK']},
            country=country_name
        ))

    # Recalculate OVR for each player based on generated attributes, then assign to team
    for p in national_team_squad:
        # OVR is already calculated in generate_player, just ensure team is None for national team context
        p.team = None 
    return national_team_squad


def simulate_world_cup(all_club_teams, user_team_ref):
    console.print(f"\n{'='*20}[bold yellow] WORLD CUP YEAR! [/bold yellow]{'='*20}", style="bold blue")
    console.print("[bold blue]--- Simulating World Cup ---[/bold blue]")

    all_players_in_game = []
    for team in all_club_teams:
        all_players_in_game.extend(team.players)

    random.shuffle(NATIONAL_TEAM_NAMES)
    participating_countries = NATIONAL_TEAM_NAMES[:32] # 32 teams for World Cup

    # Make copies of national teams for simulation to avoid modifying original club player stats
    national_teams = []
    for country_name in participating_countries:
        nat_team_copy = Team(country_name) # Create a new Team instance for the national team
        nat_team_copy.players = generate_national_team_squad(country_name, all_players_in_game)
        national_teams.append(nat_team_copy)
    
    # Reset stats for national teams (important for tournament calculation)
    reset_all_team_stats(national_teams)
    
    # Also reset player stats (goals, clean sheets) for national team players for this tournament
    for team in national_teams:
        reset_player_season_stats([team])


    # Simplified Group Stage (8 groups of 4)
    console.print("\n[bold blue]--- World Cup Group Stage ---[/bold blue]")
    random.shuffle(national_teams)
    groups = [national_teams[i:i + 4] for i in range(0, len(national_teams), 4)]

    group_winners = []
    group_runners_up = []

    for i, group in enumerate(groups):
        console.print(f"\n[bold yellow]Group {chr(65 + i)}[/bold yellow]") # A, B, C...
        group_league = League(group)
        group_fixtures = generate_fixtures(group) # Returns List[List[Tuple[Team, Team]]]

        for matchday_fixtures in group_fixtures: # Iterate through each matchday
            for home, away in matchday_fixtures: # Iterate through each match within the matchday
                if home is not None and away is not None:
                    simulate_match(home, away, is_international_match=True, user_team_ref=user_team_ref)
            group_league.update_table() # Update points after each "matchday"
        
        group_league.print_table()
        group_winners.append(group_league.table[0])
        group_runners_up.append(group_league.table[1])

    # Knockout Stage (Round of 16 to Final)
    console.print("\n[bold blue]--- World Cup Knockout Stage ---[/bold blue]")
    knockout_teams = []
    # Manual pairing for Round of 16 (Winner Group A vs Runner-up Group B, etc.)
    for i in range(len(group_winners)):
        knockout_teams.append(group_winners[i])
        knockout_teams.append(group_runners_up[(i + 1) % len(group_runners_up)]) # Simple pairing strategy

    current_round_teams = knockout_teams
    round_name_list = ["Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]
    WORLD_CUP_PRIZES = {"winner": 250_000_000, "runner_up": 100_000_000, "semi_finalist": 50_000_000}
    
    # Store teams that reach semi-finals for prize money
    semi_finalists = []

    for r_idx, r_name in enumerate(round_name_list):
        console.print(f"\n[bold yellow]--- World Cup - {r_name} ---[/bold yellow]")
        next_round_teams = []
        if len(current_round_teams) % 2 != 0: 
             if len(current_round_teams) == 1:
                 next_round_teams.append(current_round_teams[0])
                 break 
             else:
                 console.print(f"[bold yellow]Warning: Odd number of teams for {r_name}. One team gets a bye.[/bold yellow]")
                 next_round_teams.append(current_round_teams.pop(random.randrange(len(current_round_teams)))) 

        matches_this_round = []
        random.shuffle(current_round_teams) # Shuffle for fair draw
        for i in range(0, len(current_round_teams), 2):
            matches_this_round.append((current_round_teams[i], current_round_teams[i+1]))

        for team1, team2 in matches_this_round:
            # simulate_match already handles None for byes
            home_goals, away_goals = simulate_match(team1, team2, is_international_match=True, user_team_ref=user_team_ref)
            console.print(f"[cyan]{team1.name}[/cyan] [bold red]{home_goals}[/bold red] - [bold red]{away_goals}[/bold red] [cyan]{team2.name}[/cyan]")
            
            if home_goals > away_goals:
                next_round_teams.append(team1)
            elif away_goals > home_goals:
                next_round_teams.append(team2)
            else: # Draw, penalties
                console.print(f"[bold yellow]Match ends in a draw, going to penalties...[/bold yellow]")
                if random.random() > 0.5:
                    console.print(f"[bold green]{team1.name} wins after penalties![/bold green]")
                    next_round_teams.append(team1)
                else:
                    console.print(f"[bold green]{team2.name} wins after penalties![/bold green]")
                    next_round_teams.append(team2)
        
        if r_name == "Semi-Finals":
            semi_finalists.extend(current_round_teams) 

        current_round_teams = next_round_teams
        if len(current_round_teams) == 1: 
            break
    
    world_cup_winner = current_round_teams[0]

    console.print(f"\n[bold green]--- WORLD CUP WINNER: {world_cup_winner.name.upper()}!!! ---[/bold green]", style="bold magenta")

    # Award prize money to the user if their country won/runner-up/semi-finalist
    user_country_name = user_team_ref.players[0].country if user_team_ref.players else None
    
    if user_country_name:
        if world_cup_winner.name == user_country_name:
            user_team_ref.budget += WORLD_CUP_PRIZES["winner"]
            console.print(f"[bold green]Your country ({user_country_name}) won the World Cup! Your club ({user_team_ref.name}) receives a bonus of [yellow]€{WORLD_CUP_PRIZES['winner']:,}[/yellow]![/bold green]")
        elif user_country_name in [t.name for t in semi_finalists] and world_cup_winner.name != user_country_name:
            user_team_ref.budget += WORLD_CUP_PRIZES["semi_finalist"]
            console.print(f"[bold green]Your country ({user_country_name}) reached the Semi-Finals of the World Cup! Your club ({user_team_ref.name}) receives a bonus of [yellow]€{WORLD_CUP_PRIZES['semi_finalist']:,}[/yellow]![/bold green]")
    
    console.print(f"\n{'='*20}[bold yellow] WORLD CUP CONCLUDED! [/bold yellow]{'='*20}", style="bold blue")

def run_playoffs(relegated_teams, challenger_teams, user_team_ref):
    playoff_competitors = relegated_teams + challenger_teams
    reset_all_team_stats(playoff_competitors)
        
    console.print("\n[bold yellow]--- Promotion/Relegation Playoff ---[/bold yellow]")
    console.print("Teams:", ", ".join(f"[cyan]{t.name}[/cyan]" for t in playoff_competitors))
    
    playoff_fixtures = []
    for i in range(len(playoff_competitors)):
        for j in range(i + 1, len(playoff_competitors)):
            playoff_fixtures.append((playoff_competitors[i], playoff_competitors[j]))
            playoff_fixtures.append((playoff_competitors[j], playoff_competitors[i])) # Home and away

    console.input("\n[bold green]Press Enter to simulate the playoff...[/bold green]")
    
    console.print("\n[bold yellow]--- Playoff Results ---[/bold yellow]")
    for home, away in playoff_fixtures:
        home_goals, away_goals = simulate_match(home, away, user_team_ref=user_team_ref)
        console.print(f"[cyan]{home.name}[/cyan] [bold red]{home_goals}[/bold red] - [bold red]{away_goals}[/bold red] [cyan]{away.name}[/cyan]")

    playoff_table = sorted(playoff_competitors, key=lambda t: (t.points, t.goal_difference, t.goals_for), reverse=True)
    
    console.print("\n[bold yellow]--- Playoff Final Table ---[/bold yellow]")
    playoff_table_display = Table(
        title="[bold green]Playoff Standings[/bold green]",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    playoff_table_display.add_column("#", style="dim")
    playoff_table_display.add_column("Team", style="cyan", min_width=20)
    playoff_table_display.add_column("P", justify="right")
    playoff_table_display.add_column("W", justify="right")
    playoff_table_display.add_column("D", justify="right")
    playoff_table_display.add_column("L", justify="right")
    playoff_table_display.add_column("GF", justify="right")
    playoff_table_display.add_column("GA", justify="right")
    playoff_table_display.add_column("GD", justify="right")
    playoff_table_display.add_column("Pts", justify="right", style="bold yellow")
    
    for i, team in enumerate(playoff_table, 1):
        playoff_table_display.add_row(
            str(i),
            team.name,
            str(team.games_played),
            str(team.wins),
            str(team.draws),
            str(team.losses),
            str(team.goals_for),
            str(team.goals_against),
            str(team.goal_difference),
            str(team.points)
        )
    console.print(playoff_table_display)

    promoted = playoff_table[:2]
    console.print(f"\n[bold green]Congratulations to {promoted[0].name} and {promoted[1].name} on promotion![/bold green]")
    return promoted, playoff_table[2:]