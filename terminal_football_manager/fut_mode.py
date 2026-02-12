from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import random

from .fut_data import AGENT_TIERS, PLAYER_PACKS, STADIUM_NAMES, FUTPlayer, get_players_by_card_type, get_players_by_ovr_range, CHAMPIONS_LEAGUE_TEAMS_DATA, CHAMPIONS_LEAGUE_REWARDS, BIG_CLUBS_FUT_START, FUT_PLAYERS_DATA
from .models import Player, Team
from .constants import ATTRIBUTE_WEIGHTS, POSITIONS, FIRST_NAMES, LAST_NAMES, NATIONAL_FIRST_NAMES, NATIONAL_LAST_NAMES, COUNTRIES # Added name lists for player generation
from .game_logic import League, generate_fixtures, assign_goal_scorers, simulate_match, reset_all_team_stats, reset_player_season_stats # New imports from game_logic


console = Console()

from .persistence import save_game, load_game

class FutClub:
    def __init__(self, name, budget):
        self.name = name
        self.budget = budget
        self.players = []
        self.stadiums = []

    def to_dict(self):
        return {
            "name": self.name,
            "budget": self.budget,
            "players": [p.to_dict() for p in self.players],
            "stadiums": self.stadiums
        }

    @classmethod
    def from_dict(cls, data):
        club = cls(data["name"], data["budget"])
        club.stadiums = data.get("stadiums", [])
        for p_data in data["players"]:
            club.players.append(Player.from_dict(p_data))
        return club

    def add_player(self, player):
        self.players.append(player)
        # When a player is added to FutClub, ensure their 'team' attribute points back to this FutClub
        player.team = self 

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
            player.team = None
            return True
        return False

    def can_afford(self, cost):
        return self.budget >= cost

    def deduct_budget(self, amount):
        self.budget -= amount
    
    def add_budget(self, amount):
        self.budget += amount

    def add_stadium(self, stadium_name):
        self.stadiums.append(stadium_name)

    def get_team_ovr(self):
        if not self.players:
            return 0
        sorted_players = sorted(self.players, key=lambda p: p.ovr, reverse=True)
        # Consider top 11 for OVR calculation, similar to main game logic
        top_11_ovr = [p.ovr for p in sorted_players[:11]]
        return sum(top_11_ovr) / len(top_11_ovr) if top_11_ovr else 0

    def get_starting_goalkeeper(self):
        goalkeepers = [p for p in self.players if p.position == 'GK']
        if not goalkeepers:
            return None
        return max(goalkeepers, key=lambda p: p.ovr)

    def __repr__(self):
        return f"FutClub(Name: {self.name}, Budget: €{self.budget:,}, Players: {len(self.players)}, Stadiums: {len(self.stadiums)})"


def _generate_player_from_fut_data(fut_player_data, target_ovr=None):
    """
    Generates a Player object from FUTPlayer namedtuple data.
    Allows specifying a target OVR for more precise generation.
    """
    # Use base_ovr as a strong guideline, but allow slight variance
    ovr = fut_player_data.base_ovr
    if target_ovr:
        # Adjust OVR slightly towards target, but respect original base_ovr
        ovr = random.randint(max(40, target_ovr - 5), min(190, target_ovr + 5))
        
    # Generate attributes based on position and ATTRIBUTE_WEIGHTS from constants.py
    player_attributes = {}
    
    # Ensure the position is valid and has defined attribute weights
    if fut_player_data.position in ATTRIBUTE_WEIGHTS:
        for attr, weight_multiplier in ATTRIBUTE_WEIGHTS[fut_player_data.position].items():
            # Base attribute value influenced by OVR and a random factor
            base_attr_value = int(ovr * (1 + (random.random() - 0.5) * 0.3))
            # Further adjust by position weight
            player_attributes[attr] = int(base_attr_value * (1 + weight_multiplier))
            # Cap attributes to avoid extreme values and ensure a minimum
            player_attributes[attr] = max(10, min(player_attributes[attr], 150)) # Cap at 150 for realism
    else:
        # Fallback for positions not explicitly in ATTRIBUTE_WEIGHTS (e.g., new FUT specific positions)
        # Assign generic attributes
        for attr in ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"]:
            player_attributes[attr] = random.randint(ovr - 20, ovr + 10)
            player_attributes[attr] = max(10, min(player_attributes[attr], 150))
            

    return Player(
        name=fut_player_data.name,
        position=fut_player_data.position,
        age=fut_player_data.age,
        ovr=ovr,
        attributes=player_attributes, # Pass the generated attributes
        country=fut_player_data.country
    )


def scout_player_with_agent(fut_club, agent_tier):
    console.print(f"\n[bold blue]--- Scouting with {agent_tier.name} ---[/bold blue]")
    if not fut_club.can_afford(agent_tier.cost):
        console.print(f"[bold red]Not enough budget to hire the {agent_tier.name}. You need €{agent_tier.cost:,}.[/bold red]")
        return

    fut_club.deduct_budget(agent_tier.cost)
    console.print(f"[green]Hired {agent_tier.name} for €{agent_tier.cost:,}. Remaining budget: €{fut_club.budget:,}.[/green]")

    scouted_player_data = None
    
    # Check for pack chances
    pack_roll = random.randint(1, 100)
    current_chance_sum = 0
    
    for pack_name, chance in agent_tier.pack_chances.items():
        current_chance_sum += chance
        if pack_roll <= current_chance_sum:
            # Player from a specific pack card type
            eligible_players = get_players_by_card_type(pack_name)
            if eligible_players:
                scouted_player_data = random.choice(eligible_players)
                console.print(f"[bold green]The {agent_tier.name} found a special player from the {pack_name}![/bold green]")
                break
    
    if not scouted_player_data:
        # No special pack player, scout based on OVR range
        eligible_players = get_players_by_ovr_range(agent_tier.min_ovr, agent_tier.max_ovr)
        if eligible_players:
            scouted_player_data = random.choice(eligible_players)
        else:
            # Fallback if no players in range (shouldn't happen with diverse data)
            scouted_player_data = random.choice([p for p in FUT_PLAYERS_DATA if agent_tier.min_ovr <= p.base_ovr <= agent_tier.max_ovr])

    if scouted_player_data:
        # Generate the actual Player object with a potential slight OVR variance
        player = _generate_player_from_fut_data(scouted_player_data, target_ovr=random.randint(agent_tier.min_ovr, agent_tier.max_ovr))
        fut_club.add_player(player)
        console.print(Panel(f"[bold cyan]Scouted Player:[/bold cyan] {player.name} ([green]{player.ovr}[/green] OVR, {player.position}, {player.country})", title="[bold yellow]New Signing![/bold yellow]", border_style="green"))
    else:
        console.print("[red]The agent couldn't find any suitable players this time.[/red]")


def open_player_pack(fut_club, pack):
    console.print(f"\n[bold blue]--- Opening {pack.name} ---[/bold blue]")
    if not fut_club.can_afford(pack.price):
        console.print(f"[bold red]Not enough budget to buy the {pack.name}. You need €{pack.price:,}.[/bold red]")
        return

    fut_club.deduct_budget(pack.price)
    console.print(f"[green]Bought {pack.name} for €{pack.price:,}. Remaining budget: €{fut_club.budget:,}.[/green]")

    reward_found = False

    # Check for Stadium reward
    if random.randint(1, 100) <= pack.stadium_chance:
        stadium = random.choice(STADIUM_NAMES)
        fut_club.add_stadium(stadium)
        console.print(Panel(f"[bold yellow]Congratulations![/bold yellow] You've found the [bold green]{stadium}[/bold green]!", title="[bold blue]Rare Stadium![/bold blue]", border_style="yellow"))
        reward_found = True

    # Get player from pack
    player_data_pool = []
    for card_type in pack.player_pools:
        player_data_pool.extend(get_players_by_card_type(card_type))
    
    # If specific card types are not enough, fall back to OVR range
    if not player_data_pool:
        player_data_pool = get_players_by_ovr_range(pack.guaranteed_ovr_range[0], pack.guaranteed_ovr_range[1])

    if player_data_pool:
        chosen_fut_player = random.choice(player_data_pool)
        
        # Determine actual OVR, potentially within a tighter range if pack is very specific
        target_ovr = random.randint(pack.guaranteed_ovr_range[0], pack.guaranteed_ovr_range[1])
        player = _generate_player_from_fut_data(chosen_fut_player, target_ovr)
        
        fut_club.add_player(player)
        console.print(Panel(f"[bold cyan]You received:[/bold cyan] {player.name} ([green]{player.ovr}[/green] OVR, {player.position}, {player.country}) - [yellow]{chosen_fut_player.card_type}[/yellow]", title="[bold green]New Player![/bold green]", border_style="green"))
        reward_found = True
    
    if not reward_found:
        console.print("[red]Unlucky! No significant rewards this time.[/red]")


def display_fut_squad(fut_club):
    console.print(f"\n[bold blue]--- {fut_club.name} Squad ---[/bold blue]")
    if not fut_club.players:
        console.print("[yellow]Your FUT squad is empty.[/yellow]")
        return

    squad_table = Table(title="[bold green]Your FUT Players[/bold green]", show_header=True, header_style="bold magenta")
    squad_table.add_column("No.", style="dim")
    squad_table.add_column("Name", style="cyan")
    squad_table.add_column("OVR", justify="right", style="green")
    squad_table.add_column("Position")
    squad_table.add_column("Age")
    squad_table.add_column("Country")
    squad_table.add_column("Card Type", style="yellow") # Display card type from FUTPlayer data

    sorted_players = sorted(fut_club.players, key=lambda p: p.ovr, reverse=True)
    for i, player in enumerate(sorted_players):
        # We need to map the Player object back to its FUTPlayer data to get card_type
        # This is a simplification; in a real game, Player objects would have card_type directly
        original_fut_player = next((fp for fp in FUT_PLAYERS_DATA if fp.name == player.name), None)
        card_type_display = original_fut_player.card_type if original_fut_player else "N/A"

        squad_table.add_row(
            str(i+1),
            player.name,
            str(player.ovr),
            player.position,
            str(player.age),
            player.country,
            card_type_display
        )
    console.print(squad_table)

def display_fut_stadiums(fut_club):
    console.print(f"\n[bold blue]--- {fut_club.name} Stadiums ---[/bold blue]")
    if not fut_club.stadiums:
        console.print("[yellow]You don't own any stadiums yet.[/yellow]")
        return
    for i, stadium in enumerate(fut_club.stadiums):
        console.print(f"[{i+1}] [cyan]{stadium}[/cyan]")

def run_champions_league_challenge(fut_club):
    console.print(Panel("[bold yellow]Welcome to the Champions League Challenge![/bold yellow]", title="[bold blue]UEFA Champions League[/bold blue]", border_style="blue"))
    
    if not fut_club.players or fut_club.get_team_ovr() == 0:
        console.print("[bold red]You need players in your FUT squad to participate in the Champions League Challenge![/bold red]")
        console.input("\n[bold green]Press Enter to return to FUT Mode...[/bold green]")
        return
    
    # Create opponent teams from CHAMPIONS_LEAGUE_TEAMS_DATA
    opponent_teams = []
    for team_data in CHAMPIONS_LEAGUE_TEAMS_DATA:
        team_obj = Team(team_data["name"])
        for fut_player_data in team_data["players"]:
            player = _generate_player_from_fut_data(fut_player_data, target_ovr=fut_player_data.base_ovr)
            team_obj.add_player(player)
        opponent_teams.append(team_obj)
    
    random.shuffle(opponent_teams)
    
    # Create a Team object for the user's FUT club for simulation purposes
    user_fut_team_for_sim = Team(fut_club.name)
    user_fut_team_for_sim.players = fut_club.players # Link the players
    # Ensure players know their temporary "team" for the sim
    for p in user_fut_team_for_sim.players:
        p.team = user_fut_team_for_sim
    
    all_participants = [user_fut_team_for_sim] + opponent_teams[:15] # User + 15 strong teams for 4 groups of 4
    
    # Shuffle and divide into 4 groups of 4
    random.shuffle(all_participants)
    groups = [all_participants[i:i + 4] for i in range(0, len(all_participants), 4)]

    # --- Group Stage ---
    console.print("\n[bold yellow]--- Group Stage ---[/bold yellow]")
    user_qualified_from_group = False
    knockout_qualifiers = []

    for i, group_teams_sim in enumerate(groups):
        group_name = chr(65 + i) # A, B, C...
        console.print(f"\n[bold blue]--- Group {group_name} ---[/bold blue]")
        
        # Reset stats for group stage (copies are already made in simulate_competition_group_stage, but ensure for clarity)
        for t in group_teams_sim:
            t.points = 0; t.games_played = 0; t.wins = 0; t.draws = 0; t.losses = 0; t.goals_for = 0; t.goals_against = 0
            for p in t.players:
                p.season_goals = 0; p.season_clean_sheets = 0

        group_league = League(group_teams_sim)
        group_fixtures = []
        for home_team in group_teams_sim:
            for away_team in group_teams_sim:
                if home_team != away_team:
                    group_fixtures.append((home_team, away_team)) # Home and away matches

        random.shuffle(group_fixtures) # Shuffle fixtures for randomness
        
        for match_num, (home, away) in enumerate(group_fixtures):
            # Only prompt if user's team is involved in the current group and match
            if user_fut_team_for_sim in group_teams_sim:
                if home == user_fut_team_for_sim or away == user_fut_team_for_sim:
                    console.input(f"\n[bold green]Press Enter to simulate Group {group_name} Match: {home.name} vs {away.name}...[/bold green]")
            
            home_goals, away_goals = 0, 0
            # Ensure proper OVR calculation for FUT players within the Team object
            # Simulate match using the Team objects
            home_goals, away_goals = simulate_match(home, away, is_international_match=True, user_team_ref=user_fut_team_for_sim)
            
            console.print(f"[cyan]{home.name}[/cyan] [bold red]{home_goals}[/bold red] - [bold red]{away_goals}[/bold red] [cyan]{away.name}[/cyan]")
            
            # Manually update points as League object expects it
            home.games_played += 1
            away.games_played += 1
            home.goals_for += home_goals
            away.goals_for += away_goals
            home.goals_against += away_goals
            away.goals_against += home_goals

            if home_goals > away_goals:
                home.wins += 1; home.points += 3
                away.losses += 1
            elif away_goals > home_goals:
                away.wins += 1; away.points += 3
                home.losses += 1
            else:
                home.draws += 1; home.points += 1
                away.draws += 1; away.points += 1
        
        group_league.update_table()
        group_league.print_table()
        
        qualifiers_from_group = group_league.table[:2]
        knockout_qualifiers.extend(qualifiers_from_group)

        if user_fut_team_for_sim in qualifiers_from_group:
            user_qualified_from_group = True
            
    if user_qualified_from_group:
        reward = CHAMPIONS_LEAGUE_REWARDS["Group Stage"]
        fut_club.add_budget(reward["coins"])
        pack_type = PLAYER_PACKS[reward["pack"]]
        open_player_pack(fut_club, pack_type) # Directly give pack without cost
        console.print(f"[bold green]Congratulations! You qualified from the Group Stage![/bold green] You received [yellow]€{reward['coins']:,}[/yellow] and a [cyan]{reward['pack']}[/cyan].")
    else:
        console.print("[bold red]Unfortunately, your team did not qualify from the Group Stage.[/bold red]")
        console.input("\n[bold green]Press Enter to return to FUT Mode...[/bold green]")
        return
    
    # --- Knockout Stage ---
    console.print("\n[bold yellow]--- Knockout Stage ---[/bold yellow]")
    current_round_teams = list(knockout_qualifiers)
    random.shuffle(current_round_teams) # Shuffle for knockout draw

    round_names = ["Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]
    round_rewards_keys = ["Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]
    
    user_team_still_in_competition = True

    for r_idx, round_name in enumerate(round_names):
        if not user_team_still_in_competition or len(current_round_teams) < 2:
            break

        console.print(f"\n[bold blue]--- {round_name} ---[/bold blue]")
        next_round_teams = []
        
        if len(current_round_teams) % 2 != 0:
            # Should not happen if we started with 16, but as a safeguard
            console.print("[bold yellow]Warning: Odd number of teams. One team gets a bye.[/bold yellow]")
            next_round_teams.append(current_round_teams.pop(random.randrange(len(current_round_teams))))

        matches_this_round = []
        for i in range(0, len(current_round_teams), 2):
            matches_this_round.append((current_round_teams[i], current_round_teams[i+1]))

        for team1, team2 in matches_this_round:
            # Check if user's team is involved
            is_user_match = (team1 == user_fut_team_for_sim or team2 == user_fut_team_for_sim)
            if is_user_match:
                console.input(f"\n[bold green]Press Enter to simulate {round_name} match: {team1.name} vs {team2.name}...[/bold green]")

            home_goals, away_goals = simulate_match(team1, team2, is_international_match=True, user_team_ref=user_fut_team_for_sim)
            console.print(f"[cyan]{team1.name}[/cyan] [bold red]{home_goals}[/bold red] - [bold red]{away_goals}[/bold red] [cyan]{team2.name}[/cyan]")

            winner_team = None
            loser_team = None

            if home_goals > away_goals:
                winner_team = team1
                loser_team = team2
            elif away_goals > home_goals:
                winner_team = team2
                loser_team = team1
            else: # Draw, penalties
                console.print("[bold yellow]Match ends in a draw, going to penalties...[/bold yellow]")
                if random.random() > 0.5:
                    winner_team = team1
                    loser_team = team2
                    console.print(f"[bold green]{team1.name} wins after penalties![/bold green]")
                else:
                    winner_team = team2
                    loser_team = team1
                    console.print(f"[bold green]{team2.name} wins after penalties![/bold green]")
            
            next_round_teams.append(winner_team)

            if loser_team == user_fut_team_for_sim:
                user_team_still_in_competition = False
                console.print(f"[bold red]Your team was eliminated in the {round_name}.[/bold red]")
                break # Exit current match loop, user is out

        current_round_teams = next_round_teams
        
        if user_team_still_in_competition and r_idx < len(round_rewards_keys):
            reward_key = round_rewards_keys[r_idx]
            reward = CHAMPIONS_LEAGUE_REWARDS[reward_key]
            fut_club.add_budget(reward["coins"])
            pack_type = PLAYER_PACKS[reward["pack"]]
            open_player_pack(fut_club, pack_type)
            console.print(f"[bold green]Your team advanced to the next round![/bold green] You received [yellow]€{reward['coins']:,}[/yellow] and a [cyan]{reward['pack']}[/cyan].")
        
        if not user_team_still_in_competition:
            break
            
    # --- Final Result ---
    if user_team_still_in_competition and len(current_round_teams) == 1:
        winner = current_round_teams[0]
        console.print(f"\n[bold magenta]*** CHAMPIONS LEAGUE WINNER: {winner.name.upper()} ***[/bold magenta]")
        
        if winner == user_fut_team_for_sim:
            reward = CHAMPIONS_LEAGUE_REWARDS["Winner"]
            fut_club.add_budget(reward["coins"])
            pack_type = PLAYER_PACKS[reward["pack"]]
            open_player_pack(fut_club, pack_type)
            console.print(Panel(f"[bold green]UNBELIEVABLE! Your FUT Club has won the Champions League Challenge![/bold green]\n"
                                f"You received [yellow]€{reward['coins']:,}[/yellow] and a [cyan]{reward['pack']}[/cyan]!",
                                title="[bold yellow]CHAMPIONS![/bold yellow]", border_style="yellow"))
        else:
            console.print(f"[bold red]Your team reached the Final but lost to {winner.name}.[/bold red]")
            reward = CHAMPIONS_LEAGUE_REWARDS["Final"] # Finalist reward
            fut_club.add_budget(reward["coins"])
            pack_type = PLAYER_PACKS[reward["pack"]]
            open_player_pack(fut_club, pack_type)
            console.print(f"[bold green]You received [yellow]€{reward['coins']:,}[/yellow] and a [cyan]{reward['pack']}[/cyan] for being a finalist.[/bold green]")
    elif user_team_still_in_competition:
        console.print("[bold red]The Champions League Challenge ended unexpectedly without a clear winner.[/bold red]")


    console.input("\n[bold green]Press Enter to return to FUT Mode...[/bold green]")


def run_fut_mode(fut_club=None):
    console.print(Panel("[bold magenta]Welcome to FUT Central![/bold magenta]",
                        title="[bold yellow]FUT MODE[/bold yellow]", border_style="blue"))

    if fut_club is None:
        # Home Team Selection
        chosen_club_name = None
        while chosen_club_name is None:
            console.print("\n[bold blue]--- Choose Your Home Club for FUT ---[/bold blue]")
            for i, club_name in enumerate(BIG_CLUBS_FUT_START):
                console.print(f"[{i+1}] [cyan]{club_name}[/cyan]")
            
            choice = console.input("[bold yellow]Enter the number of your chosen club:[/bold yellow] ")
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(BIG_CLUBS_FUT_START):
                    chosen_club_name = BIG_CLUBS_FUT_START[choice_idx]
                else:
                    console.print("[red]Invalid choice. Please select a number from the list.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a number.[/red]")

        fut_club = FutClub(chosen_club_name + " FUT", 50_000_000) # Starting budget for FUT

        # Populate initial squad with players from chosen club, with low OVRs
        players_for_initial_squad = [p for p in CHAMPIONS_LEAGUE_TEAMS_DATA if p["name"] == chosen_club_name]
        if players_for_initial_squad:
            for fut_player_data_entry in players_for_initial_squad[0]["players"]:
                # Generate player with OVR between 70-90
                target_ovr = random.randint(70, 90)
                # Make a copy of the fut_player_data_entry and modify its base_ovr for generation
                temp_fut_player_data = FUTPlayer(
                    name=fut_player_data_entry.name,
                    position=fut_player_data_entry.position,
                    age=random.randint(20,28), # Adjust age for initial squad
                    base_ovr=target_ovr,
                    country=fut_player_data_entry.country,
                    card_type="Common" # Initial cards are common
                )
                player = _generate_player_from_fut_data(temp_fut_player_data, target_ovr=target_ovr)
                fut_club.add_player(player)
            console.print(Panel(f"[bold green]Your initial FUT squad for {chosen_club_name} FUT has been generated![/bold green]", title="[bold yellow]Squad Ready![/bold yellow]", border_style="green"))
        else:
            console.print("[red]Could not find player data for the chosen club. Your squad may be empty.[/red]")

        # Simplified Formation Selection (Placeholder for now)
        console.print("\n[bold blue]--- Choose Your Formation ---[/bold blue]")
        console.print("1. 4-3-3 Attacking")
        console.print("2. 4-4-2 Flat")
        console.print("3. 3-5-2")
        formation_choice = console.input("[bold yellow]Enter your preferred formation (e.g., 1):[/bold yellow] ")
        # For now, just acknowledge the choice. Actual formation logic can be added later.
        console.print(f"You have chosen formation: {formation_choice}. This will be implemented in future updates.")
    else:
        console.print(f"[bold green]Welcome back to {fut_club.name}![/bold green]")


    while True:
        console.print("\n[bold blue]--- FUT Mode Menu ---[/bold blue]")
        console.print(f"Current FUT Budget: [green]€{fut_club.budget:,}[/green]")
        console.print("1. Scout Players (Agent Recruiter)")
        console.print("2. Open Player Packs")
        console.print("3. View My Squad")
        console.print("4. View My Stadiums")
        console.print("5. Champions League Challenge")
        console.print("6. Save FUT Club")
        console.print("7. Exit FUT Mode")
        
        choice = console.input("[bold yellow]Enter your choice:[/bold yellow] ")

        if choice == '1': # Scout Players
            while True:
                console.print("\n[bold blue]--- Agent Recruiter ---[/bold blue]")
                console.print(f"Your FUT Budget: [green]€{fut_club.budget:,}[/green]")
                
                agent_tier_list = list(AGENT_TIERS.items())
                for i, (name, agent) in enumerate(agent_tier_list):
                    console.print(f"[{i+1}] {agent.name} - Cost: [red]€{agent.cost:,}[/red] (Scouts OVR {agent.min_ovr}-{agent.max_ovr})")
                
                agent_choice = console.input("[bold yellow]Select an agent (or 0 to go back):[/bold yellow] ")
                if agent_choice == '0': break
                
                try:
                    agent_idx = int(agent_choice) - 1
                    if 0 <= agent_idx < len(agent_tier_list):
                        selected_agent = agent_tier_list[agent_idx][1]
                        scout_player_with_agent(fut_club, selected_agent)
                    else:
                        console.print("[red]Invalid choice.[/red]")
                except ValueError:
                    console.print("[red]Invalid input.[/red]")

        elif choice == '2': # Open Player Packs
            while True:
                console.print("\n[bold blue]--- Player Packs Store ---[/bold blue]")
                console.print(f"Your FUT Budget: [green]€{fut_club.budget:,}[/green]")
                
                pack_list = list(PLAYER_PACKS.items())
                for i, (name, pack) in enumerate(pack_list):
                    console.print(f"[{i+1}] {pack.name} - Price: [red]€{pack.price:,}[/red] (Guaranteed OVR: {pack.guaranteed_ovr_range[0]}-{pack.guaranteed_ovr_range[1]})")
                
                pack_choice = console.input("[bold yellow]Select a pack to open (or 0 to go back):[/bold yellow] ")
                if pack_choice == '0': break
                
                try:
                    pack_idx = int(pack_choice) - 1
                    if 0 <= pack_idx < len(pack_list):
                        selected_pack = pack_list[pack_idx][1]
                        open_player_pack(fut_club, selected_pack)
                    else:
                        console.print("[red]Invalid choice.[/red]")
                except ValueError:
                    console.print("[red]Invalid input.[/red]")

        elif choice == '3': # View My Squad
            display_fut_squad(fut_club)

        elif choice == '4': # View My Stadiums
            display_fut_stadiums(fut_club)

        elif choice == '5': # Champions League Challenge
            run_champions_league_challenge(fut_club)

        elif choice == '6': # Save FUT Club
            save_game("FUT", fut_club.to_dict())

        elif choice == '7': # Exit FUT Mode
            console.print("[bold green]Exiting FUT Mode. Good luck with your club![/bold green]")
            break
        else:
            console.print("[red]Invalid choice.[/red]")

