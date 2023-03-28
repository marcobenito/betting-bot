import re

class BetInfo:
    def __init__(self, text):
        self.raw_text = text
        self.text = []
        # Initialize the attributes dictionary called info
        self.info = {"option": "", "odd": "", "bet": "", "game": "", "sport": "",
                     "sport_id": ""}

    def extract_bet_info(self):
        # The first step is to extract the sport (event) info
        self.get_sport_type()

        # Clean the text for deleting white lines
        self.raw_text = self.raw_text.split("\n")
        for i, line in enumerate(self.raw_text):
            if not re.match(r'^\s*$', line):
                self.text.append(line)

        # I have to identify the type of bet. For doing this, I will read the first line of the picture,
        # to know if it's a "simple" or a "double" bet
        if "Sencillas" in self.text[0]:
            if "Crear apuesta" in self.text:
                self.single_bet_combined()
            else:
                self.single_bet()
        elif "Dobles" in self.text[0]:
            self.multiple_bet()

        return self.info

    def get_sport_type(self):
        """This function reads the text and returns the sport and sport id of the bet
        :param text: the text of the bet
        :return sport: the name of the sport
        :return sport_id: the id of the sport, as per the Betfair documentation"""

        sports = {"Soccer": "⚽", "Tennis": "🎾", "Basketball": "🏀", "Handball": "🤾‍♂"}
        sports_id = {"Soccer": "29", "Tennis": "33", "Basketball": "4", "Handball": "18"}
        sport, sport_id = "", ""

        for key in sports.keys():
            if sports[key] in self.raw_text:
                sport = key
                sport_id = sports_id[key]
                break
        self.info["sport"] = sport
        self.info["sport_id"] = sport_id
        return sport, sport_id

    def single_bet(self):
        for i, line in enumerate(self.text):
            # My specific trigger is the © character. This means that the line containing the bet
            # info is the one starting with this character and the two following, in case of a single bet
            if "©" in line:
                self.info["option"] = " ".join(line[2:].split(" ")[:-1])
                self.info["odd"] = line.split(" ")[-1]
                self.info["bet"] = self.text[i + 1]
                self.info["game_date"] = self.text[i + 2]
                break
        self.info["game"] = " ".join(self.info["game_date"].split(" ")[:-4])
        self.info["date"] = " ".join(self.info["game_date"].split(" ")[-4:])
        self.info["home"] = self.info["game"].split(" v ")[0].strip()
        self.info["away"] = self.info["game"].split(" v ")[1].strip()

        # Define relevant information for placing a bet
        # Define Type of bet
        if "Resultado final" in self.info["bet"]:
            self.info["bet_type"] = "MONEYLINE"
        elif "Otras Opciones" in self.info["bet"] or "Handicap" in self.info["bet"]:
            if self.info["home"] in self.info["option"] or self.info["away"] in self.info["option"]:
                self.info["bet_type"] = "TEAM_TOTAL_POINTS"
            else:
                self.info["bet_type"] = "TOTAL_POINTS"
        elif "Ganara el encuentro" in self.info["bet"]:
            self.info["bet_type"] = "MONEYLINE"
        else:
            self.info["bet_type"] = ""

        # Get the handicap if applied
        if "TOTAL_POINTS" in self.info["bet_type"]:
            self.info["handicap"] = self.info["option"].split(" ")[-1]

        if "Mas de" in self.info["option"]:
            self.info["side"] = "OVER"
        elif "Menos de" in self.info["option"]:
            self.info["side"] = "UNDER"

        # Get the chosen team
        if self.info["home"] in self.info["option"]:
            self.info["team"] = "Team1"
        elif self.info["away"] in self.info["option"]:
            self.info["team"] = "Team2"





    def single_bet1(self):
        for i, line in enumerate(self.text):
            # My specific trigger is the © character. This means that the line containing the bet
            # info is the one starting with this character and the two following, in case of a single bet
            if line[-1] == "x":
                self.info["option"] = " ".join(line[2:].split(" ")[:-1])
                self.info["odd"] = line.split(" ")[-1]
                self.info["bet"] = self.text[i + 1]
                self.info["game"] = line[4, -2]
                break

    def single_bet_combined(self):
        pass

    def multiple_bet(self):
        pass

    def translate_bet_info(self):
        pass
