import random
from .constants import COUNTRIES, POSITIONS, TRAINER_TIERS, ATTRIBUTE_WEIGHTS

class Player:
    """Represents a single player with attributes and an overall rating."""
    def __init__(self, name, position, age, ovr, attributes, country=None, potential=None):
        self.name = name
        self.position = position
        self.age = age
        self.ovr = ovr
        self.potential = potential if potential else min(250, ovr + random.randint(5, 45)) # Higher potential ceiling
        self.attributes = attributes
        self.country = country if country else random.choice(COUNTRIES)
        self.trainer_level = 0 
        self.season_goals = 0
        self.season_clean_sheets = 0
        self.team = None # This will be set externally when added to a team
        
        # New attributes for depth
        self.stamina = 100
        self.morale = 70 # 0-100
        self.form = 50 # 0-100, affects performance
        self.injury_days = 0 # Days until recovered
        self.is_banned = False
        self.match_streak = 0 # For "On Fire" logic
        self.traits = [] # Special abilities

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
        # Adjusted for higher OVR potential
        base_value = (self.ovr ** 3.2) * 85
        age_multiplier = max(0.15, (35 - self.age) / 10) 
        # Form affects value
        form_multiplier = 0.8 + (self.form / 250)
        value = int(base_value * age_multiplier * form_multiplier)
        return max(50_000, value) 

    def __repr__(self):
        trainer_str = ""
        if self.trainer_level > 0:
            tier_names = list(TRAINER_TIERS.keys())
            if self.trainer_level <= len(tier_names):
                trainer_str = f", Trainer: {tier_names[self.trainer_level-1]}"
        injury_str = f" [INJURED: {self.injury_days}d]" if self.injury_days > 0 else ""
        ban_str = " [BANNED]" if self.is_banned else ""
        return f"Player({self.name}, {self.age}, {self.position}, OVR: {self.ovr}{injury_str}{ban_str}, Potential: {self.potential}, Value: €{self.market_value:,}, Country: {self.country}{trainer_str})"

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
            "stamina": self.stamina,
            "morale": self.morale,
            "form": self.form,
            "injury_days": self.injury_days,
            "is_banned": self.is_banned,
            "match_streak": self.match_streak,
            "traits": self.traits
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
        player.stamina = data.get("stamina", 100)
        player.morale = data.get("morale", 70)
        player.form = data.get("form", 50)
        player.injury_days = data.get("injury_days", 0)
        player.is_banned = data.get("is_banned", False)
        player.match_streak = data.get("match_streak", 0)
        player.traits = data.get("traits", [])
        return player


class Team:
    """Represents a football team with a roster of players and season stats."""
    def __init__(self, name, league=None): 
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
        self.league = league 
        self.trophies = [] 
        self.reputation = 50 # 0-100, unlocks better clubs/players
        self.stadium_name = f"{self.name} Stadium"

    @property
    def stadium_capacity(self):
        return 10000 + (self.stadium_level * 5000) # Increased capacity scaling

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
        # Use starting 11 for OVR
        sorted_players = sorted(self.players, key=lambda p: p.ovr, reverse=True)
        top_11_ovr = [p.ovr for p in sorted_players[:11]]
        return sum(top_11_ovr) / len(top_11_ovr) if top_11_ovr else 0

    def get_starting_goalkeeper(self):
        goalkeepers = [p for p in self.players if p.position == 'GK']
        if not goalkeepers:
            return None
        return max(goalkeepers, key=lambda p: p.ovr)

    def __repr__(self):
        return f"Team({self.name}, OVR: {self.get_team_ovr():.2f}, Reputation: {self.reputation}, Budget: €{self.budget:,}, League: {self.league}, Trophies: {len(self.trophies)})"

    def to_dict(self):
        return {
            "name": self.name,
            "players": [p.to_dict() for p in self.players],
            "youth_academy": [p.to_dict() for p in self.youth_academy],
            "budget": self.budget,
            "stadium_level": self.stadium_level,
            "stadium_name": self.stadium_name,
            "academy_level": self.academy_level,
            "points": self.points,
            "games_played": self.games_played,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "league": self.league,
            "trophies": self.trophies,
            "reputation": self.reputation
        }

    @classmethod
    def from_dict(cls, data):
        team = cls(data["name"], data.get("league"))
        team.budget = data["budget"]
        team.stadium_level = data["stadium_level"]
        team.stadium_name = data.get("stadium_name", f"{team.name} Stadium")
        team.academy_level = data["academy_level"]
        team.points = data["points"]
        team.games_played = data["games_played"]
        team.wins = data["wins"]
        team.draws = data["draws"]
        team.losses = data["losses"]
        team.goals_for = data["goals_for"]
        team.goals_against = data["goals_against"]
        team.trophies = data.get("trophies", [])
        team.reputation = data.get("reputation", 50)
        
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
        new_team.stadium_name = self.stadium_name
        new_team.academy_level = self.academy_level
        new_team.trophies = list(self.trophies)
        new_team.reputation = self.reputation
        new_team.points = 0
        new_team.games_played = 0
        new_team.wins = 0
        new_team.draws = 0
        new_team.losses = 0
        new_team.goals_for = 0
        new_team.goals_against = 0
        
        new_team.players = [Player.from_dict(p.to_dict()) for p in self.players]
        for p in new_team.players:
            p.team = new_team 
        new_team.youth_academy = [Player.from_dict(p.to_dict()) for p in self.youth_academy]
        for p in new_team.youth_academy:
            p.team = new_team
        return new_team
