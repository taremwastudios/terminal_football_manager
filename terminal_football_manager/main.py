import random
import json
import os

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

from .constants import COUNTRIES, NATIONAL_FIRST_NAMES, NATIONAL_LAST_NAMES, FIRST_NAMES, LAST_NAMES, ATTRIBUTE_WEIGHTS, POSITIONS, TRAINER_TIERS
from .persistence import save_game, load_game
from .models import Player, Team
from .player_career import run_player_career_mode, HeroPlayer
from .fut_mode import run_fut_mode, FutClub
from .game_logic import (
    League, generate_fixtures, assign_goal_scorers, simulate_match, 
    reset_all_team_stats, reset_player_season_stats, 
    simulate_competition_group_stage, simulate_competition_knockout_stage, 
    simulate_international_tournament, simulate_knockout_cup, 
    simulate_home_away_cup, generate_sponsorship_offer, 
    calculate_merchandise_revenue, generate_national_team_squad, 
    simulate_world_cup, AWARD_PRIZES, NATIONAL_TEAM_NAMES,
    present_season_awards, run_playoffs
)

# --- Data Structures ---


# --- Generation Logic ---

def generate_player_name(player_country=None):
    first_name_pool = FIRST_NAMES
    last_name_pool = LAST_NAMES

    if player_country and player_country in NATIONAL_FIRST_NAMES and NATIONAL_FIRST_NAMES[player_country]:
        first_name_pool = NATIONAL_FIRST_NAMES[player_country]
    if player_country and player_country in NATIONAL_LAST_NAMES and NATIONAL_LAST_NAMES[player_country]:
        last_name_pool = NATIONAL_LAST_NAMES[player_country]
    
    return f"{random.choice(first_name_pool)} {random.choice(last_name_pool)}"

def generate_player(is_youth=False, min_ovr=None, max_ovr=None, position=None, country_pool=None):
    if position is None:
        position = random.choice(POSITIONS)
    
    if is_youth:
        age = random.randint(16, 18)
        base_ovr_min = 40 if min_ovr is None else min_ovr
        base_ovr_max = 65 if max_ovr is None else max_ovr
    else:
        age = random.randint(17, 34)
        base_ovr_min = 50 if min_ovr is None else min_ovr
        base_ovr_max = 75 if max_ovr is None else max_ovr
    
    base_ovr = random.randint(base_ovr_min, base_ovr_max)

    attributes = {attr: int(base_ovr * (1 + (random.random() - 0.5) * 0.5)) for attr in ATTRIBUTE_WEIGHTS[position]}
    for attr, weight in ATTRIBUTE_WEIGHTS[position].items():
        attributes[attr] = int(attributes[attr] * (1 + weight))
        attributes[attr] = max(10, min(attributes[attr], 130)) # Cap attributes, allowing high values for strong players
    ovr = int(sum(attributes.values()) / len(attributes))

    # Robust Scouting: Assign potential
    potential = random.randint(ovr + 5, min(150, ovr + 30))
    if is_youth and random.random() < 0.1: # 10% chance for a youth wonderkid
        potential = random.randint(130, 160)

    player_country = random.choice(country_pool) if country_pool else random.choice(COUNTRIES)

    return Player(generate_player_name(player_country), position, age, ovr, attributes, player_country, potential=potential)

def create_teams():
    all_club_teams = []

    # Domestic Leagues
    domestic_league_names = [
        "Superstars", "Kitoha FC", "Red Stars", "FC Pastro", "SC Annex",
        "Tripple X", "CityBoys", "FC Kabanana", "Nevis FC", "Guliza",
        "Dragon Stars", "Young Stars", "FC Pacific Coast", "The Blues"
    ]
    domestic_playoff_names = ["Dreamwarriors", "CF Tesa"]
    
    # International Leagues
    international_league_groups = {
        "Premier League": ["Manchester City", "Arsenal", "Liverpool", "Chelsea", "Manchester United", "Tottenham Hotspur", "Newcastle United", "Brighton & Hove Albion"],
        "La Liga": ["Real Madrid", "Barcelona", "Atletico Madrid", "Girona", "Real Sociedad", "Athletic Club", "Real Betis", "Sevilla"],
        "Serie A": ["Inter Milan", "AC Milan", "Juventus", "Napoli", "Roma", "Lazio", "Atalanta", "Fiorentina"],
        "Ligue 1": ["Paris Saint-Germain", "Monaco", "Lille", "Nice", "Marseille", "Rennes", "Lens", "Lyon"]
    }

    # Define country pools for biasing
    HOME_LEAGUE_PRIORITY_COUNTRIES = ["Nigeria", "Uganda", "Kenya", "South Africa"]
    EUROPEAN_PRIORITY_COUNTRIES = ["England", "Spain", "France", "Germany", "Italy", "Portugal", "Netherlands", "Belgium"]
    GLOBAL_TALENT_MIX_COUNTRIES = [c for c in COUNTRIES if c not in HOME_LEAGUE_PRIORITY_COUNTRIES + EUROPEAN_PRIORITY_COUNTRIES]
    GLOBAL_TALENT_MIX_COUNTRIES = list(set(GLOBAL_TALENT_MIX_COUNTRIES + HOME_LEAGUE_PRIORITY_COUNTRIES[:2] + EUROPEAN_PRIORITY_COUNTRIES[:2])) # Add some overlap

    # Star Players Data
    star_players_data = [
        # Our Domestic League Stars
        {"name": "Mark Muonge", "ovr": 120, "pos": "GK", "team": "Superstars", "country": "Uganda"},
        {"name": "Akankunda Emmanuel", "ovr": 113, "pos": "RWF", "team": "Superstars", "country": "Uganda"},
        {"name": "T. Trevor", "ovr": 111, "pos": "AMF", "team": "Superstars", "country": "Uganda"},
        {"name": "Loughlan", "ovr": 108, "pos": "AMF", "team": "Superstars", "country": "England"},
        {"name": "T. Andrew", "ovr": 119, "pos": "CF", "team": "Superstars", "country": "Uganda"},
        {"name": "Tomy Chan", "ovr": 117, "pos": "CMF", "team": "Superstars", "country": "China"},
        {"name": "Mark Davins", "ovr": 103, "pos": "AMF", "team": "Superstars", "country": "Uganda"},
        {"name": "Ariho Raymond", "ovr": 105, "pos": "CB", "team": "Superstars", "country": "Uganda"},
        {"name": "Cosmas", "ovr": 102, "pos": "LB", "team": "Superstars", "country": "Uganda"},
        {"name": "Balikudembe", "ovr": 97, "pos": "RB", "team": "Superstars", "country": "Uganda"},
        {"name": "Rukundo Emmanuel", "ovr": 99, "pos": "CB", "team": "Superstars", "country": "Uganda"},
        {"name": "Isaiah", "ovr": 101, "pos": "AMF", "team": "FC Pastro", "country": "Uganda"},
        {"name": "Naju Godwin", "ovr": 117, "pos": "LWF", "team": "FC Pastro", "country": "Nigeria"},
        {"name": "Innocent", "ovr": 113, "pos": "GK", "team": "FC Pastro", "country": "Kenya"},
        {"name": "Arinaitwe Davies Kapara", "ovr": 111, "pos": "LWF", "team": "FC Pastro", "country": "Uganda"},
        {"name": "Felix B", "ovr": 89, "pos": "RB", "team": "FC Pastro", "country": "South Africa"},
        {"name": "Agustus Kanyantabe", "ovr": 118, "pos": "RWF", "team": "FC Pastro", "country": "Uganda"},
        {"name": "Ahimibisibwe John Stuart", "ovr": 110, "pos": "CF", "team": "Red Stars", "country": "Nigeria"},
        {"name": "Barrerio", "ovr": 112, "pos": "LB", "team": "Kitoha FC", "country": "Spain"},
        {"name": "Avitus", "ovr": 115, "pos": "CB", "team": "Kitoha FC", "country": "Uganda"},
        {"name": "Shield", "ovr": 116, "pos": "RB", "team": "Kitoha FC", "country": "England"},
        {"name": "Amanya Andrew", "ovr": 113, "pos": "CF", "team": "Kitoha FC", "country": "Uganda"},
        {"name": "Nevis", "ovr": 121, "pos": "CF", "team": "Nevis FC", "country": "Portugal"},
        {"name": "Benjamin", "ovr": 114, "pos": "CF", "team": "Nevis FC", "country": "South Africa"},
        {"name": "Nasa", "ovr": 122, "pos": "CF", "team": "Dragon Stars", "country": "Brazil"},
        {"name": "Regina Nantes", "ovr": 121, "pos": "AMF", "team": "Dragon Stars", "country": "France"},
        {"name": "Fredrick M", "ovr": 101, "pos": "CMF", "team": "Dragon Stars", "country": "Kenya"},
        {"name": "Lawrence", "ovr": 112, "pos": "CB", "team": "FC Kabanana", "country": "Nigeria"},
        {"name": "Aine Arnold", "ovr": 117, "pos": "CF", "team": "Young Stars", "country": "Uganda"},
        {"name": "Ainembabazi Brian", "ovr": 119, "pos": "LB", "team": "Young Stars", "country": "Uganda"},
        {"name": "Eric", "ovr": 101, "pos": "CMF", "team": "The Blues", "country": "England"},
        # Premier League Stars - added specific countries
        {"name": "Erling Haaland", "ovr": 130, "pos": "CF", "team": "Manchester City", "country": "Norway"},
        {"name": "Kevin De Bruyne", "ovr": 128, "pos": "CMF", "team": "Manchester City", "country": "Belgium"},
        {"name": "Bukayo Saka", "ovr": 125, "pos": "RWF", "team": "Arsenal", "country": "England"},
        {"name": "Mohamed Salah", "ovr": 127, "pos": "RWF", "team": "Liverpool", "country": "Egypt"},
        {"name": "Virgil van Dijk", "ovr": 126, "pos": "CB", "team": "Liverpool", "country": "Netherlands"},
        {"name": "Bruno Fernandes", "ovr": 124, "pos": "AMF", "team": "Manchester United", "country": "Portugal"},
        # La Liga Stars - added specific countries
        {"name": "Jude Bellingham", "ovr": 129, "pos": "CMF", "team": "Real Madrid", "country": "England"},
        {"name": "Vinicius Jr.", "ovr": 127, "pos": "LWF", "team": "Real Madrid", "country": "Brazil"},
        {"name": "Robert Lewandowski", "ovr": 126, "pos": "CF", "team": "Barcelona", "country": "Poland"},
        {"name": "Marc-Andre ter Stegen", "ovr": 125, "pos": "GK", "team": "Barcelona", "country": "Germany"},
        {"name": "Antoine Griezmann", "ovr": 124, "pos": "SS", "team": "Atletico Madrid", "country": "France"},
        # Serie A Stars - added specific countries
        {"name": "Lautaro Martinez", "ovr": 126, "pos": "CF", "team": "Inter Milan", "country": "Argentina"},
        {"name": "Rafael Leão", "ovr": 125, "pos": "LWF", "team": "AC Milan", "country": "Portugal"},
        {"name": "Victor Osimhen", "ovr": 127, "pos": "CF", "team": "Napoli", "country": "Nigeria"},
        {"name": "Federico Chiesa", "ovr": 123, "pos": "RWF", "team": "Juventus", "country": "Italy"},
        # Ligue 1 Stars - added specific countries
        {"name": "Kylian Mbappé", "ovr": 132, "pos": "LWF", "team": "Paris Saint-Germain", "country": "France"},
        {"name": "Neymar Jr.", "ovr": 128, "pos": "LWF", "team": "Paris Saint-Germain", "country": "Brazil"},
    ]

    all_teams_map = {} # To quickly find teams by name

    # Create domestic league teams
    for name in domestic_league_names:
        team = Team(name, league="Domestic League")
        all_club_teams.append(team)
        all_teams_map[name] = team
    
    # Create domestic playoff contenders
    for name in domestic_playoff_names:
        team = Team(name, league="Domestic Playoff")
        all_club_teams.append(team)
        all_teams_map[name] = team

    # Create international league teams
    for league_name, teams_in_league in international_league_groups.items():
        for name in teams_in_league:
            team = Team(name, league=league_name)
            all_club_teams.append(team)
            all_teams_map[name] = team


    # Add star players to their teams
    for star_data in star_players_data:
        team_name = star_data["team"]
        if team_name in all_teams_map:
            team = all_teams_map[team_name]
            
            pos = star_data["pos"]
            ovr = star_data["ovr"]
            country = star_data.get("country", random.choice(COUNTRIES)) # Use specified country or random
            base_attrs = {attr: random.randint(ovr - 20, ovr - 5) for attr in ATTRIBUTE_WEIGHTS[pos]}
            weighted_attrs = {}
            for attr, weight in ATTRIBUTE_WEIGHTS[pos].items():
                weighted_attrs[attr] = int(base_attrs[attr] + (ovr * 0.2 * weight))
                weighted_attrs[attr] = max(10, min(weighted_attrs[attr], 130)) # Cap attributes, but allow stars to exceed normal caps

            star_player = Player(
                name=star_data["name"],
                position=pos,
                age=random.randint(19, 29), # Stars are typically in their prime
                ovr=ovr,
                attributes=weighted_attrs,
                country=country # Use the specific country for star players
            )
            team.add_player(star_player)

    # Fill remaining slots with random players and assign budgets
    for team in all_club_teams:
        num_existing_players = len(team.players)
        num_random_to_add = 22 - num_existing_players # Ensure each team has 22 players
        
        for _ in range(num_random_to_add):
            if team.league in international_league_groups: # For strong international teams
                # Bias international teams towards European and global talent
                if random.random() < 0.7: # 70% chance of European priority
                    player_country_pool = EUROPEAN_PRIORITY_COUNTRIES
                else: # 30% chance of global talent mix
                    player_country_pool = GLOBAL_TALENT_MIX_COUNTRIES
                
                team.add_player(generate_player(is_youth=False, min_ovr=100, max_ovr=140, country_pool=player_country_pool))
            else: # For domestic league teams (and playoffs)
                # Bias domestic teams towards specified African countries
                if random.random() < 0.8: # 80% chance of home league priority
                    player_country_pool = HOME_LEAGUE_PRIORITY_COUNTRIES
                else: # 20% chance of global talent mix
                    player_country_pool = GLOBAL_TALENT_MIX_COUNTRIES
                
                team.add_player(generate_player(is_youth=False, country_pool=player_country_pool))
        
        # Initialize the youth academy
        for _ in range(random.randint(5, 10)):
            # Youth academy players also follow team's country bias
            if team.league in international_league_groups:
                if random.random() < 0.7:
                    player_country_pool = EUROPEAN_PRIORITY_COUNTRIES
                else:
                    player_country_pool = GLOBAL_TALENT_MIX_COUNTRIES
                team.youth_academy.append(generate_player(is_youth=True, country_pool=player_country_pool))
            else:
                if random.random() < 0.8:
                    player_country_pool = HOME_LEAGUE_PRIORITY_COUNTRIES
                else:
                    player_country_pool = GLOBAL_TALENT_MIX_COUNTRIES
                team.youth_academy.append(generate_player(is_youth=True, country_pool=player_country_pool))


        # Assign budget based on team OVR and league importance
        team_ovr = team.get_team_ovr()
        if team.league in international_league_groups:
            team.budget = int(7 * (team_ovr * 2_000_000 + random.randint(50_000_000, 100_000_000)))
        else: # Domestic or Playoff teams
            team.budget = int(7 * (team_ovr * 1_000_000 + random.randint(5_000_000, 15_000_000)))
            
    return all_club_teams



















def run_off_season_training(all_teams, user_team_ref):
    console.print("\n[bold blue]--- Off-Season Training & Development ---[/bold blue]")
    
    for team in all_teams:
        players_to_remove_from_team = []
        players_to_remove_from_academy = []

        # Process senior players
        for player in team.players:
            player.age += 1
            old_ovr = player.ovr

            if player.age >= 40: # Retirement check
                if team == user_team_ref: # Only print retirement for user's team
                    console.print(f"[bold red][RETIREMENT][/bold red] [cyan]{player.name}[/cyan] ([yellow]{player.age}[/yellow], [blue]{player.team.name if player.team else 'N/A'}[/blue]) has retired!")
                players_to_remove_from_team.append(player)
                continue 

            ovr_change = 0
            if player.age < 24:
                # Young players grow towards their potential
                growth_room = player.potential - player.ovr
                if growth_room > 0:
                    ovr_change = random.randint(1, min(5, max(1, growth_room // 5)))
                else:
                    ovr_change = random.randint(0, 1)
            elif 24 <= player.age <= 29:
                ovr_change = random.randint(0, 1)
            elif 30 <= player.age <= 32:
                ovr_change = random.randint(-1, 0)
            else:
                ovr_change = random.randint(-3, -1)
            
            if player.trainer_level > 0:
                tier_name = list(TRAINER_TIERS.keys())[player.trainer_level - 1]
                boost = TRAINER_TIERS[tier_name]['boost']
                ovr_change += boost
                if team == user_team_ref: # Only print training boost for user's team
                    console.print(f"[bold green][TRAINING][/bold green] [cyan]{player.name}[/cyan] gets a [bold]+{boost} OVR[/bold] boost from their {tier_name} trainer!")

            player.ovr = max(10, player.ovr + ovr_change)

            if ovr_change != 0:
                for _ in range(abs(ovr_change)):
                    attr = random.choice(list(player.attributes.keys()))
                    change = 1 if ovr_change > 0 else -1
                    player.attributes[attr] = max(10, min(125, player.attributes[attr] + change))
            
            if team == user_team_ref and player.ovr != old_ovr: # Only print OVR changes for user's team
                console.print(f"[cyan]{player.name}[/cyan] ([yellow]{player.age}[/yellow]) OVR: [red]{old_ovr}[/red] -> [green]{player.ovr}[/green]")
            player.trainer_level = 0 # Reset trainer after use for the season

        # Process youth academy players
        for player in team.youth_academy:
            player.age += 1
            old_ovr = player.ovr

            if player.age >= 40: # Retirement check for youth players (unlikely but possible)
                if team == user_team_ref: # Only print retirement for user's team youth
                    console.print(f"[bold red][RETIREMENT][/bold red] Youth player [cyan]{player.name}[/cyan] ([yellow]{player.age}[/yellow], [blue]{player.team.name if player.team else 'N/A'}[/blue]) has retired from the academy!")
                players_to_remove_from_academy.append(player)
                continue

            ovr_change = 0
            if player.age < 24:
                growth_room = player.potential - player.ovr
                if growth_room > 0:
                    ovr_change = random.randint(1, min(5, max(1, growth_room // 4)))
                else:
                    ovr_change = random.randint(0, 1)
            elif 24 <= player.age <= 29:
                ovr_change = random.randint(0, 1)
            elif 30 <= player.age <= 32:
                ovr_change = random.randint(-1, 0)
            else:
                ovr_change = random.randint(-3, -1)
            
            player.ovr = max(10, player.ovr + ovr_change)

            if team == user_team_ref and player.ovr != old_ovr: # Only print OVR changes for user's team youth
                console.print(f"Youth: [cyan]{player.name}[/cyan] ([yellow]{player.age}[/yellow]) OVR: [red]{old_ovr}[/red] -> [green]{player.ovr}[/green]")

        # Remove retired players from the team and academy
        for player in players_to_remove_from_team:
            team.remove_player(player)
        for player in players_to_remove_from_academy:
            team.youth_academy.remove(player)

    if random.random() < 0.1:
        wonderkid = generate_player(is_youth=True)
        wonderkid.ovr = random.randint(98, 103)
        eligible_teams = [t for t in all_teams if t.name not in ["Dreamwarriors", "CF Tesa"]]
        if eligible_teams:
            chosen_team = random.choice(eligible_teams)
            chosen_team.youth_academy.append(wonderkid)
            wonderkid.team = chosen_team 
            console.print(Panel(f"[bold green]A generational talent has emerged![/bold green]\n[cyan]{wonderkid.age}[/cyan]-year-old [bold]{wonderkid.position}[/bold], [green]{wonderkid.ovr} OVR[/green]) has joined the [blue]{chosen_team.name}[/blue] youth academy!", title="[bold yellow]BREAKING NEWS[/bold yellow]", border_style="yellow"))

def restock_youth_academy(all_teams, user_team_ref): # Added user_team_ref
    console.print("\n[bold blue]--- Youth Academies Restocking ---[/bold blue]")
    
    # Define country pools for biasing within this scope
    HOME_LEAGUE_PRIORITY_COUNTRIES = ["Nigeria", "Uganda", "Kenya", "South Africa"]
    EUROPEAN_PRIORITY_COUNTRIES = ["England", "Spain", "France", "Germany", "Italy", "Portugal", "Netherlands", "Belgium"]
    GLOBAL_TALENT_MIX_COUNTRIES = [c for c in COUNTRIES if c not in HOME_LEAGUE_PRIORITY_COUNTRIES + EUROPEAN_PRIORITY_COUNTRIES]
    GLOBAL_TALENT_MIX_COUNTRIES = list(set(GLOBAL_TALENT_MIX_COUNTRIES + HOME_LEAGUE_PRIORITY_COUNTRIES[:2] + EUROPEAN_PRIORITY_COUNTRIES[:2])) # Add some overlap


    for team in all_teams:
        num_new_youth = 1 + (team.academy_level // 10) 
        for _ in range(num_new_youth):
            # Determine player country pool based on team league
            # Assuming international_league_groups is defined or passed - let's define it here for clarity or rely on global scope
            international_league_groups_check = ["Premier League", "La Liga", "Serie A", "Ligue 1"] # Simplified check
            
            if team.league in international_league_groups_check: 
                if random.random() < 0.7:
                    player_country_pool = EUROPEAN_PRIORITY_COUNTRIES
                else:
                    player_country_pool = GLOBAL_TALENT_MIX_COUNTRIES
            else: # Domestic or Playoff teams
                if random.random() < 0.8:
                    player_country_pool = HOME_LEAGUE_PRIORITY_COUNTRIES
                else:
                    player_country_pool = GLOBAL_TALENT_MIX_COUNTRIES
            
            new_player = generate_player(is_youth=True, country_pool=player_country_pool) # Pass country_pool
            new_player.ovr += team.academy_level // 10 
            team.youth_academy.append(new_player)
            new_player.team = team 
        if team == user_team_ref and num_new_youth > 0: # Only print for user's team
            console.print(f"[blue]{team.name}'s[/blue] academy has produced [bold green]{num_new_youth}[/bold green] new talent(s).")

def run_youth_promotions(user_team):
    while True:
        console.print("\n[bold blue]--- Youth Academy Promotions ---[/bold blue]")
        if not user_team.youth_academy:
            console.print("[red]Your youth academy is empty.[/red]"); console.input("[green]Press Enter to continue...[/green]"); return

        console.print(f"Your senior squad currently has [bold]{len(user_team.players)}/22[/bold] players.")
        console.print("Select a player to promote to the senior squad (max 22 players).")
        for i, p in enumerate(user_team.youth_academy): console.print(f"[{i+1}] [cyan]{p}[/cyan]")
        
        try:
            choice = int(console.input("Enter player number to promote (or 0 to go back): "))
            if choice == 0: return
            if 1 <= choice <= len(user_team.youth_academy):
                if len(user_team.players) >= 22:
                    console.print("[red]\nSenior squad is full! You must sell or release a player first.[/red]"); continue
                
                player = user_team.youth_academy.pop(choice - 1)
                user_team.add_player(player) 
                console.print(f"\n[bold green]{player.name}[/bold green] has been promoted to the senior squad!")
            else: console.print("[red]Invalid choice.[/red]")
        except ValueError: console.print("[red]Invalid input.[/red]")

def run_management_menu(user_team):
    while True:
        console.print(Panel(
            f"Your budget: [green]€{user_team.budget:,}[/green]\n"
            f"Total Squad Value: [green]€{user_team.total_squad_value:,}[/green]\n"
            f"Total Weekly Wage Bill: [green]€{user_team.total_wage_bill:,}[/green]",
            title="[bold blue]Management Menu[/bold blue]",
            border_style="blue"
        ))
        
        stadium_cost = 200_000 * user_team.stadium_level
        academy_cost = 150_000 * user_team.academy_level

        console.print(f"\n1. Upgrade Stadium")
        console.print(f"   - Level: [bold yellow]{user_team.stadium_level}[/bold yellow]/100 | Capacity: {user_team.stadium_capacity:,}")
        console.print(f"   - Upgrade Cost: [red]€{stadium_cost:,}[/red]")

        console.print(f"\n2. Upgrade Youth Academy")
        console.print(f"   - Level: [bold yellow]{user_team.academy_level}[/bold yellow]/100")
        console.print(f"   - Upgrade Cost: [red]€{academy_cost:,}[/red]")

        console.print("\n3. Assign Special Player Training")
        console.print("\n4. Exit Management Menu")

        choice = console.input("[bold yellow]Enter your choice:[/bold yellow] ")
        if choice == '1':
            if user_team.stadium_level >= 100: console.print("[red]\nStadium is already max level.[/red]"); continue
            if user_team.budget >= stadium_cost:
                user_team.budget -= stadium_cost; user_team.stadium_level += 1
                console.print("[green]\nStadium upgrade successful![/green]")
            else: console.print("[red]\nNot enough budget.[/red]")
        elif choice == '2':
            if user_team.academy_level >= 100: console.print("[red]\nYouth Academy is already max level.[/red]"); continue
            if user_team.budget >= academy_cost:
                user_team.budget -= academy_cost; user_team.academy_level += 1
                console.print("[green]\nYouth Academy upgrade successful![/green]")
            else: console.print("[red]\nNot enough budget.[/red]")
        elif choice == '3': run_special_training_menu(user_team)
        elif choice == '4': return
        else: console.print("[red]Invalid choice.[/red]")

def run_special_training_menu(user_team):
    while True:
        console.print("\n[bold blue]--- Special Training Assignment ---[/bold blue]")
        console.print("Select a player to assign a special trainer to for this season.")
        
        players = sorted(user_team.players, key=lambda p: p.name)
        for i, p in enumerate(players): console.print(f"[{i+1}] [cyan]{p}[/cyan]")

        try:
            player_choice = int(console.input("[bold yellow]Enter player number (or 0 to go back):[/bold yellow] "))
            if player_choice == 0: return
            if 1 <= player_choice <= len(players):
                player = players[player_choice - 1]
                if player.trainer_level > 0: console.print(f"[red]\n{player.name} already has a trainer assigned for this season.[/red]"); continue

                console.print(f"\nSelect a trainer tier for [cyan]{player.name}[/cyan]:")
                tiers_list = list(TRAINER_TIERS.items())
                for i, (name, data) in enumerate(tiers_list): console.print(f"[{i+1}] [magenta]{name}[/magenta] - Cost: [red]€{data['cost']:,}[/red], Boost: [green]+{data['boost']} OVR[/green]")
                
                trainer_choice = int(console.input("[bold yellow]Enter tier (or 0 to cancel):[/bold yellow] "))
                if 1 <= trainer_choice <= len(tiers_list):
                    name, data = tiers_list[trainer_choice-1]
                    if user_team.budget >= data['cost']:
                        user_team.budget -= data['cost']
                        player.trainer_level = trainer_choice
                        console.print(f"[bold green]\nSUCCESS! A {name} trainer assigned to {player.name}.[/bold green]")
                    else: console.print("[red]\nNot enough budget.[/red]")
                elif trainer_choice != 0: console.print("[red]Invalid tier.[/red]")
            else: console.print("[red]Invalid player choice.[/red]")
        except ValueError: console.print("[red]Invalid input.[/red]")

def run_transfer_window(league_teams, user_team, window_name, all_club_teams): # Added all_club_teams
    console.print(f"\n[bold blue]--- {window_name} Transfer Window is OPEN ---[/bold blue]")
    
    # Ensure all players are linked to their current teams for transfer logic
    for team in all_club_teams: # Iterate through all clubs
        for player in team.players:
            player.team = team
        for player in team.youth_academy:
            player.team = team

    other_teams = [t for t in all_club_teams if t != user_team] # Consider all clubs for transfers
    
    transfer_list = []
    # AI teams putting players on transfer list
    for team in other_teams:
        if not team.players: continue
        players_sorted_by_age = sorted(team.players, key=lambda p: p.age, reverse=True)
        
        # Logic to decide which players AI puts on transfer list
        # Older players
        if players_sorted_by_age and random.random() < 0.3: # 30% chance for oldest player
            transfer_list.append({"player": players_sorted_by_age[0], "seller": team})
        
        # Young promising players (less chance)
        eligible_young_players = [p for p in team.players if p.age < 28 and p not in [item['player'] for item in transfer_list]]
        if eligible_young_players and random.random() < 0.15: # 15% chance for a young player
            transfer_list.append({"player": random.choice(eligible_young_players), "seller": team})
        
        # Surplus players
        if len(team.players) > 22 and random.random() < 0.5: # 50% chance to list a surplus player
            extra_players = [p for p in team.players if p not in [item['player'] for item in transfer_list]]
            if extra_players:
                transfer_list.append({"player": random.choice(extra_players), "seller": team})

    while True:
        console.print(Panel(
            f"Your budget: [green]€{user_team.budget:,}[/green]\n"
            f"Your Squad Value: [green]€{user_team.total_squad_value:,}[/green]\n"
            f"Your Weekly Wage Bill: [green]€{user_team.total_wage_bill:,}[/green]",
            title="[bold blue]Transfer Window[/bold blue]",
            border_style="blue"
        ))
        console.print("\n[bold yellow]1. View Squad[/bold yellow] | [bold yellow]2. Buy[/bold yellow] | [bold yellow]3. Sell[/bold yellow] | [bold yellow]4. Youth Academy[/bold yellow] | [bold yellow]5. Finish Business[/bold yellow]")
        choice = console.input("[bold yellow]Choice:[/bold yellow] ")
        
        if choice == '1':
            console.print(f"\n[bold blue]--- {user_team.name} Squad ---[/bold blue]")
            for p in sorted(user_team.players, key=lambda p: p.ovr, reverse=True): console.print(f"- [cyan]{p}[/cyan]")
        elif choice == '2': # Buy Players
            
            # Combine transfer list and scouted international players
            available_players_to_buy = list(transfer_list) # Start with players already listed by AI
            
            # Define international league groups for filtering
            international_league_groups_keys = ["Premier League", "La Liga", "Serie A", "Ligue 1"]
            
            scouting_options = []
            for team in all_club_teams:
                if team.league in international_league_groups_keys and team != user_team:
                    # Select a few top players from stronger international teams for scouting
                    top_players = sorted(team.players, key=lambda p: p.ovr, reverse=True)[:random.randint(1,4)] # Offer 1-4 top players
                    for p in top_players:
                        # Ensure player is not already in transfer_list or user's team
                        if p.team != user_team and not any(item['player'] == p for item in available_players_to_buy):
                            scouting_options.append({"player": p, "seller": team})
            
            if scouting_options:
                console.print("\n[bold blue]--- International Scouting Opportunities ---[/bold blue]")
                random.shuffle(scouting_options) # Mix up the scouted players
                available_players_to_buy.extend(scouting_options[:random.randint(5, 10)]) # Present a few random scouted players
                
            if not available_players_to_buy: console.print("[red]No players available for purchase.[/red]"); continue

            console.print("\n[bold blue]--- Players Available for Purchase ---[/bold blue]")
            for i, item in enumerate(available_players_to_buy): 
                console.print(f"[{i+1}] [cyan]{item['player']}[/cyan] (From: [blue]{item['seller'].name}[/blue])")
            
            try:
                buy_choice = int(console.input(f"[bold yellow]Enter player number to buy (1-{len(available_players_to_buy)}, or 0 to back):[/bold yellow] "))
                if buy_choice == 0: continue
                
                if 1 <= buy_choice <= len(available_players_to_buy):
                    selected_item = available_players_to_buy[buy_choice - 1]
                    player, seller_team = selected_item['player'], selected_item['seller']
                    
                    # Dynamic pricing for international players or highly sought players
                    transfer_fee = player.market_value
                    if player.ovr > 90: # Boost price for very high OVR players
                        transfer_fee = int(transfer_fee * random.uniform(1.2, 1.8)) 
                    if player.team.league in international_league_groups_keys: # Further boost for international league players
                        transfer_fee = int(transfer_fee * random.uniform(1.1, 1.5))

                    if user_team.budget >= transfer_fee:
                        confirm = console.input(f"[bold yellow]Confirm purchase of {player.name} from {seller_team.name} for [green]€{transfer_fee:,}[/green]? (yes/no): [/bold yellow]").lower()
                        if confirm == 'yes':
                            user_team.budget -= transfer_fee
                            seller_team.budget += transfer_fee
                            seller_team.remove_player(player) 
                            user_team.add_player(player) 
                            # Remove the player from the transfer_list to prevent duplicate purchases
                            transfer_list = [item for item in transfer_list if item['player'] != player]
                            console.print(f"\n[bold green]SUCCESS! {player.name} joins {user_team.name} for €{transfer_fee:,}![/bold green]")
                        else: console.print("[red]Transfer cancelled.[/red]")
                    else: console.print("[red]Not enough budget.[/red]")
                else: console.print("[red]Invalid choice.[/red]")
            except (ValueError, IndexError): console.print("[red]Invalid input.[/red]")

        elif choice == '3': # Sell Players
            if not user_team.players: console.print("[red]Your squad is empty.[/red]"); continue
            console.print("\n[bold blue]--- Select a Player to Sell ---[/bold blue]")
            for i, p in enumerate(user_team.players): console.print(f"[{i+1}] [cyan]{p}[/cyan]")
            try:
                sell_choice = int(console.input("[bold yellow]Sell player # (0 to back):[/bold yellow] "))
                if sell_choice == 0: continue
                if 1 <= sell_choice <= len(user_team.players):
                    player_to_sell = user_team.players[sell_choice - 1]
                    
                    # AI teams making offers for user's players
                    # Prioritize stronger, wealthier AI teams for making offers
                    eligible_buyers = [t for t in other_teams if t.budget >= player_to_sell.market_value and len(t.players) < 30]
                    
                    # Filter for teams that are likely to be interested (i.e., player would be an improvement)
                    interested_buyers = [t for t in eligible_buyers if player_to_sell.ovr > t.get_team_ovr() - 15] # AI won't buy much worse player
                    
                    if interested_buyers and random.random() < 0.8: # High chance of an offer if interested buyers exist
                        # Give preference to richer, stronger teams from international leagues
                        international_league_groups_keys = ["Premier League", "La Liga", "Serie A", "Ligue 1"]
                        strong_buyers = [t for t in interested_buyers if t.league in international_league_groups_keys and t.budget > player_to_sell.market_value * 1.5]
                        
                        buyer = None
                        if strong_buyers and random.random() < 0.7: # 70% chance a strong buyer makes an offer
                            buyer = random.choice(strong_buyers)
                            offer_amount = int(player_to_sell.market_value * random.uniform(1.1, 1.5)) # Strong buyers offer more
                        elif interested_buyers: # Otherwise, a regular interested buyer
                            buyer = random.choice(interested_buyers)
                            offer_amount = int(player_to_sell.market_value * random.uniform(0.9, 1.2)) # Regular offer

                        if buyer:
                            console.print(f"\n[bold green]Offer received for {player_to_sell.name} from {buyer.name} for [yellow]€{offer_amount:,}[/yellow]![/bold green]")
                            confirm = console.input("[bold yellow]Accept offer? (yes/no): [/bold yellow]").lower()
                            if confirm == 'yes':
                                user_team.budget += offer_amount
                                buyer.budget -= offer_amount
                                user_team.remove_player(player_to_sell)
                                buyer.add_player(player_to_sell)
                                console.print(f"\n[bold green]SUCCESS! {player_to_sell.name} sold to {buyer.name} for €{offer_amount:,}![/bold green]")
                            else: console.print("[red]Offer declined.[/red]")
                        else:
                            console.print(f"\n[yellow]No suitable offers came in for {player_to_sell.name} at this time.[/yellow]")
                    else: console.print(f"\n[yellow]No offers came in for {player_to_sell.name} at this time.[/yellow]")
                else: console.print("[red]Invalid input.[/red]")
            except (ValueError, IndexError): console.print("[red]Invalid input.[/red]")
        elif choice == '4': run_youth_promotions(user_team)
        elif choice == '5': break
        else: console.print("[red]Invalid choice.[/red]")

    console.print("\n[bold blue]--- AI Transfer Activity ---[/bold blue]")
    # AI teams buying and selling among themselves
    indices_to_remove_from_transfer_list = []
    
    for buyer_team in other_teams:
        if buyer_team.budget < 1_000_000: continue
        random.shuffle(transfer_list) 

        for i, item in enumerate(transfer_list):
            if item in indices_to_remove_from_transfer_list: continue 
            player, seller_team = item['player'], item['seller']
            if buyer_team == seller_team: continue 

            potential_new_ovr = (sum(p.ovr for p in buyer_team.players) + player.ovr) / (len(buyer_team.players) + 1)
            is_improvement = potential_new_ovr > buyer_team.get_team_ovr() + 1
            can_afford = buyer_team.budget >= player.market_value
            has_space = len(buyer_team.players) < 30

            if is_improvement and can_afford and has_space and random.random() < 0.3: 
                buyer_team.budget -= player.market_value
                seller_team.budget += player.market_value
                seller_team.remove_player(player)
                buyer_team.add_player(player)
                # console.print(f"[TRANSFER] {player.name} ({seller_team.name} -> {buyer_team.name}) for €{player.market_value:,}!") # Suppressed
                indices_to_remove_from_transfer_list.append(item)
                break 
    
    transfer_list = [item for item in transfer_list if item not in indices_to_remove_from_transfer_list]

    if not indices_to_remove_from_transfer_list:
        console.print("[yellow]No major AI transfers in this window.[/yellow]")
    
    console.print(f"\n[bold blue]--- {window_name} Transfer Window is CLOSED ---[/bold blue]")


def serialize_manager_state(all_club_teams, user_team_name, season_count):
    return {
        "all_club_teams": [t.to_dict() for t in all_club_teams],
        "user_team_name": user_team_name,
        "season_count": season_count
    }

def deserialize_manager_state(data):
    all_teams_map = {}
    all_club_teams = []
    for t_data in data["all_club_teams"]:
        team = Team.from_dict(t_data)
        all_club_teams.append(team)
        all_teams_map[team.name] = team
    
    # Re-link players to teams
    for team_obj in all_club_teams:
        for player in team_obj.players:
            player.team = team_obj
        for youth_player in team_obj.youth_academy:
            youth_player.team = team_obj

    user_team = all_teams_map[data["user_team_name"]]
    season_count = data["season_count"]
    
    # Reconstruct league_teams and playoff_teams based on current user_team's league
    league_teams = [t for t in all_club_teams if t.league == user_team.league and t.league != "Domestic Playoff"]
    playoff_teams = [t for t in all_club_teams if t.league == "Domestic Playoff"]

    return all_club_teams, league_teams, playoff_teams, user_team, season_count






def handle_job_offers(user_team, all_club_teams, season_number, current_league_teams_sorted): # Added current_league_teams_sorted
    console.print("\n[bold blue]--- Evaluating Manager Job Offers ---[/bold blue]")
    offers = []
    
    international_league_groups_keys = ["Premier League", "La Liga", "Serie A", "Ligue 1"]
    
    # Conditions for receiving offers
    if user_team.stadium_level > 50 and user_team.academy_level > 50 and season_number > 3:
        # User success factor (e.g., top 3 in current league)
        user_team_position = -1
        for i, team in enumerate(current_league_teams_sorted):
            if team == user_team:
                user_team_position = i
                break
        
        success_factor = 0
        if user_team_position != -1 and user_team_position < 3: # Top 3
            success_factor = 1
        elif user_team_position != -1 and user_team_position < 8: # Top half
            success_factor = 0.5
        
        if success_factor > 0:
            # Filter for clubs in bigger leagues that might be interested
            eligible_clubs = []
            for club in all_club_teams:
                if club.league in international_league_groups_keys and club != user_team:
                    # Basic criteria: user's OVR is high, and the target club is "better" but not astronomically so
                    if user_team.get_team_ovr() >= club.get_team_ovr() - 10 and user_team.get_team_ovr() <= club.get_team_ovr() + 10: # Similar OVR
                        eligible_clubs.append(club)
                    elif user_team.get_team_ovr() >= 100 and club.get_team_ovr() > user_team.get_team_ovr(): # User is strong, target is stronger
                         eligible_clubs.append(club)
            
            if eligible_clubs:
                # Offer a few random offers
                random.shuffle(eligible_clubs)
                for _ in range(random.randint(1, min(3, len(eligible_clubs)))):
                    offer_club = eligible_clubs.pop(0)
                    offer_budget = int(offer_club.budget * random.uniform(0.8, 1.2))
                    offers.append({"club": offer_club, "budget": offer_budget})
    
    if offers:
        console.print(Panel("[bold green]*** Exciting News! You've received job offers! ***[/bold green]", title="[bold yellow]Job Offers[/bold yellow]", border_style="green"))
        for i, offer in enumerate(offers):
            console.print(f"[{i+1}] [cyan]{offer['club'].name}[/cyan] (League: [blue]{offer['club'].league}[/blue]) - Offered Budget: [yellow]€{offer['budget']:,}[/yellow]")
        
        choice = console.input("[bold yellow]Enter the number of the offer to accept, or 0 to decline all offers:[/bold yellow] ")
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(offers):
                accepted_offer = offers[choice_idx]
                new_user_team = accepted_offer['club']
                
                # Make the old user_team an AI team by assigning a default budget/settings
                # This ensures the old team doesn't just disappear or break game logic
                user_team.budget = int(user_team.budget * random.uniform(0.5, 0.8)) # Old team budget might drop
                user_team.stadium_level = max(1, user_team.stadium_level - random.randint(0, 5))
                user_team.academy_level = max(1, user_team.academy_level - random.randint(0, 5))
                
                new_user_team.budget = accepted_offer['budget'] # New budget from the offer
                
                console.print(f"\n[bold green]Congratulations! You have accepted the job at {new_user_team.name}![/bold green]")
                return new_user_team # Only return new user team, main will manage leagues
            else:
                console.print("[yellow]All offers declined. You remain at your current club.[/yellow]")
        except ValueError:
            console.print("[red]Invalid input. All offers declined. You remain at your current club.[/red]")
    else:
        console.print("[yellow]No job offers received this season.[/yellow]")
    
    return user_team # No change if no offers or declined

def run_season(all_club_teams, league_teams, playoff_teams, user_team, season_number): # Added all_club_teams
    console.print(f"\n[bold green]{ '='*20}SEASON {season_number} {'='*20}[/bold green]", style="bold blue")
    
    if season_number > 1:
        run_off_season_training(all_club_teams, user_team) # Pass user_team_ref
        restock_youth_academy(all_club_teams, user_team) # Pass user_team_ref
        run_youth_promotions(user_team)

    # Only reset stats for teams in the current league and playoffs
    for team in league_teams + playoff_teams:
        reset_all_team_stats([team])
        reset_player_season_stats([team])
    
    # Reset stats for all other teams that might be participating in cups later
    for team in all_club_teams:
        if team not in league_teams and team not in playoff_teams:
            reset_all_team_stats([team])
            reset_player_season_stats([team])


    main_league = League(league_teams)
    main_league.fixtures = generate_fixtures(list(main_league.teams.values())) 
    
    mid_season_matchday_index = len(main_league.fixtures) // 2

    # --- Start of Season Financials ---
    console.print("\n[bold blue]--- Start of Season Financials ---[/bold blue]")
    
    # All teams receive sponsorship
    for team in all_club_teams:
        # Only offer sponsorship if not user team or if user team explicitly accepts
        if team == user_team:
            sponsorship_offer = generate_sponsorship_offer(user_team.get_team_ovr())
            console.print(f"You received a sponsorship offer of [yellow]€{sponsorship_offer:,}[/yellow]!")
            choice = console.input("[bold yellow]Accept sponsorship? (yes/no):[/bold yellow] ").lower()
            if choice == 'yes':
                user_team.budget += sponsorship_offer
                console.print(f"[bold green]Sponsorship accepted! Your new budget is [yellow]€{user_team.budget:,}[/yellow].[/bold green]")
            else:
                console.print("[yellow]Sponsorship declined.[/yellow]")
        else: # AI teams automatically accept sponsorship
            ai_sponsorship_offer = generate_sponsorship_offer(team.get_team_ovr())
            team.budget += ai_sponsorship_offer
            # console.print(f"[AI Financials] {team.name} received €{ai_sponsorship_offer:,} from sponsorship.") # Suppressed


    # CUP DE GURU (Knockout, top 8 domestic teams)
    domestic_teams_sorted_by_ovr = sorted([t for t in all_club_teams if t.league == user_team.league and t.league != "Domestic Playoff"], key=lambda t: t.get_team_ovr(), reverse=True)
    cup_de_guru_participants = domestic_teams_sorted_by_ovr[:8]
    CUP_DE_GURU_PRIZES = {"winner": 10_000_000, "runner_up": 5_000_000, "semi_finalist": 2_000_000}

    # SILVER CUP (Home and away, 16 teams - 8 domestic, 8 random international)
    silver_cup_domestic_participants = random.sample([t for t in all_club_teams if t.league == user_team.league and t.league != "Domestic Playoff"], min(8, len(league_teams)))
    
    console.print("\n[bold blue]--- Preparing Silver Cup Participants ---[/bold blue]")
    international_league_groups_keys = ["Premier League", "La Liga", "Serie A", "Ligue 1"] # For filtering
    
    silver_cup_international_participants = []
    # Select from already created international club teams
    available_international_clubs = [t for t in all_club_teams if t.league in international_league_groups_keys]
    
    random.shuffle(available_international_clubs)
    silver_cup_international_participants = available_international_clubs[:8] # Take up to 8 unique international teams
    
    silver_cup_participants = silver_cup_domestic_participants + silver_cup_international_participants
    random.shuffle(silver_cup_participants) # Mix them up
    SILVER_CUP_PRIZES = {"winner": 15_000_000, "runner_up": 7_000_000}


    for i, matchday in enumerate(main_league.fixtures):
        console.print(f"\n[bold blue]--- Matchday {i + 1} - Weekly Wage Payment ---[/bold blue]")
        for team in league_teams + playoff_teams: 
            wage_deduction = team.total_wage_bill
            team.budget -= wage_deduction
            if team == user_team: # Only print weekly wages for user's team
                console.print(f"[green]{team.name}[/green] paid [red]€{wage_deduction:,}[/red] in wages. New budget: [yellow]€{team.budget:,}[/yellow]")
            
        run_management_menu(user_team)

        if i == mid_season_matchday_index:
            run_transfer_window(league_teams, user_team, "Mid-Season", all_club_teams) # Pass all_club_teams
        
        if i == len(main_league.fixtures) // 4: # Roughly quarter-season
            console.print(f"\n[bold green]{'='*50}\n{' '*15}CUP DE GURU Quarter-Finals!\n{'='*50}[/bold green]", style="bold blue")
            simulate_knockout_cup(cup_de_guru_participants, "Cup De Guru", CUP_DE_GURU_PRIZES, user_team)
            console.print(f"\n[bold green]{'='*50}\n{' '*15}CUP DE GURU Concluded!\n{'='*50}[/bold green]", style="bold blue")

        if i == len(main_league.fixtures) // 2 + len(main_league.fixtures) // 4: # Roughly three-quarter season
            console.print(f"\n[bold green]{'='*50}\n{' '*15}SILVER CUP Group Stage/First Rounds!\n{'='*50}[/bold green]", style="bold blue")
            simulate_home_away_cup(silver_cup_participants, "Silver Cup", SILVER_CUP_PRIZES, user_team)
            console.print(f"\n[bold green]{'='*50}\n{' '*15}SILVER CUP Concluded!\n{'='*50}[/bold green]", style="bold blue")


        console.print(f"\n[bold blue]--- Matchday {i + 1}/{len(main_league.fixtures)} ---[/bold blue]")
        user_match_found = False
        for home, away in matchday:
            if home == user_team or away == user_team:
                console.print(f"Your next match: [cyan]{home.name}[/cyan] vs [cyan]{away.name}[/cyan]")
                user_match_found = True
                break
        if not user_match_found:
            console.print("[yellow]Your team has no match this matchday.[/yellow]")
        
        console.input("\n[bold green]Press Enter to simulate the next matchday...[/bold green]")
        
        console.print(f"\n[bold blue]--- Matchday {i + 1} Results ---[/bold blue]")
        if not matchday:
            console.print("[yellow]No matches scheduled for this matchday.[/yellow]")
            continue
        for home, away in matchday:
            if home is None or away is None: 
                continue
            home_goals, away_goals = simulate_match(home, away, user_team_ref=user_team)
            if home == user_team or away == user_team: # Only print result if user's team is involved
                console.print(f"[cyan]{home.name}[/cyan] [bold red]{home_goals}[/bold red] - [bold red]{away_goals}[/bold red] [cyan]{away.name}[/cyan]")
            
        main_league.update_table()
        main_league.print_table()

    console.print("\n[bold green]--- SEASON OVER ---[/bold green]", style="bold blue")
    console.print("[bold blue]Final League Table:[/bold blue]")
    main_league.print_table()

    console.print("\n[bold blue]--- End of Season Financials ---[/bold blue]")
    prize_money = [
        50_000_000, 45_000_000, 40_000_000, 35_000_000, 30_000_000,
        25_000_000, 22_000_000, 20_000_000, 18_000_000, 16_000_000,
        14_000_000, 12_000_000, 10_000_000, 8_000_000
    ]
    for i, team in enumerate(main_league.table):
        if i < len(prize_money): 
            reward = prize_money[i]
            team.budget += reward
            if team == user_team: # Only print prize money for user's team
                console.print(f"[bold green][PRIZE MONEY][/bold green] [cyan]{team.name}[/cyan] awarded [yellow]€{reward:,}[/yellow] for finishing {i+1}.")

    # Merchandise Revenue - now for all teams
    for team in all_club_teams:
        # Use main_league.table for all teams to determine their relative position for merch calculation
        merch_revenue = calculate_merchandise_revenue(team, main_league.table)
        team.budget += merch_revenue
        if team == user_team: # Only print merchandise revenue for user's team
            console.print(f"[bold green][FINANCIALS][/bold green] [cyan]{team.name}[/cyan] generated [yellow]€{merch_revenue:,}[/yellow] from merchandise sales.")


    # Final Sacking Check (only at end of season)
    if user_team.budget < 0:
        console.print(f"\n[bold red]CRITICAL: Your budget is €{user_team.budget:,} even after prize money![/bold red]")
        console.print("[bold red]MANAGER SACKED! The board has decided to let you go.[/bold red]")
        return None, None, None, None # Return None for all if sacked
    
    # AI Team Bailout: Ensure AI teams don't go bankrupt and can still compete
    for team in all_club_teams:
        if team != user_team and team.budget < 0:
            team.budget = 200_000_000 # Bailout for AI teams in debt
            console.print(f"[bold yellow][AI BAILOUT][/bold yellow] [cyan]{team.name}[/cyan] was in debt and received a [green]€200,000,000 bailout![/green]")
    
    # International Competition Prize Structures
    CL_PRIZES = {"winner": 100_000_000, "runner_up": 50_000_000, "participation": 15_000_000}
    EL_PRIZES = {"winner": 40_000_000, "runner_up": 20_000_000, "participation": 8_000_000}
    COL_PRIZES = {"winner": 20_000_000, "runner_up": 10_000_000, "participation": 4_000_000}

    # Common pool of eligible teams for international tournaments
    eligible_club_teams_for_inter_tournaments = [t for t in all_club_teams if t.league != "Domestic Playoff"]
    all_club_teams_sorted_by_ovr = sorted(eligible_club_teams_for_inter_tournaments, key=lambda t: t.get_team_ovr(), reverse=True)

    international_league_groups_keys = ["Premier League", "La Liga", "Serie A", "Ligue 1"]
    
    if user_team.league in international_league_groups_keys:
        # User is in a major league, qualify based on their league table and top OVR teams globally
        current_user_league_teams = sorted([t for t in all_club_teams if t.league == user_team.league], key=lambda t: t.points, reverse=True)
        
        # Champions League - aim for 16 teams (4 groups of 4)
        cl_participants = []
        # Add top teams from user's league
        cl_participants.extend(current_user_league_teams[:4]) # Top 4 from user's major league
        
        # Fill with other top teams from all international leagues, ensuring uniqueness
        for team in all_club_teams_sorted_by_ovr:
            if len(cl_participants) >= 16: break
            if team.league in international_league_groups_keys and team not in cl_participants:
                cl_participants.append(team)
        
        if len(cl_participants) >= 16:
            console.print(f"\n[bold green]{'='*50}\n{' '*15}CHAMPIONS LEAGUE!\n{'='*50}[/bold green]", style="bold blue")
            cl_group_qualifiers = simulate_competition_group_stage(cl_participants, "Champions League", user_team)
            simulate_competition_knockout_stage(cl_group_qualifiers, "Champions League", CL_PRIZES, user_team)
        else:
            console.print(f"\n[bold yellow]Not enough teams ({len(cl_participants)}) for a full Champions League simulation. Falling back to simplified.[/bold yellow]")
            simulate_international_tournament(cl_participants, "Champions League", CL_PRIZES, user_team)

        # Europa League - aim for 16 teams
        el_participants = []
        # Add next teams from user's league
        el_participants.extend(current_user_league_teams[4:8]) # Next 4 from user's major league (e.g., 5th-8th place)

        # Fill with other top teams not in CL, ensuring uniqueness
        for team in all_club_teams_sorted_by_ovr:
            if len(el_participants) >= 16: break
            if team not in cl_participants and team not in el_participants and team.league in international_league_groups_keys:
                el_participants.append(team)
        
        if len(el_participants) >= 16:
            console.print(f"\n[bold green]{'='*50}\n{' '*15}EUROPA LEAGUE!\n{'='*50}[/bold green]", style="bold blue")
            el_group_qualifiers = simulate_competition_group_stage(el_participants, "Europa League", user_team)
            simulate_competition_knockout_stage(el_group_qualifiers, "Europa League", EL_PRIZES, user_team)
        else:
            console.print(f"\n[bold yellow]Not enough teams ({len(el_participants)}) for a full Europa League simulation. Falling back to simplified.[/bold yellow]")
            simulate_international_tournament(el_participants, "Europa League", EL_PRIZES, user_team)

        # Conference League - aim for 16 teams
        col_participants = []
        # Add next teams from user's league (e.g., 9th-12th place)
        col_participants.extend(current_user_league_teams[8:12])

        # Fill with other teams not in CL/EL, ensuring uniqueness
        for team in all_club_teams_sorted_by_ovr:
            if len(col_participants) >= 16: break
            if team not in cl_participants and team not in el_participants and team not in col_participants and team.league in international_league_groups_keys:
                col_participants.append(team)

        if len(col_participants) >= 16:
            console.print(f"\n[bold green]{'='*50}\n{' '*15}CONFERENCE LEAGUE!\n{'='*50}[/bold green]", style="bold blue")
            col_group_qualifiers = simulate_competition_group_stage(col_participants, "Conference League", user_team)
            simulate_competition_knockout_stage(col_group_qualifiers, "Conference League", COL_PRIZES, user_team)
        else:
            console.print(f"\n[bold yellow]Not enough teams ({len(col_participants)}) for a full Conference League simulation. Falling back to simplified.[/bold yellow]")
            simulate_international_tournament(col_participants, "Conference League", COL_PRIZES, user_team)

    else: # User is in Domestic League, use global OVR based qualification
        # Create a sorted list of domestic teams based on league table (current season performance)
        domestic_teams_sorted_by_points = sorted([t for t in all_club_teams if t.league == user_team.league and t.league != "Domestic Playoff"], key=lambda t: t.points, reverse=True)

        # Champions League - aim for 16 teams (4 groups of 4)
        cl_participants = []
        cl_participants.extend(domestic_teams_sorted_by_points[:2]) # Top 2 from domestic league

        # Fill with other top teams from all clubs, excluding domestic playoff teams and existing CL participants
        for team in all_club_teams_sorted_by_ovr:
            if len(cl_participants) >= 16: break
            if team not in cl_participants and team.league != "Domestic Playoff":
                cl_participants.append(team)
        
        if len(cl_participants) >= 16:
            console.print(f"\n[bold green]{'='*50}\n{' '*15}CHAMPIONS LEAGUE!\n{'='*50}[/bold green]", style="bold blue")
            cl_group_qualifiers = simulate_competition_group_stage(cl_participants, "Champions League", user_team)
            simulate_competition_knockout_stage(cl_group_qualifiers, "Champions League", CL_PRIZES, user_team)
        else:
            console.print(f"\n[bold yellow]Not enough teams ({len(cl_participants)}) for a full Champions League simulation. Falling back to simplified.[/bold yellow]")
            simulate_international_tournament(cl_participants, "Champions League", CL_PRIZES, user_team)

        # Europa League - aim for 16 teams
        el_participants = []
        el_participants.extend(domestic_teams_sorted_by_points[2:4]) # Next 2 from domestic league

        # Fill with other top teams not in CL, excluding domestic playoff teams and existing EL participants
        for team in all_club_teams_sorted_by_ovr:
            if len(el_participants) >= 16: break
            if team not in cl_participants and team not in el_participants and team.league != "Domestic Playoff":
                el_participants.append(team)

        if len(el_participants) >= 16:
            console.print(f"\n[bold green]{'='*50}\n{' '*15}EUROPA LEAGUE!\n{'='*50}[/bold green]", style="bold blue")
            el_group_qualifiers = simulate_competition_group_stage(el_participants, "Europa League", user_team)
            simulate_competition_knockout_stage(el_group_qualifiers, "Europa League", EL_PRIZES, user_team)
        else:
            console.print(f"\n[bold yellow]Not enough teams ({len(el_participants)}) for a full Europa League simulation. Falling back to simplified.[/bold yellow]")
            simulate_international_tournament(el_participants, "Europa League", EL_PRIZES, user_team)

        # Conference League - aim for 16 teams
        col_participants = []
        col_participants.extend(domestic_teams_sorted_by_points[4:6]) # Next 2 from domestic league

        # Fill with other teams not in CL/EL, excluding domestic playoff teams and existing COL participants
        for team in all_club_teams_sorted_by_ovr:
            if len(col_participants) >= 16: break
            if team not in cl_participants and team not in el_participants and team not in col_participants and team.league != "Domestic Playoff":
                col_participants.append(team)

        if len(col_participants) >= 16:
            console.print(f"\n[bold green]{'='*50}\n{' '*15}CONFERENCE LEAGUE!\n{'='*50}[/bold green]", style="bold blue")
            col_group_qualifiers = simulate_competition_group_stage(col_participants, "Conference League", user_team)
            simulate_competition_knockout_stage(col_group_qualifiers, "Conference League", COL_PRIZES, user_team)
        else:
            console.print(f"\n[bold yellow]Not enough teams ({len(col_participants)}) for a full Conference League simulation. Falling back to simplified.[/bold yellow]")
            simulate_international_tournament(col_participants, "Conference League", COL_PRIZES, user_team)


    # World Cup integration
    if season_number % 4 == 0: 
        simulate_world_cup(all_club_teams, user_team) # Pass all_club_teams here

    present_season_awards(all_club_teams, user_team) # Awards based on current league table

    # Determine promoted/relegated teams from the domestic league
    # This logic only applies to the "Domestic League" and "Domestic Playoff"
    # Need to correctly identify the current domestic league teams for relegation/promotion logic
    
    # If the user is in a "Domestic League"
    if user_team.league == "Domestic League":
        # Ensure main_league.table is updated before getting relegated teams
        main_league.update_table() 
        relegated_teams_from_user_league = main_league.table[-2:] # Assuming last 2 are relegated
        domestic_playoff_teams_current = [t for t in all_club_teams if t.league == "Domestic Playoff"]
        
        promoted_to_user_league, demoted_from_user_league_playoffs = run_playoffs(relegated_teams_from_user_league, domestic_playoff_teams_current, user_team)
        
        # Update leagues for affected teams in all_club_teams
        for team in relegated_teams_from_user_league:
            team.league = "Domestic Playoff" # Relegated teams go to playoff league
        for team in promoted_to_user_league:
            team.league = "Domestic League" # Promoted teams come to domestic league
        for team in demoted_from_user_league_playoffs:
            team.league = "Domestic Playoff" # Teams that stayed in playoff league
            
    run_transfer_window(league_teams, user_team, "End of Season", all_club_teams) # Pass all_club_teams

    # Manager Job Offers (after transfer window to account for new squad/budget)
    new_user_team = handle_job_offers(user_team, all_club_teams, season_number, main_league.table) # Pass sorted current league table

    # If user changed teams, update the league_teams and playoff_teams accordingly
    if new_user_team != user_team:
        user_team = new_user_team
        # Reconstruct league_teams and playoff_teams based on the new user_team's league
        league_teams = [t for t in all_club_teams if t.league == user_team.league and t.league != "Domestic Playoff"]
        # Playoff teams: if user moves to a non-domestic league, this list might be empty or still refer to domestic playoffs
        # For simplicity, we'll keep domestic playoff teams as the only ones for now.
        if user_team.league == "Domestic League":
            playoff_teams = [t for t in all_club_teams if t.league == "Domestic Playoff"]
        else:
            playoff_teams = [] # International leagues typically don't have this playoff structure in this game
        
        console.print(f"\n[bold green]--- NEW LEAGUE: {user_team.league} ---[/bold green]")

    else: # If user didn't change teams, update league/playoff teams based on current league changes
        league_teams = [t for t in all_club_teams if t.league == user_team.league and t.league != "Domestic Playoff"]
        if user_team.league == "Domestic League":
            playoff_teams = [t for t in all_club_teams if t.league == "Domestic Playoff"]
        else:
            playoff_teams = [] # International leagues typically don't have this playoff structure in this game


    return all_club_teams, league_teams, playoff_teams, user_team 

def main():
    console.print(Panel("[bold green]Welcome to Terminal Football Manager![/bold green]", title="[bold yellow]FOOTBALL MANAGER[/bold yellow]", style="bold blue"))
    
    all_club_teams = []
    league_teams, playoff_teams, user_team, season_count = None, None, None, 1
    
    while True:
        console.print("\n[bold blue]--- Main Menu ---[/bold blue]")
        console.print("1. Start New Game (Manager Mode)")
        console.print("2. Load Game (Manager Mode)")
        console.print("3. Start Player Career Mode")
        console.print("4. FUT Mode")
        console.print("5. Exit")
        main_choice = console.input("[bold yellow]Enter your choice:[/bold yellow] ")

        if main_choice == '1':
            all_club_teams = create_teams() # Get all teams generated
            
            domestic_teams_for_selection = [t for t in all_club_teams if t.league == "Domestic League"]
            console.print("\n[bold blue]To begin your managerial career, please select a team:[/bold blue]")
            sorted_teams = sorted(domestic_teams_for_selection, key=lambda t: t.name)
            for i, team in enumerate(sorted_teams):
                console.print(f"[{i + 1}] [cyan]{team.name}[/cyan] (Avg. OVR: [green]{team.get_team_ovr():.2f}[/green]) - Budget: [yellow]€{team.budget:,}[/yellow], Squad Value: [yellow]€{team.total_squad_value:,}[/yellow], Weekly Wage: [red]€{team.total_wage_bill:,}[/red])")
            
            while not user_team:
                try:
                    choice = int(console.input("[bold yellow]Enter the number of your team:[/bold yellow] "))
                    if 1 <= choice <= len(sorted_teams):
                        user_team = sorted_teams[choice - 1]
                        console.print(f"\n[bold green]You have chosen to manage {user_team.name}.[/bold green]\n")
                    else:
                        console.print("[red]Invalid number. Please try again.[/red]")
                except ValueError:
                    console.print("[red]Invalid input. Please enter a number.[/red]")
            
            # Initialize league_teams and playoff_teams based on user's selected domestic league
            league_teams = [t for t in all_club_teams if t.league == user_team.league and t.league != "Domestic Playoff"]
            playoff_teams = [t for t in all_club_teams if t.league == "Domestic Playoff"] # Domestic playoff teams
            break

        elif main_choice == '2':
            mode, loaded_state = load_game()
            if loaded_state:
                if mode == "Manager Mode":
                    all_club_teams, league_teams, playoff_teams, user_team, season_count = deserialize_manager_state(loaded_state)
                    break
                elif mode == "Player Career":
                    hero_player = HeroPlayer.from_dict(loaded_state)
                    run_player_career_mode(hero_player)
                    all_club_teams, league_teams, playoff_teams, user_team, season_count = [], [], [], None, 1
                    continue
                elif mode == "FUT":
                    fut_club = FutClub.from_dict(loaded_state)
                    run_fut_mode(fut_club)
                    all_club_teams, league_teams, playoff_teams, user_team, season_count = [], [], [], None, 1
                    continue
            else:
                console.print("[yellow]No save file found or incompatible format.[/yellow]")
                continue 
        elif main_choice == '3':
            run_player_career_mode()
            all_club_teams, league_teams, playoff_teams, user_team, season_count = [], [], [], None, 1 # Reset state
            continue # Loop back to main menu
        elif main_choice == '4':
            # FUT Mode
            run_fut_mode() # Call FUT mode independently
            continue # Return to main menu after FUT mode
        elif main_choice == '5':
            console.print("[bold red]Exiting game. Goodbye![/bold red]")
            return
        else:
            console.print("[red]Invalid choice.[/red]")

    # Main season loop for Manager Mode
    while True:
        if user_team is None: 
            console.print(Panel("[bold red]--- CAREER ENDED ---[/bold red]\nYou were sacked. You can start a new game or load a previous save.", title="[bold yellow]GAME OVER[/bold yellow]", border_style="red"))
            main() 
            return # Exit this instance of main() as a new one is started

        all_club_teams, league_teams, playoff_teams, current_user_team = run_season(all_club_teams, league_teams, playoff_teams, user_team, season_count) # Pass all_club_teams
        
        if current_user_team is None: # Manager was sacked during the season
            user_team = None # Signal that manager is sacked
            continue # Loop will restart main menu for new career/load

        user_team = current_user_team # Update user_team reference

        save_choice = console.input("\n[bold yellow]Do you want to save your game? (yes/no):[/bold yellow] ").lower()
        if save_choice == 'yes':
            game_state_to_save = serialize_manager_state(all_club_teams, user_team.name, season_count)
            save_game("Manager Mode", game_state_to_save)

        while True:
            another_season = console.input("\n[bold yellow]Play another season? (yes/no):[/bold yellow] ").lower()
            if another_season in ["yes", "no"]:
                break
            console.print("[red]Invalid input. Please enter 'yes' or 'no'.[/red]")
        
        if another_season == "no":
            console.print("[bold red]Thanks for playing![/bold red]")
            break
            
        season_count += 1

if __name__ == "__main__":
    main()
