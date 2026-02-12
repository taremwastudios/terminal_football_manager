import random
import json
import os
from .constants import *

from .persistence import save_game, load_game

class HeroPlayer:
    """Represents the user's single player in Hero Mode."""
    def __init__(self, name, position, age, ovr, attributes, country, team_name=None, career_season_count=1):
        self.name = name
        self.position = position
        self.age = age
        self.ovr = ovr
        self.attributes = attributes
        self.country = country
        self.team_name = team_name 
        self.career_goals = 0
        self.career_assists = 0 # Future use
        self.seasons_played = 0
        self.career_season_count = career_season_count # To track overall career length for save/load

    @property
    def market_value(self):
        """Calculates the market value of a player."""
        base_value = self.ovr ** 3 * 100
        age_multiplier = max(0.1, (30 - self.age) / 10 + 0.5) 
        return int(base_value * age_multiplier)

    @property
    def salary(self):
        """Calculates player salary."""
        base_salary = self.ovr * 7500
        age_multiplier = 1.0
        if self.age < 22: age_multiplier = 0.7
        elif self.age > 30: age_multiplier = 0.8
        return int(base_salary * age_multiplier)

    def __repr__(self):
        return f"HeroPlayer({self.name}, {self.age}, {self.position}, OVR: {self.ovr}, Value: €{self.market_value:,}, Salary: €{self.salary:,}, Country: {self.country}, Team: {self.team_name if self.team_name else 'Unattached'}, Goals: {self.career_goals})"

    def to_dict(self):
        return {
            "name": self.name,
            "position": self.position,
            "age": self.age,
            "ovr": self.ovr,
            "attributes": self.attributes,
            "country": self.country,
            "team_name": self.team_name,
            "career_goals": self.career_goals,
            "career_assists": self.career_assists,
            "seasons_played": self.seasons_played,
            "career_season_count": self.career_season_count,
        }

    @classmethod
    def from_dict(cls, data):
        player = cls(
            data["name"],
            data["position"],
            data["age"],
            data["ovr"],
            data["attributes"],
            data["country"],
            data["team_name"],
            data["career_season_count"]
        )
        player.career_goals = data.get("career_goals", 0)
        player.career_assists = data.get("career_assists", 0)
        player.seasons_played = data.get("seasons_played", 0)
        return player

def generate_hero_player():
    """Generates a HeroPlayer with starting stats suitable for weak teams."""
    print("\n--- Create Your Hero Player ---")
    name = input("Enter your player's first name: ")
    last_name = input("Enter your player's last name: ")
    full_name = f"{name} {last_name}"

    print("Select your player's position:")
    for i, pos in enumerate(POSITIONS):
        print(f"[{i+1}] {pos}")
    
    position = None
    while position not in POSITIONS:
        try:
            choice = int(input("Enter position number: "))
            if 1 <= choice <= len(POSITIONS):
                position = POSITIONS[choice-1]
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    age = random.randint(18, 20) # Start young
    ovr = random.randint(55, 65) # Start low
    country = random.choice(COUNTRIES)

    attributes = {attr: int(ovr * (1 + (random.random() - 0.3) * 0.3)) for attr in ATTRIBUTE_WEIGHTS[position]}
    for attr, weight in ATTRIBUTE_WEIGHTS[position].items():
        attributes[attr] = int(attributes[attr] * (1 + weight))
        attributes[attr] = max(10, min(attributes[attr], 90))
    
    return HeroPlayer(full_name, position, age, ovr, attributes, country, team_name="Unattached")

def generate_offer_team_name(player_ovr):
    """Generates a team name based on player OVR for offers."""
    if player_ovr < 65:
        return random.choice(["Local Amateurs", "Village FC", "Youth Stars FC"])
    elif 65 <= player_ovr < 75:
        return random.choice(["Lower League United", "Regional Rovers", "Promising FC"])
    elif 75 <= player_ovr < 85:
        return random.choice(["Mid-Table City", "League Challengers", "Rising Phoenix"])
    elif 85 <= player_ovr < 95:
        return random.choice(["Top Flight FC", "Elite United", "Continental Hope"])
    else: # ovr >= 95
        return random.choice(["Champions League Elite", "Global Giants", "Dream Team FC"])


def simulate_player_performance(hero_player):
    """Simulates player's goals for a season based on OVR and position."""
    goals = 0
    if hero_player.position in ["CF", "SS", "RWF", "LWF"]:
        goals = random.randint(max(0, hero_player.ovr // 10 - 5), hero_player.ovr // 5)
    elif hero_player.position in ["CMF", "AMF"]:
        goals = random.randint(max(0, hero_player.ovr // 15 - 5), hero_player.ovr // 7)
    else: # Defenders/Goalkeepers
        goals = random.randint(0, 3) # Very rare goals

    hero_player.career_goals += goals
    return goals

def run_player_career_mode(hero_player=None):
    print("\n--- Welcome to Player Career Mode ---")
    career_season_count = 1

    if hero_player is None:
        while hero_player is None:
            print("\n1. Start New Career")
            print("2. Load Career")
            print("3. Back to Main Menu")
            choice = input("Enter your choice: ")

            if choice == '1':
                hero_player = generate_hero_player()
                print(f"\nYour career begins! {hero_player}")
            elif choice == '2':
                mode, loaded_state = load_game()
                if mode == "Player Career" and loaded_state:
                    hero_player = HeroPlayer.from_dict(loaded_state)
                    career_season_count = hero_player.career_season_count
                    print(f"\nCareer loaded: {hero_player}")
                else:
                    print("No Player Career save found in unified save file.")
            elif choice == '3':
                return # Go back to main menu
            else:
                print("Invalid choice.")
    else:
        career_season_count = hero_player.career_season_count
        print(f"\nContinuing career: {hero_player}")

    while True: # Main career loop
        print(f"\n--- Season {career_season_count} ---")
        hero_player.seasons_played += 1
        hero_player.age += 1

        if hero_player.age >= 40:
            print(f"\n--- RETIREMENT ---")
            print(f"{hero_player.name} has reached the age of {hero_player.age} and has decided to retire!")
            print(f"Career Stats: {hero_player.seasons_played} seasons, {hero_player.career_goals} goals.")
            input("Press Enter to end career...")
            break # Exit career loop

        print(f"\n{hero_player.name} (Age: {hero_player.age}, OVR: {hero_player.ovr})")
        print(f"Current Team: {hero_player.team_name if hero_player.team_name else 'Unattached'}")
        
        # Simulate OVR changes
        ovr_change = 0
        if hero_player.age < 24: ovr_change = random.randint(1, 3)
        elif 24 <= hero_player.age <= 29: ovr_change = random.randint(0, 2)
        elif 30 <= hero_player.age <= 34: ovr_change = random.randint(-1, 1)
        else: ovr_change = random.randint(-3, -1)
        
        old_ovr = hero_player.ovr
        hero_player.ovr = max(10, hero_player.ovr + ovr_change)
        if hero_player.ovr != old_ovr:
            print(f"Player development: OVR changed from {old_ovr} to {hero_player.ovr}")

        # Simulate performance
        season_goals = simulate_player_performance(hero_player)
        print(f"This season: {season_goals} goals. Total Career Goals: {hero_player.career_goals}")

        # Offer/Action menu
        while True:
            print("\n--- Player Actions ---")
            print("1. View Player Info")
            print("2. Train (Improve Attributes)") # Placeholder
            print("3. Request Transfer") # Placeholder
            print("4. Continue to Next Season")
            print("5. Save Career")
            print("6. Exit Career (without saving)")

            action_choice = input("Enter your action: ")

            if action_choice == '1':
                print(hero_player)
            elif action_choice == '2':
                # Simplified training: direct OVR boost
                if hero_player.ovr < 100:
                    train_boost = random.randint(1, 2)
                    hero_player.ovr = min(100, hero_player.ovr + train_boost)
                    print(f"You trained hard! OVR increased by {train_boost} to {hero_player.ovr}.")
                else:
                    print("You're already at max OVR!")
            elif action_choice == '3':
                # Simplified transfer request
                offer_team_name = generate_offer_team_name(hero_player.ovr)
                print(f"\n{offer_team_name} is interested in signing you!")
                print(f"Current Team: {hero_player.team_name if hero_player.team_name else 'Unattached'}")
                print(f"Offer from: {offer_team_name}")
                transfer_choice = input("Accept offer? (yes/no): ").lower()
                if transfer_choice == 'yes':
                    hero_player.team_name = offer_team_name
                    print(f"You've accepted the offer and joined {hero_player.team_name}!")
                else:
                    print("You decided to stay put for now.")
            elif action_choice == '4':
                break # Exit action menu, continue to next season
            elif action_choice == '5':
                save_game("Player Career", hero_player.to_dict())
            elif action_choice == '6':
                print("Exiting Player Career Mode.")
                return # Go back to main menu
            else:
                print("Invalid choice.")
        
        career_season_count += 1
