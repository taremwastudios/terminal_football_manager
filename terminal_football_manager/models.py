import random
from .constants import COUNTRIES, POSITIONS, TRAINER_TIERS, ATTRIBUTE_WEIGHTS

class Player:
    """Represents a single player with attributes and an overall rating."""
    def __init__(self, name, position, age, ovr, attributes, country=None, potential=None):
        self.name = name
        self.position = position
        self.age = age
        self.ovr = ovr
        self.potential = potential if potential else min(150, ovr + random.randint(5, 25))
        self.attributes = attributes
        self.country = country if country else random.choice(COUNTRIES)
        self.trainer_level = 0 
        self.season_goals = 0
        self.season_clean_sheets = 0
        self.team = None # This will be set externally when added to a team

    @property
    def salary(self):
        """Calculates player salary based on OVR and age."""
        base_salary = self.ovr * 5000 
        age_multiplier = 1.0
        if self.age < 22: age_multiplier = 0.7
        elif self.age > 30: age_multiplier = 0.8
        return int(base_salary * age_multiplier)

    @property
    def market_value(self):
        """Calculates the market value of a player in Euros based on OVR and age."""
        base_value = self.ovr ** 3 * 80
        age_multiplier = max(0.15, (33 - self.age) / 8) 
        value = int(base_value * age_multiplier)
        return max(100_000, value) 

    def __repr__(self):
        trainer_str = ""
        if self.trainer_level > 0:
            tier_names = list(TRAINER_TIERS.keys())
            if self.trainer_level <= len(tier_names):
                trainer_str = f", Trainer: {tier_names[self.trainer_level-1]}"
        return f"Player({self.name}, {self.age}, {self.position}, OVR: {self.ovr}, Potential: {self.potential}, Value: €{self.market_value:,}, Salary: €{self.salary:,}, Country: {self.country}{trainer_str})"

    def to_dict(self):
        return {
            "name": self.name,
            "position": self.position,
            "age": self.age,
            "ovr": self.ovr,
            "potential": self.potential,
            "attributes": self.attributes,
            "country": self.country,
            "trainer_level": self.trainer_level,
            "season_goals": self.season_goals,
            "season_clean_sheets": self.season_clean_sheets,
            # Do NOT store 'team' directly to avoid circular references; it's re-linked on load
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
            data.get("potential")
        )
        player.trainer_level = data["trainer_level"]
        player.season_goals = data["season_goals"]
        player.season_clean_sheets = data["season_clean_sheets"]
        # player.team will be set externally after all teams are loaded
        return player


class Team:
    """Represents a football team with a roster of players and season stats."""
    def __init__(self, name, league=None): # Added league attribute
        self.name = name
        self.players = []
        self.youth_academy = []
        self.budget = 0
        self.stadium_level = 1
        self.academy_level = 1
        self.points = 0
        self.games_played = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.goals_for = 0
        self.goals_against = 0
        self.league = league # Store league affiliation
        self.trophies = [] # List of trophies won

    @property
    def stadium_capacity(self):
        return 10000 + (self.stadium_level * 500)

    @property
    def total_squad_value(self):
        return sum(p.market_value for p in self.players)

    @property
    def total_wage_bill(self):
        return sum(p.salary for p in self.players)

    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against

    def add_player(self, player):
        self.players.append(player)
        player.team = self

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
            player.team = None
            return True
        return False

    def get_team_ovr(self):
        if not self.players:
            return 0
        sorted_players = sorted(self.players, key=lambda p: p.ovr, reverse=True)
        top_11_ovr = [p.ovr for p in sorted_players[:11]]
        return sum(top_11_ovr) / len(top_11_ovr) if top_11_ovr else 0

    def get_starting_goalkeeper(self):
        goalkeepers = [p for p in self.players if p.position == 'GK']
        if not goalkeepers:
            return None
        return max(goalkeepers, key=lambda p: p.ovr)

    def __repr__(self):
        return f"Team({self.name}, OVR: {self.get_team_ovr():.2f}, Budget: €{self.budget:,}, League: {self.league}, Trophies: {len(self.trophies)})"

    def to_dict(self):
        return {
            "name": self.name,
            "players": [p.to_dict() for p in self.players], # Convert players to dicts
            "youth_academy": [p.to_dict() for p in self.youth_academy], # Convert youth players to dicts
            "budget": self.budget,
            "stadium_level": self.stadium_level,
            "academy_level": self.academy_level,
            "points": self.points,
            "games_played": self.games_played,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "league": self.league, # Save league affiliation
            "trophies": self.trophies
        }

    @classmethod
    def from_dict(cls, data):
        team = cls(data["name"], data.get("league")) # Pass league to constructor
        team.budget = data["budget"]
        team.stadium_level = data["stadium_level"]
        team.academy_level = data["academy_level"]
        team.points = data["points"]
        team.games_played = data["games_played"]
        team.wins = data["wins"]
        team.draws = data["draws"]
        team.losses = data["losses"]
        team.goals_for = data["goals_for"]
        team.goals_against = data["goals_against"]
        team.trophies = data.get("trophies", [])
        
        # Players are reconstructed but their 'team' attribute is set by deserialize_game_state
        for p_data in data["players"]:
            team.players.append(Player.from_dict(p_data))
        for yp_data in data["youth_academy"]:
            team.youth_academy.append(Player.from_dict(yp_data))
        return team

    def copy(self):
        """Creates a deep copy of the team, isolating stats for simulations."""
        new_team = Team(self.name, self.league)
        new_team.budget = self.budget
        new_team.stadium_level = self.stadium_level
        new_team.academy_level = self.academy_level
        new_team.trophies = list(self.trophies)
        # Reset stats for the copy as it's for a new competition
        new_team.points = 0
        new_team.games_played = 0
        new_team.wins = 0
        new_team.draws = 0
        new_team.losses = 0
        new_team.goals_for = 0
        new_team.goals_against = 0
        
        # Deep copy players too, so their individual stats for the competition are separate
        new_team.players = [Player.from_dict(p.to_dict()) for p in self.players]
        for p in new_team.players:
            p.team = new_team # Link copied players to their copied team
        new_team.youth_academy = [Player.from_dict(p.to_dict()) for p in self.youth_academy]
        for p in new_team.youth_academy:
            p.team = new_team
        return new_team