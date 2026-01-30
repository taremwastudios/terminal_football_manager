from collections import namedtuple
import random

# --- FUT Player Data (Real FC Mobile inspired, with expanded OVR) ---
# OVRs adjusted for game balance and premium rewards up to 190.
# Attributes are simplified as a list for now, actual calculation happens in Player class.

FUTPlayer = namedtuple("FUTPlayer", ["name", "position", "age", "base_ovr", "country", "card_type"])

# Example Real Players for various packs and OVR ranges
FUT_PLAYERS_DATA = [
    # General / Common Players (45-80 OVR)
    FUTPlayer("Joe Bloggs", "CB", 25, 60, "England", "Common"),
    FUTPlayer("Juan Perez", "CMF", 23, 68, "Spain", "Common"),
    FUTPlayer("Ali Khan", "ST", 28, 75, "Egypt", "Common"),
    FUTPlayer("Kim Min-Jae", "RB", 21, 70, "South Korea", "Common"),
    FUTPlayer("Carlos Silva", "LB", 26, 65, "Brazil", "Common"),

    # Team of the Season (TOTS) - High OVR (100-150+)
    FUTPlayer("Lionel Messi", "RW", 36, 145, "Argentina", "Team of the Season"),
    FUTPlayer("Cristiano Ronaldo", "ST", 39, 140, "Portugal", "Team of the Season"),
    FUTPlayer("Kylian Mbappé", "ST", 25, 150, "France", "Team of the Season"),
    FUTPlayer("Erling Haaland", "ST", 23, 148, "Norway", "Team of the Season"),
    FUTPlayer("Kevin De Bruyne", "CM", 32, 142, "Belgium", "Team of the Season"),
    FUTPlayer("Virgil van Dijk", "CB", 32, 138, "Netherlands", "Team of the Season"),
    FUTPlayer("Jude Bellingham", "CM", 20, 147, "England", "Team of the Season"),
    FUTPlayer("Vinicius Jr.", "LW", 23, 143, "Brazil", "Team of the Season"),
    FUTPlayer("Robert Lewandowski", "ST", 35, 139, "Poland", "Team of the Season"),
    FUTPlayer("Mohamed Salah", "RW", 31, 141, "Egypt", "Team of the Season"),

    # FC Captains - Mid to High OVR (90-130+)
    FUTPlayer("Sergio Ramos", "CB", 37, 120, "Spain", "FC Captains"),
    FUTPlayer("Manuel Neuer", "GK", 37, 125, "Germany", "FC Captains"),
    FUTPlayer("Harry Kane", "ST", 30, 130, "England", "FC Captains"),
    FUTPlayer("Bruno Fernandes", "CAM", 29, 128, "Portugal", "FC Captains"),
    FUTPlayer("Son Heung-min", "LW", 31, 127, "South Korea", "FC Captains"),

    # Grassroot Greats - Promising Youngsters / Unique talents (80-120 OVR)
    FUTPlayer("Pedri", "CM", 21, 115, "Spain", "Grassroot Greats"),
    FUTPlayer("Jamal Musiala", "CAM", 20, 118, "Germany", "Grassroot Greats"),
    FUTPlayer("Gavi", "CM", 19, 110, "Spain", "Grassroot Greats"),
    FUTPlayer("Florian Wirtz", "CAM", 20, 117, "Germany", "Grassroot Greats"),

    # Aqua Or Inferno - Themed event players (110-160 OVR)
    FUTPlayer("Neymar Jr.", "LW", 31, 155, "Brazil", "Aqua Or Inferno"), # Inferno
    FUTPlayer("Ruben Dias", "CB", 26, 145, "Portugal", "Aqua Or Inferno"), # Aqua
    FUTPlayer("Rodri", "CDM", 27, 148, "Spain", "Aqua Or Inferno"), # Aqua
    FUTPlayer("Antoine Griezmann", "ST", 32, 152, "France", "Aqua Or Inferno"), # Inferno

    # Team of the Year (TOTY) - Top Tier OVR (150-170+)
    FUTPlayer("Karim Benzema", "ST", 36, 160, "France", "Team of the Year"),
    FUTPlayer("Thibaut Courtois", "GK", 31, 158, "Belgium", "Team of the Year"),
    FUTPlayer("Luka Modric", "CM", 38, 155, "Croatia", "Team of the Year"),
    FUTPlayer("Casemiro", "CDM", 31, 157, "Brazil", "Team of the Year"),
    FUTPlayer("Kevin De Bruyne", "CM", 32, 165, "Belgium", "Team of the Year"), # Another version
    FUTPlayer("Virgil van Dijk", "CB", 32, 162, "Netherlands", "Team of the Year"), # Another version

    # Premium Rewards (177-190 OVR) - Elite of the Elite
    FUTPlayer("Pelé", "CAM", 83, 190, "Brazil", "Premium Icon"),
    FUTPlayer("Diego Maradona", "CAM", 60, 188, "Argentina", "Premium Icon"),
    FUTPlayer("Johan Cruyff", "CAM", 76, 185, "Netherlands", "Premium Icon"),
    FUTPlayer("Franz Beckenbauer", "SW", 78, 187, "Germany", "Premium Icon"),
    FUTPlayer("Zinedine Zidane", "CAM", 51, 180, "France", "Premium Icon"),
    FUTPlayer("Ronaldo Nazário", "ST", 47, 183, "Brazil", "Premium Icon"),
    FUTPlayer("Paolo Maldini", "LB", 55, 179, "Italy", "Premium Icon"),
    FUTPlayer("Garrincha", "RW", 72, 177, "Brazil", "Premium Icon"),
]

# --- Champions League Challenge Data ---
CHAMPIONS_LEAGUE_TEAMS_DATA = [
    {"name": "Real Madrid", "players": [
        FUTPlayer("Thibaut Courtois", "GK", 31, 158, "Belgium", "Team of the Year"),
        FUTPlayer("Éder Militão", "CB", 26, 135, "Brazil", "Team of the Season"),
        FUTPlayer("David Alaba", "CB", 31, 130, "Austria", "FC Captains"),
        FUTPlayer("Dani Carvajal", "RB", 32, 125, "Spain", "FC Captains"),
        FUTPlayer("Ferland Mendy", "LB", 28, 120, "France", "Common"),
        FUTPlayer("Casemiro", "CDM", 31, 157, "Brazil", "Team of the Year"),
        FUTPlayer("Toni Kroos", "CM", 34, 130, "Germany", "FC Captains"),
        FUTPlayer("Luka Modric", "CM", 38, 155, "Croatia", "Team of the Year"),
        FUTPlayer("Jude Bellingham", "CM", 20, 147, "England", "Team of the Season"),
        FUTPlayer("Vinicius Jr.", "LW", 23, 143, "Brazil", "Team of the Season"),
        FUTPlayer("Rodrygo", "RW", 23, 138, "Brazil", "Team of the Season"),
        FUTPlayer("Karim Benzema", "ST", 36, 160, "France", "Team of the Year"),
        FUTPlayer("Federico Valverde", "CM", 25, 130, "Uruguay", "FC Captains"),
        FUTPlayer("Aurélien Tchouaméni", "CDM", 24, 125, "France", "Grassroot Greats"),
        FUTPlayer("Eduardo Camavinga", "CM", 21, 120, "France", "Grassroot Greats"),
        FUTPlayer("Arda Güler", "CAM", 19, 110, "Turkey", "Grassroot Greats"),
        FUTPlayer("Brahim Díaz", "CAM", 24, 105, "Spain", "Common"),
        FUTPlayer("Joselu", "ST", 34, 100, "Spain", "Common"),
        FUTPlayer("Andriy Lunin", "GK", 25, 100, "Ukraine", "Common"),
        FUTPlayer("Nacho", "CB", 34, 95, "Spain", "Common"),
        FUTPlayer("Lucas Vázquez", "RB", 32, 90, "Spain", "Common"),
        FUTPlayer("Eder Militao", "CB", 26, 135, "Brazil", "Team of the Season"), # Ensure 22 players
    ]},
    {"name": "Manchester City", "players": [
        FUTPlayer("Ederson", "GK", 30, 135, "Brazil", "Team of the Season"),
        FUTPlayer("Ruben Dias", "CB", 26, 145, "Portugal", "Aqua Or Inferno"),
        FUTPlayer("John Stones", "CB", 29, 130, "England", "FC Captains"),
        FUTPlayer("Kyle Walker", "RB", 33, 128, "England", "FC Captains"),
        FUTPlayer("Joško Gvardiol", "CB", 22, 125, "Croatia", "Grassroot Greats"),
        FUTPlayer("Rodri", "CDM", 27, 148, "Spain", "Aqua Or Inferno"),
        FUTPlayer("Kevin De Bruyne", "CM", 32, 165, "Belgium", "Team of the Year"),
        FUTPlayer("Bernardo Silva", "CAM", 29, 138, "Portugal", "Team of the Season"),
        FUTPlayer("Phil Foden", "LW", 23, 132, "England", "Team of the Season"),
        FUTPlayer("Julian Álvarez", "ST", 24, 130, "Argentina", "Team of the Season"),
        FUTPlayer("Erling Haaland", "ST", 23, 148, "Norway", "Team of the Season"),
        FUTPlayer("Manuel Akanji", "CB", 28, 120, "Switzerland", "Common"),
        FUTPlayer("Nathan Aké", "CB", 29, 118, "Netherlands", "Common"),
        FUTPlayer("Mateo Kovačić", "CM", 29, 115, "Croatia", "Common"),
        FUTPlayer("Jack Grealish", "LW", 28, 110, "England", "Common"),
        FUTPlayer("Jeremy Doku", "LW", 21, 108, "Belgium", "Grassroot Greats"),
        FUTPlayer("Kalvin Phillips", "CDM", 28, 105, "England", "Common"),
        FUTPlayer("Stefan Ortega", "GK", 35, 100, "Germany", "Common"),
        FUTPlayer("Scott Carson", "GK", 38, 90, "England", "Common"),
        FUTPlayer("Rico Lewis", "RB", 19, 95, "England", "Grassroot Greats"),
        FUTPlayer("Oscar Bobb", "RW", 20, 90, "Norway", "Grassroot Greats"),
        FUTPlayer("Sergio Gómez", "LB", 23, 85, "Spain", "Common"),
    ]},
    {"name": "Bayern Munich", "players": [
        FUTPlayer("Manuel Neuer", "GK", 37, 125, "Germany", "FC Captains"),
        FUTPlayer("Matthijs de Ligt", "CB", 24, 130, "Netherlands", "Team of the Season"),
        FUTPlayer("Kim Min-Jae", "CB", 27, 128, "South Korea", "Team of the Season"),
        FUTPlayer("Alphonso Davies", "LB", 23, 125, "Canada", "Team of the Season"),
        FUTPlayer("Joshua Kimmich", "CDM", 29, 138, "FC Captains", "Germany"),
        FUTPlayer("Leon Goretzka", "CM", 29, 130, "Germany", "Team of the Season"),
        FUTPlayer("Jamal Musiala", "CAM", 20, 118, "Germany", "Grassroot Greats"),
        FUTPlayer("Leroy Sané", "LW", 28, 127, "Germany", "Team of the Season"),
        FUTPlayer("Kingsley Coman", "RW", 27, 125, "France", "Team of the Season"),
        FUTPlayer("Harry Kane", "ST", 30, 130, "England", "FC Captains"),
        FUTPlayer("Serge Gnabry", "RW", 28, 120, "Germany", "Common"),
        FUTPlayer("Dayot Upamecano", "CB", 25, 118, "France", "Common"),
        FUTPlayer("Noussair Mazraoui", "RB", 26, 115, "Morocco", "Common"),
        FUTPlayer("Konrad Laimer", "CM", 26, 110, "Austria", "Common"),
        FUTPlayer("Mathys Tel", "ST", 18, 105, "France", "Grassroot Greats"),
        FUTPlayer("Eric Maxim Choupo-Moting", "ST", 35, 95, "Cameroon", "Common"),
        FUTPlayer("Bouna Sarr", "RB", 32, 90, "Senegal", "Common"),
        FUTPlayer("Sven Ulreich", "GK", 35, 90, "Germany", "Common"),
        FUTPlayer("Raphaël Guerreiro", "LB", 30, 105, "Portugal", "Common"),
        FUTPlayer("Thomas Müller", "CAM", 34, 120, "Germany", "FC Captains"),
        FUTPlayer("Joshua Kimmich", "CDM", 29, 138, "Germany", "FC Captains"), # Ensure 22 players
        FUTPlayer("Matthijs de Ligt", "CB", 24, 130, "Netherlands", "Team of the Season"), # Ensure 22 players
    ]},
    {"name": "Liverpool", "players": [
        FUTPlayer("Alisson", "GK", 31, 130, "Brazil", "Team of the Season"),
        FUTPlayer("Virgil van Dijk", "CB", 32, 138, "Netherlands", "Team of the Season"),
        FUTPlayer("Ibrahima Konaté", "CB", 24, 125, "France", "Common"),
        FUTPlayer("Trent Alexander-Arnold", "RB", 25, 132, "England", "Team of the Season"),
        FUTPlayer("Andrew Robertson", "LB", 30, 128, "Scotland", "Team of the Season"),
        FUTPlayer("Fabinho", "CDM", 30, 120, "Brazil", "Common"),
        FUTPlayer("Alexis Mac Allister", "CM", 25, 128, "Argentina", "Team of the Season"),
        FUTPlayer("Dominik Szoboszlai", "CAM", 23, 125, "Hungary", "Grassroot Greats"),
        FUTPlayer("Mohamed Salah", "RW", 31, 141, "Egypt", "Team of the Season"),
        FUTPlayer("Luis Díaz", "LW", 27, 128, "Colombia", "Team of the Season"),
        FUTPlayer("Darwin Núñez", "ST", 24, 127, "Uruguay", "Team of the Season"),
        FUTPlayer("Harvey Elliott", "CAM", 20, 110, "England", "Grassroot Greats"),
        FUTPlayer("Curtis Jones", "CM", 23, 105, "England", "Grassroot Greats"),
        FUTPlayer("Joe Gomez", "CB", 26, 100, "England", "Common"),
        FUTPlayer("Konstantinos Tsimikas", "LB", 27, 95, "Greece", "Common"),
        FUTPlayer("Wataru Endo", "CDM", 31, 98, "Japan", "Common"),
        FUTPlayer("Cody Gakpo", "ST", 24, 120, "Netherlands", "Common"),
        FUTPlayer("Diogo Jota", "ST", 27, 125, "Portugal", "Common"),
        FUTPlayer("Caoimhín Kelleher", "GK", 25, 90, "Ireland", "Common"),
        FUTPlayer("Adrian", "GK", 37, 85, "Spain", "Common"),
        FUTPlayer("Joel Matip", "CB", 32, 105, "Cameroon", "Common"),
        FUTPlayer("Thiago", "CM", 32, 115, "Spain", "Common"),
    ]},
    {"name": "Paris Saint-Germain", "players": [
        FUTPlayer("Gianluigi Donnarumma", "GK", 25, 128, "Italy", "Team of the Season"),
        FUTPlayer("Marquinhos", "CB", 29, 135, "Brazil", "FC Captains"),
        FUTPlayer("Milan Škriniar", "CB", 29, 128, "Slovakia", "Team of the Season"),
        FUTPlayer("Achraf Hakimi", "RB", 25, 130, "Morocco", "Team of the Season"),
        FUTPlayer("Nuno Mendes", "LB", 21, 120, "Portugal", "Grassroot Greats"),
        FUTPlayer("Vitinha", "CM", 24, 118, "Portugal", "Common"),
        FUTPlayer("Warren Zaïre-Emery", "CM", 18, 115, "France", "Grassroot Greats"),
        FUTPlayer("Ousmane Dembélé", "RW", 26, 128, "France", "Team of the Season"),
        FUTPlayer("Kylian Mbappé", "ST", 25, 150, "France", "Team of the Season"),
        FUTPlayer("Neymar Jr.", "LW", 31, 155, "Brazil", "Aqua Or Inferno"),
        FUTPlayer("Randall Kolo Muani", "ST", 25, 125, "France", "Common"),
        FUTPlayer("Bradley Barcola", "LW", 21, 110, "France", "Grassroot Greats"),
        FUTPlayer("Gonçalo Ramos", "ST", 22, 118, "Portugal", "Common"),
        FUTPlayer("Lee Kang-in", "CAM", 23, 115, "South Korea", "Grassroot Greats"),
        FUTPlayer("Manuel Ugarte", "CDM", 23, 110, "Uruguay", "Common"),
        FUTPlayer("Lucas Hernández", "CB", 28, 115, "France", "Common"),
        FUTPlayer("Presnel Kimpembe", "CB", 28, 105, "France", "Common"),
        FUTPlayer("Nordi Mukiele", "RB", 26, 100, "France", "Common"),
        FUTPlayer("Arnau Tenas", "GK", 23, 90, "Spain", "Common"),
        FUTPlayer("Keylor Navas", "GK", 37, 100, "Costa Rica", "Common"),
        FUTPlayer("Danilo Pereira", "CDM", 32, 100, "Portugal", "Common"),
        FUTPlayer("Carlos Soler", "CM", 27, 105, "Spain", "Common"),
    ]},
    {"name": "Barcelona", "players": [
        FUTPlayer("Marc-André ter Stegen", "GK", 31, 125, "Germany", "FC Captains"),
        FUTPlayer("Ronald Araújo", "CB", 25, 130, "Uruguay", "Team of the Season"),
        FUTPlayer("Jules Kounde", "CB", 25, 128, "France", "Team of the Season"),
        FUTPlayer("Alejandro Balde", "LB", 20, 120, "Spain", "Grassroot Greats"),
        FUTPlayer("João Cancelo", "RB", 29, 127, "Portugal", "Team of the Season"),
        FUTPlayer("Frenkie de Jong", "CM", 26, 135, "Netherlands", "Team of the Season"),
        FUTPlayer("Pedri", "CM", 21, 115, "Spain", "Grassroot Greats"),
        FUTPlayer("Gavi", "CM", 19, 110, "Spain", "Grassroot Greats"),
        FUTPlayer("Ilkay Gündoğan", "CM", 33, 125, "Germany", "FC Captains"),
        FUTPlayer("Robert Lewandowski", "ST", 35, 139, "Poland", "Team of the Season"),
        FUTPlayer("Raphinha", "RW", 27, 126, "Brazil", "Team of the Season"),
        FUTPlayer("Lamine Yamal", "RW", 16, 115, "Spain", "Grassroot Greats"),
        FUTPlayer("Ferran Torres", "ST", 24, 110, "Spain", "Common"),
        FUTPlayer("Andreas Christensen", "CB", 27, 105, "Denmark", "Common"),
        FUTPlayer("Sergi Roberto", "RB", 32, 95, "Spain", "FC Captains"),
        FUTPlayer("Oriol Romeu", "CDM", 32, 98, "Spain", "Common"),
        FUTPlayer("Iñigo Martínez", "CB", 32, 100, "Spain", "Common"),
        FUTPlayer("Vitor Roque", "ST", 19, 108, "Brazil", "Grassroot Greats"),
        FUTPlayer("Marc Guiu", "ST", 18, 95, "Spain", "Grassroot Greats"),
        FUTPlayer("Fermín López", "CM", 20, 98, "Spain", "Grassroot Greats"),
        FUTPlayer("João Félix", "LW", 24, 122, "Portugal", "Common"),
        FUTPlayer("Raphinha", "RW", 27, 126, "Brazil", "Team of the Season"),
    ]}
]

CHAMPIONS_LEAGUE_REWARDS = {
    "Group Stage": {"coins": 50_000, "pack": "Silver Pack"},
    "Round of 16": {"coins": 100_000, "pack": "Gold Pack"},
    "Quarter-Finals": {"coins": 250_000, "pack": "Grassroot Greats Pack"},
    "Semi-Finals": {"coins": 500_000, "pack": "FC Captains Pack"},
    "Final": {"coins": 1_000_000, "pack": "Team of the Season Pack"},
    "Winner": {"coins": 10_000_000, "pack": "Premium Icon Pack"},
}


# --- Agent Tiers ---
AgentTier = namedtuple("AgentTier", ["name", "cost", "min_ovr", "max_ovr", "pack_chances"])

AGENT_TIERS = {
    "Common Agent": AgentTier(
        name="Common Agent",
        cost=10_000,
        min_ovr=45,
        max_ovr=80,
        pack_chances={"Team of the Season": 5} # 5% chance
    ),
    "Rare Agent": AgentTier(
        name="Rare Agent",
        cost=50_000,
        min_ovr=66,
        max_ovr=100,
        pack_chances={"FC Captains": 35, "Team of the Season": 35} # 35% chance each
    ),
    "Legendary Agent": AgentTier(
        name="Legendary Agent",
        cost=200_000,
        min_ovr=99,
        max_ovr=150,
        pack_chances={
            "Team of the Season": 25,
            "Grassroot Greats": 20,
            "FC Captains": 20,
            "Aqua Or Inferno": 15,
            "Team of the Year": 15 # Total 95%, remaining 5% for standard high OVR
        }
    )
}

# --- Player Packs ---
PlayerPack = namedtuple("PlayerPack", ["name", "price", "guaranteed_ovr_range", "player_pools", "stadium_chance"])

PLAYER_PACKS = {
    "Bronze Pack": PlayerPack(
        name="Bronze Pack",
        price=5_000,
        guaranteed_ovr_range=(45, 60),
        player_pools=["Common"],
        stadium_chance=1 # 1% chance for any stadium
    ),
    "Silver Pack": PlayerPack(
        name="Silver Pack",
        price=15_000,
        guaranteed_ovr_range=(60, 75),
        player_pools=["Common"], # Still mostly common, but higher OVR
        stadium_chance=2
    ),
    "Gold Pack": PlayerPack(
        name="Gold Pack",
        price=50_000,
        guaranteed_ovr_range=(75, 90),
        player_pools=["Common", "Grassroot Greats"], # Chance for a Grassroot Great
        stadium_chance=3
    ),
    "Team of the Season Pack": PlayerPack(
        name="Team of the Season Pack",
        price=150_000,
        guaranteed_ovr_range=(100, 140),
        player_pools=["Team of the Season"],
        stadium_chance=5
    ),
    "FC Captains Pack": PlayerPack(
        name="FC Captains Pack",
        price=120_000,
        guaranteed_ovr_range=(90, 130),
        player_pools=["FC Captains"],
        stadium_chance=4
    ),
    "Grassroot Greats Pack": PlayerPack(
        name="Grassroot Greats Pack",
        price=100_000,
        guaranteed_ovr_range=(80, 120),
        player_pools=["Grassroot Greats"],
        stadium_chance=3
    ),
    "Aqua Or Inferno Pack": PlayerPack(
        name="Aqua Or Inferno Pack",
        price=180_000,
        guaranteed_ovr_range=(110, 150),
        player_pools=["Aqua Or Inferno"],
        stadium_chance=6
    ),
    "Team of the Year Pack": PlayerPack(
        name="Team of the Year Pack",
        price=250_000,
        guaranteed_ovr_range=(150, 170),
        player_pools=["Team of the Year"],
        stadium_chance=8
    ),
    "Premium Icon Pack": PlayerPack(
        name="Premium Icon Pack",
        price=500_000,
        guaranteed_ovr_range=(177, 190),
        player_pools=["Premium Icon"],
        stadium_chance=10 # Higher chance for stadiums
    ),
}

# --- Stadium Data (Real Stadiums) ---
STADIUM_NAMES = [
    "Wembley Stadium", "Camp Nou", "Santiago Bernabéu", "Old Trafford",
    "Allianz Arena", "San Siro", "Anfield", "Signal Iduna Park",
    "Estadio Azteca", "Maracanã", "Soccer City", "Parc des Princes",
    "Juventus Stadium", "Stamford Bridge", "Etihad Stadium", "Metropolitano Stadium"
]

# Helper to get players by card type
def get_players_by_card_type(card_type):
    return [p for p in FUT_PLAYERS_DATA if p.card_type == card_type]

# --- Helper to get players within OVR range
def get_players_by_ovr_range(min_ovr, max_ovr, card_types=None):
    if card_types:
        eligible_players = [p for p in FUT_PLAYERS_DATA if p.card_type in card_types and min_ovr <= p.base_ovr <= max_ovr]
    else:
        eligible_players = [p for p in FUT_PLAYERS_DATA if min_ovr <= p.base_ovr <= max_ovr]
    return eligible_players

# --- Big Clubs for FUT Start ---
BIG_CLUBS_FUT_START = [
    "Real Madrid", "Manchester City", "Bayern Munich", "Liverpool", "Paris Saint-Germain", "Barcelona"
]