import random

# Game Constants

# --- Player Data ---
POSITIONS = ["GK", "CB", "LB", "RB", "CMF", "AMF", "LWF", "RWF", "CF", "SS", "RW", "LW", "CAM", "CDM", "ST"]

ATTRIBUTE_WEIGHTS = {
    "GK": {"goalkeeping": 0.5, "reflexes": 0.4, "handling": 0.3, "kicking": 0.2, "positioning": 0.3, "jumping": 0.1},
    "CB": {"defense": 0.5, "tackling": 0.4, "heading": 0.3, "strength": 0.3, "interceptions": 0.3, "speed": 0.2},
    "LB": {"defense": 0.4, "tackling": 0.3, "speed": 0.4, "crossing": 0.3, "dribbling": 0.2, "stamina": 0.3},
    "RB": {"defense": 0.4, "tackling": 0.3, "speed": 0.4, "crossing": 0.3, "dribbling": 0.2, "stamina": 0.3},
    "CMF": {"passing": 0.4, "dribbling": 0.3, "control": 0.3, "stamina": 0.3, "tackling": 0.2, "vision": 0.3},
    "AMF": {"passing": 0.4, "dribbling": 0.4, "shooting": 0.3, "vision": 0.4, "control": 0.3, "speed": 0.2},
    "LWF": {"speed": 0.4, "dribbling": 0.4, "shooting": 0.3, "crossing": 0.3, "control": 0.3, "finishing": 0.2},
    "RWF": {"speed": 0.4, "dribbling": 0.4, "shooting": 0.3, "crossing": 0.3, "control": 0.3, "finishing": 0.2},
    "CF": {"shooting": 0.5, "finishing": 0.4, "heading": 0.3, "strength": 0.3, "speed": 0.3, "positioning": 0.3},
    "SS": {"shooting": 0.4, "passing": 0.3, "dribbling": 0.4, "vision": 0.3, "speed": 0.3, "finishing": 0.3},
    "RW": {"speed": 0.45, "dribbling": 0.45, "shooting": 0.35, "crossing": 0.35, "control": 0.35, "finishing": 0.25},
    "LW": {"speed": 0.45, "dribbling": 0.45, "shooting": 0.35, "crossing": 0.35, "control": 0.35, "finishing": 0.25},
    "CAM": {"passing": 0.45, "dribbling": 0.45, "shooting": 0.35, "vision": 0.45, "control": 0.35, "speed": 0.25},
    "CDM": {"defense": 0.45, "tackling": 0.45, "interceptions": 0.45, "strength": 0.35, "passing": 0.35, "stamina": 0.35},
    "ST": {"shooting": 0.55, "finishing": 0.45, "heading": 0.35, "strength": 0.35, "speed": 0.35, "positioning": 0.35}
}

# --- Expanded Name Databases ---

# General names (fallbacks or for diverse smaller countries)
FIRST_NAMES = [
    "John", "Michael", "David", "James", "Robert", "William", "Charles", "Joseph", "Thomas", "Christopher",
    "Daniel", "Paul", "Mark", "Donald", "George", "Kenneth", "Steven", "Edward", "Brian", "Ronald",
    "Anthony", "Kevin", "Jason", "Jeff", "Gary", "Timothy", "Larry", "Frank", "Scott", "Eric",
    "Stephen", "Andrew", "Raymond", "Gregory", "Joshua", "Jerry", "Dennis", "Walter", "Patrick", "Peter",
    "Harold", "Douglas", "Henry", "Carl", "Arthur", "Ryan", "Roger", "Joe", "Juan", "Jack",
    "Albert", "Jonathan", "Justin", "Terry", "Gerald", "Keith", "Samuel", "Willie", "Ralph", "Lawrence",
    "Nicholas", "Matthew", "Boris", "Dimitri", "Ivan", "Sergei", "Vladimir", "Alexei", "Pierre", "Jean-Luc",
    "François", "Antoine", "Henri", "Michel", "Louis", "Marc", "Philippe", "Christophe", "Sébastien", "Olivier",
    "Carlos", "Miguel", "Jose", "Fernando", "Ricardo", "Manuel", "Javier", "Diego", "Luis", "Rafael",
    "Juan", "Pedro", "Pablo", "Jorge", "Andres", "Gabriel", "Adrian", "Hector", "Sergio", "Antonio",
    "Alessandro", "Marco", "Giuseppe", "Francesco", "Giovanni", "Roberto", "Andrea", "Stefano", "Simone", "Luca",
    "Paolo", "Fabio", "Daniele", "Christian", "Matteo", "Federico", "Enzo", "Vincenzo", "Massimo", "Lorenzo",
    "Jan", "Thomas", "Michael", "Andreas", "Stefan", "Markus", "Christian", "Martin", "Frank", "Jörg",
    "Peter", "Robert", "Dirk", "Thorsten", "Klaus", "Uwe", "Wolfgang", "Ralf", "Bernd", "Guenter",
    "Björn", "Erik", "Lars", "Olaf", "Sven", "Magnus", "Anders", "Jonas", "Fredrik", "Carl",
    "Mohamed", "Ahmed", "Ali", "Omar", "Youssef", "Khalid", "Mustafa", "Abdullah", "Hassan", "Ibrahim",
    "Chinedu", "Emeka", "Oluwafemi", "Adekunle", "Nonso", "Bayo", "Tope", "Kunle", "Nnamdi", "Ikenna", "Obinna", "Chukwuemeka", "Olumide", "Ayodeji", "Femi", "Tunde", "Segun", "Dapo", "Jide", "Kolawole",
    "Musa", "Kwame", "Kofi", "Yaw", "Papa", "Akua", "Ama", "Esi", "Adwoa", "Yaa", "Kojo", "Kwabena", "Kwaku", "Kwasi", "Kweku", "Kwadwo", "Kwame", "Kofi", "Yaw", "Kojo",
    "Katongole", "Mugisha", "Okello", "Otim", "Wamala", "Nsubuga", "Ssenyonga", "Lubega", "Kato", "Kiggundu", "Mwesigwa", "Kintu", "Ssemwanga", "Lwanga", "Ssekandi", "Kyagulanyi", "Bwambale", "Tumusiime", "Rwothomio", "Odong",
    "Kipkorir", "Chebet", "Wanjiru", "Njoroge", "Kamau", "Ochieng", "Odhiambo", "Akinyi", "Mwangi", "Kimani", "Maina", "Kiplagat", "Cheruiyot", "Rotich", "Korir", "Ndungu", "Ngugi", "Wambua", "Mutua", "Githuku",
    "Sipho", "Thabo", "Lukhanyo", "Bongani", "Nkosi", "Zola", "Xolani", "Mpho", "Sizwe", "Sandile", "Khaya", "Lungelo", "Katlego", "Lebo", "Neo", "Tebogo", "Kagiso", "Oupa", "Jabu", "Zwane",
    "Dlamini", "Khumalo", "Zulu", "Mkhize", "Sithole", "Ndlovu", "Ngcobo", "Mthembu", "Khoza", "Gwala", "Ncube", "Biyela", "Mhlongo", "Sibisi", "Hlongwane", "Gumede", "Cele", "Nxumalo", "Moyo", "Mabena",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes",
    "Stewart", "Morris", "Morgan", "Cooper", "Bailey", "Reed", "Cook", "Bell", "Kelly", "Howard",
    "Ward", "Cox", "Diaz", "Peterson", "Gray", "Ramirez", "James", "Watson", "Brooks", "Bennett",
    "Wood", "Barnes", "Ross", "Henderson", "Coleman", "Jenkins", "Perry", "Powell", "Long", "Patterson",
    "Hughes", "Flores", "Washington", "Butler", "Simmons", "Foster", "Gonzales", "Bryant", "Alexander", "Russell",
    "Grigoriev", "Smirnov", "Petrov", "Sokolov", "Popov", "Kuznetsov", "Volkov", "Morozov", "Novikov", "Kozlov",
    "Dubois", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Leroy", "Moreau", "Simon",
    "Laurent", "Lefevre", "Roux", "Garcia", "Martin", "Bertrand", "Roussel", "Lopez", "Fournier", "Blanc",
    "Rossi", "Ferrari", "Russo", "Bianchi", "Mancini", "Esposito", "Romano", "Gallo", "Costa", "Fontana",
    "Ricci", "Bruno", "Conti", "Marino", "Greco", "Vitale", "Lombardi", "Barbieri", "Giordano", "Galli",
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
    "Schäfer", "Koch", "Richter", "Bauer", "Klein", "Wolf", "Neumann", "Schwarz", "Braun", "Hofmann",
    "Davies", "Evans", "Jones", "Williams", "Morgan", "Lewis", "Roberts", "Thomas", "Wright", "Hughes",
    "Johnson", "Brown", "Wilson", "Robinson", "Green", "Baker", "White", "Edwards", "Taylor", "Hall",
    "Mohammed", "Khan", "Ali", "Singh", "Patel", "Ahmed", "Syed", "Shah", "Begum", "Chowdhury",
    "Okafor", "Okoro", "Chukwu", "Nwoye", "Eze", "Igbo", "Obi", "Ugochukwu", "Anyanwu", "Ekeh", "Okoye", "Ibrahim", "Musa", "Audu", "Abdullahi", "Usman", "Dikko", "Sani", "Bello", "Danladi",
    "Oluoch", "Otieno", "Wanjala", "Kemei", "Chepkoech", "Cherono", "Kiplagat", "Mutiso", "Wambui", "Njuguna", "Opiyo", "Ochola", "Omondi", "Achieng", "Anyango", "Kerubo", "Moraa", "Muli", "Ngugi", "Wafula",
    "Moyo", "Ndlovu", "Sithole", "Nkosi", "Zulu", "Khumalo", "Mhlongo", "Dlamini", "Sibanda", "Gumbo", "Ncube", "Bhebhe", "Nkomo", "Mabena", "Gumede", "Cele", "Nxumalo", "Hlongwane", "Ngcobo", "Sibisi",
    "Tumwesigye", "Mugabi", "Nalwoga", "Nakalema", "Katumba", "Kizza", "Namukasa", "Nankya", "Ssebuwufu", "Lubyayi", "Mayanja", "Ssali", "Kyomuhendo", "Mbabazi", "Muhumuza", "Akello", "Achan", "Adong", "Opio", "Ocen",
]

COUNTRIES = [
    "Nigeria", "Uganda", "Kenya", "South Africa", # Heavily biased home league countries
    "England", "Spain", "France", "Germany", "Italy", "Portugal", "Netherlands", "Belgium", # European for international
    "Brazil", "Argentina", "Mexico", "USA", "Canada", # Americas
    "Egypt", "Ghana", "Ivory Coast", "Cameroon", # More African
    "Japan", "South Korea", "China", # Asia
    "Australia", "New Zealand", # Oceania
    "Croatia", "Serbia", "Poland", "Sweden", "Denmark", "Norway", "Scotland", "Ireland", # More European
    "Colombia", "Chile", "Uruguay", "Peru", # More South American
    "Algeria", "Morocco", "Tunisia", "Senegal", # North/West Africa
    "Russia", "Ukraine", "Turkey", "Greece", "Switzerland", "Austria" # Eastern/Central Europe
]

NATIONAL_FIRST_NAMES = {
    "Nigeria": ["Chinedu", "Emeka", "Oluwafemi", "Adekunle", "Nonso", "Bayo", "Tope", "Kunle", "Nnamdi", "Ikenna", "Obinna", "Chukwuemeka", "Olumide", "Ayodeji", "Femi", "Tunde", "Segun", "Dapo", "Jide", "Kolawole", "Ibrahim", "Musa", "Audu", "Abdullahi", "Usman", "Dikko", "Sani", "Bello", "Danladi", "Aminu", "Garba", "Jibrin", "Mohammed", "Umaru", "Yakubu", "Yusuf"],
    "Uganda": ["Katongole", "Mugisha", "Okello", "Otim", "Wamala", "Nsubuga", "Ssenyonga", "Lubega", "Kato", "Kiggundu", "Mwesigwa", "Kintu", "Ssemwanga", "Lwanga", "Ssekandi", "Kyagulanyi", "Bwambale", "Tumusiime", "Rwothomio", "Odong", "Akello", "Achan", "Adong", "Opio", "Ocen", "Mbabazi", "Namukasa", "Nakalema", "Nankya", "Kyomuhendo"],
    "Kenya": ["Kipkorir", "Chebet", "Wanjiru", "Njoroge", "Kamau", "Ochieng", "Odhiambo", "Akinyi", "Mwangi", "Kimani", "Maina", "Kiplagat", "Cheruiyot", "Rotich", "Korir", "Ndungu", "Ngugi", "Wambua", "Mutua", "Githuku", "Omondi", "Opiyo", "Achieng", "Anyango", "Kerubo", "Moraa"],
    "South Africa": ["Sipho", "Thabo", "Lukhanyo", "Bongani", "Nkosi", "Zola", "Xolani", "Mpho", "Sizwe", "Sandile", "Khaya", "Lungelo", "Katlego", "Lebo", "Neo", "Tebogo", "Kagiso", "Oupa", "Jabu", "Zwane", "Kgosi", "Tshepo", "Rethabile", "Bokang", "Mpumelelo", "Nokwanda", "Thandeka", "Lerato", "Zanele", "Busisiwe"],
    "England": ["Harry", "George", "Thomas", "James", "William", "Jacob", "Noah", "Leo", "Oscar", "Freddie", "Archie", "Arthur", "Jack", "Charlie", "Oliver", "Alfie", "Ethan", "Finley", "Henry", "Max"],
    "Spain": ["Alejandro", "Daniel", "Pablo", "Hugo", "Álvaro", "Manuel", "Lucas", "David", "Javier", "Marco", "Adrian", "Diego", "Sergio", "Carlos", "José", "Jorge", "Mario", "Juan", "Pedro", "Iker"],
    "France": ["Lucas", "Gabriel", "Léo", "Louis", "Arthur", "Adam", "Hugo", "Paul", "Raphaël", "Jules", "Noah", "Mohamed", "Ethan", "Tom", "Théo", "Nathan", "Liam", "Enzo", "Gabin", "Sacha"],
    "Germany": ["Noah", "Leon", "Paul", "Ben", "Louis", "Luca", "Emil", "Lian", "Jonas", "Felix", "Maximilian", "Finn", "Henry", "Anton", "Moritz", "Jakob", "Oskar", "Leo", "Matteo", "David"],
    "Italy": ["Leonardo", "Francesco", "Alessandro", "Lorenzo", "Andrea", "Mattia", "Riccardo", "Gabriele", "Tommaso", "Davide", "Giuseppe", "Antonio", "Federico", "Christian", "Samuele", "Giovanni", "Marco", "Luca", "Simone", "Pietro"],
    "Portugal": ["João", "Francisco", "Martim", "Santiago", "Tomás", "Lucas", "Gabriel", "Afonso", "Rodrigo", "Miguel", "Guilherme", "Gonçalo", "Dinis", "Salvador", "Vicente", "Diogo", "Duarte", "Eduardo", "Lourenço", "Pedro"],
    "Brazil": ["Gabriel", "Arthur", "Miguel", "Heitor", "Théo", "Davi", "Bernardo", "Samuel", "João", "Pedro", "Lucas", "Gustavo", "Rafael", "Felipe", "Matheus", "Enzo", "Guilherme", "Nicolas", "Lorenzo", "Daniel"],
    "Argentina": ["Santiago", "Mateo", "Valentino", "Benjamín", "Joaquín", "Thiago", "Agustín", "Tomás", "Lautaro", "Facundo", "Juan", "Manuel", "Lucas", "Francisco", "Ignacio", "Matías", "Nicolás", "Máximo", "Felipe", "Bautista"],
    "Mexico": ["Santiago", "Sebastián", "Matías", "Emiliano", "Diego", "Miguel", "Alexander", "Leonardo", "Daniel", "Mateo", "Liam", "Gael", "José", "Carlos", "Juan", "Manuel", "Ricardo", "Fernando", "Eduardo", "Alejandro"],
    "USA": ["Noah", "Liam", "Oliver", "Elijah", "James", "William", "Benjamin", "Lucas", "Henry", "Theodore", "Jackson", "Samuel", "Sebastian", "David", "Joseph", "Matthew", "Owen", "Daniel", "Gabriel", "Logan"],
    "Ghana": ["Kwame", "Kofi", "Yaw", "Papa", "Kojo", "Kwabena", "Kwaku", "Kwasi", "Kweku", "Kwadwo", "Akua", "Ama", "Esi", "Adwoa", "Yaa", "Abena", "Afia", "Araba", "Efe", "Dede"],
    "Egypt": ["Mohamed", "Ahmed", "Ali", "Omar", "Youssef", "Khalid", "Mustafa", "Abdullah", "Hassan", "Ibrahim", "Mahmoud", "Tarek", "Karim", "Amr", "Sami", "Hossam", "Mido", "Essam", "Wael", "Sherif"],
    "Japan": ["Ren", "Haruto", "Sota", "Yuto", "Hinata", "Shota", "Kaito", "Riku", "Taiga", "Ryota", "Yuki", "Daiki", "Tsubasa", "Kazuki", "Koji", "Masaki", "Kenji", "Hiroshi", "Takumi", "Yuma"],
    "South Korea": ["Minjun", "Seojun", "Dohyun", "Eunwoo", "Siwoo", "Jimin", "Junjun", "Hajun", "Yeongu", "Jisu", "Hyunwoo", "Jaehyun", "Woo-jin", "Chan-woo", "Geon-woo", "Hwan-hee", "Jae-ho", "Min-woo", "Sang-hyun", "Sung-ho"],
}

NATIONAL_LAST_NAMES = {
    "Nigeria": ["Okafor", "Okoro", "Chukwu", "Nwoye", "Eze", "Igbo", "Obi", "Ugochukwu", "Anyanwu", "Ekeh", "Okoye", "Ibrahim", "Musa", "Audu", "Abdullahi", "Usman", "Dikko", "Sani", "Bello", "Danladi", "Adewale", "Adeyemi", "Akintola", "Dike", "Egbuna", "Nwankwo", "Okonkwo", "Olawale", "Oyewole", "Uzodinma"],
    "Uganda": ["Tumwesigye", "Mugabi", "Nalwoga", "Nakalema", "Katumba", "Kizza", "Namukasa", "Nankya", "Ssebuwufu", "Lubyayi", "Mayanja", "Ssali", "Kyomuhendo", "Mbabazi", "Muhumuza", "Akello", "Achan", "Adong", "Opio", "Ocen", "Mugisha", "Okello", "Otim", "Wamala", "Nsubuga", "Ssenyonga", "Lubega", "Kato", "Kiggundu", "Mwesigwa"],
    "Kenya": ["Oluoch", "Otieno", "Wanjala", "Kemei", "Chepkoech", "Cherono", "Kiplagat", "Mutiso", "Wambui", "Njuguna", "Opiyo", "Ochola", "Omondi", "Achieng", "Anyango", "Kerubo", "Moraa", "Muli", "Ngugi", "Wafula", "Kamau", "Kimani", "Maina", "Mwangi", "Njoroge", "Ndungu", "Rotich", "Korir", "Kipkemboi", "Cheruiyot"],
    "South Africa": ["Moyo", "Ndlovu", "Sithole", "Nkosi", "Zulu", "Khumalo", "Mhlongo", "Dlamini", "Sibanda", "Gumbo", "Ncube", "Bhebhe", "Nkomo", "Mabena", "Gumede", "Cele", "Nxumalo", "Hlongwane", "Ngcobo", "Sibisi", "Pretorius", "van der Merwe", "Botha", "Du Plessis", "Venter", "Naidoo", "Pillay", "Coetzee", "Meyer", "Jordaan"],
    "England": ["Smith", "Jones", "Williams", "Brown", "Taylor", "Wilson", "Davies", "Evans", "Thomas", "Johnson", "Walker", "Roberts", "Wright", "Robinson", "Thompson", "White", "Hughes", "Green", "Hall", "Lewis"],
    "Spain": ["Garcia", "Rodriguez", "Fernandez", "Gonzalez", "Lopez", "Martinez", "Sanchez", "Perez", "Martin", "Gomez", "Jimenez", "Ruiz", "Hernandez", "Diaz", "Moreno", "Muñoz", "Alvarez", "Romero", "Alonso", "Gutierrez"],
    "France": ["Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Laurent", "Simon", "Michel", "Lefevre", "Leroy", "Roux", "David", "Bertrand", "Fournier", "Girard", "Dupont"],
    "Germany": ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann", "Schäfer", "Koch", "Richter", "Bauer", "Klein", "Wolf", "Neumann", "Schwarz", "Braun", "Hofmann"],
    "Italy": ["Rossi", "Ferrari", "Russo", "Bianchi", "Mancini", "Esposito", "Romano", "Gallo", "Costa", "Fontana", "Ricci", "Bruno", "Conti", "Marino", "Greco", "Vitale", "Lombardi", "Barbieri", "Giordano", "Galli"],
    "Portugal": ["Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa", "Rodrigues", "Martins", "Jesus", "Sousa", "Fernandes", "Gonçalves", "Gomes", "Lopes", "Marques", "Alves", "Almeida", "Ribeiro", "Pinto", "Carvalho"],
    "Brazil": ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Fernandes", "Rodrigues", "Alves", "Ferreira", "Carvalho", "Pereira", "Gomes", "Ribeiro", "Martins", "Costa", "Melo", "Barbosa", "Araújo", "Dias", "Nascimento"],
    "Argentina": ["Gonzalez", "Rodriguez", "Fernandez", "Lopez", "Martinez", "Diaz", "Perez", "Sanchez", "Romero", "Garcia", "Acosta", "Benitez", "Ruiz", "Gomez", "Torres", "Ramirez", "Flores", "Rivero", "Moyano", "Ortiz"],
    "Mexico": ["Hernandez", "Garcia", "Martinez", "Lopez", "Gonzalez", "Rodriguez", "Perez", "Sanchez", "Ramirez", "Cruz", "Flores", "Gomez", "Morales", "Reyes", "Jimenez", "Ruiz", "Rivera", "Diaz", "Torres", "Moreno"],
    "USA": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"],
    "Ghana": ["Mensah", "Owusu", "Adjei", "Danquah", "Kofi", "Agyemang", "Boateng", "Frimpong", "Appiah", "Nkrumah", "Osei", "Sarfo", "Opoku", "Ntow", "Baah", "Annan", "Asamoah", "Gyan", "Partey", "Ayew"],
    "Egypt": ["Mohamed", "Ahmed", "Ali", "Hassan", "Ibrahim", "Mahmoud", "Abdullah", "Hussein", "Sayed", "El-Sayed", "Gaber", "Khalifa", "Mansour", "Metwally", "Ragab", "Ramadan", "Sobhy", "Taha", "Yassin", "Zakaria"],
    "Japan": ["Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Nakamura", "Kobayashi", "Yamamoto", "Kato", "Yoshida", "Yamada", "Sasaki", "Matsumoto", "Inoue", "Kimura", "Hayashi", "Shimizu", "Mori", "Ikeda"],
    "South Korea": ["Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Cho", "Yoon", "Jang", "Lim", "Han", "Oh", "Shin", "Seo", "Kwon", "Hwang", "Ahn", "Song", "Hong", "Ryu"],
}


# General countries (for initial assignment, can be refined)
COUNTRIES = list(NATIONAL_FIRST_NAMES.keys()) + [
    "Netherlands", "Belgium", "Austria", "Switzerland", "Sweden", "Norway", "Denmark", "Scotland", "Ireland",
    "Croatia", "Serbia", "Poland", "Ukraine", "Russia", "Turkey", "Greece",
    "Colombia", "Chile", "Uruguay", "Peru", "Venezuela",
    "Ivory Coast", "Cameroon", "Algeria", "Morocco", "Tunisia", "Senegal", "Mali", "DR Congo",
    "China", "India", "Indonesia", "Thailand", "Malaysia", "Vietnam",
    "Australia", "New Zealand"
]
COUNTRIES = sorted(list(set(COUNTRIES))) # Remove duplicates and sort

# --- Trainer Data ---
TRAINER_TIERS = {
    "Bronze": {"cost": 500_000, "boost": 1},
    "Silver": {"cost": 1_500_000, "boost": 2},
    "Gold": {"cost": 3_000_000, "boost": 3},
    "Platinum": {"cost": 5_000_000, "boost": 4},
}