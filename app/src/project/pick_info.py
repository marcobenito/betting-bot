from .betting import get_all_leagues
from app.src.utils.utils import closest_string_match, rows_to_columns, columns_to_rows
import re


class PickInfo:
    def __init__(self, text, bet_auth):
        self.image_text = text["image_text"]
        self.desc = text["description_text"]
        self.bet_auth = bet_auth
        # The pick_info dictionary is the object where all the pick info will be stored. Sport and sport id
        # are manually set as all bets will be for the same sport
        self.info = {"sport": "Tennis", "sport_id": 33}
        self.warning = ""
        self.error = ""

    def extract_from_description(self):
        """Extract relevant information from the pick description, such as stake, tournament and bet type"""
        text = self.desc
        if "live" in text:
            self.info["live_status"] = 1
        else:
            self.info["live_status"] = 0

        lines = text.split("\n")
        try:
            self.info["stake"] = float(lines[-1].split(" ")[1].split("——")[0].replace(",", "."))
        except IndexError:
            self.info["stake"] = None
            self.warning += "STAKE could not be retrieved from description \n"

        try:
            self.info["tournament"] = lines[1][1:-1]
        except IndexError:
            self.info["tournament"] = None
            self.warning += "TOURNAMENT could not be retrieved from description \n"

    def extract_from_image_text(self, stake_1=100):
        """Extract betting relevant information from the text obtained from the image, as game, odds, team or
        bet type"""

        text = self.image_text
        lines = text.split("\n")
        # If the word "Game" is inside the text, it is sure it is a live bet
        is_live = len(re.findall(" game", text)) > 0
        # is_live = 1 if next((True for line in lines if "game" in line), False) else 0
        # Home and away teams
        try:
            if is_live:
                self.info["live_status"] = 1
                match = " ".join(lines[3].split(" ")[:-1])
                sh, sa = lines[3].split(" ")[-1].split("-")  # Nr of sets of the home and away players
                self.info["current_set"] = int(sh) + int(sa) + 1
            else:
                if ":" in lines[3]:
                    match = " ".join(lines[3].split(" ")[:-4])
                elif ":" in lines[4]:
                    # The date is always 16 characters long ( ddd dd jj hh:mm), so if the match name is very long,
                    # the date can split and partially jump to the next line
                    line_4_length = len(lines[4])
                    subtract_from_line_3 = 16 - line_4_length
                    match = lines[3][:-subtract_from_line_3]
                else:
                    match = lines[3]
                self.info["current_set"] = None

            self.info["home"] = match.split(" v ")[0].strip()
            self.info["away"] = match.split(" v ")[1].strip()
        except IndexError as err:
            # There are some times where the ocr does not work completely properly
            # and reads the "v" of versus as "vy"
            self.info["home"] = None
            self.info["away"] = None
            self.error += "GAME could not be retrieved from image text \n"
            self.error += str(err) + "\n"

        # Option: this is the actual pick (which of the two teams is selected for the bet
        try:
            self.info["option"] = " ".join(lines[1].split(" ")[1:-1])
        except IndexError:
            self.info["option"] = None
            self.error += "OPTION could not be retrieved from image text \n"
        try:
            if self.info["home"] in self.info["option"]:
                self.info["option_team"] = "home"
            elif self.info["away"] in self.info["option"]:
                self.info["option_team"] = "away"
            else:
                self.info["option_team"] = "home"
        except TypeError:
            self.error += "Team could not be retrieved from image text \n"
            self.error += "TEXT: \n"
            self.error += text
            self.info["option_team"] = None

        # Bet (e.g. match winner)
        try:
            self.info["bet"] = lines[2]
        except IndexError:
            self.info["bet"] = None
            self.error += "BET could not be retrieved from image text \n"

        # If stake info has not been extracted from text, derive it from the bet quantity
        if self.info["stake"] is None:
            try:
                # The last line (lines[-1]) is an empty line, as the text finishes with \n
                bet_quantity = lines[-2].split(",")[0]
                stake = int(bet_quantity) / stake_1
                self.info["stake"] = stake
            except IndexError:
                self.error += "STAKE could not be retrieved from image text \n"

    def select_bet(self):
        """The picks provided by the tipster are from bet365, and the bets will be placed on Pinnacle using the
        ps3838 API. That's why the info read from the pick has to be mapped to the terms from ps3838"""

        # First step is to obtain the correct bet365 bet using the Levenshtein Distance, because the
        # OCR will not be 100% accurate and sometime will misread some letter (e.g Ganarea el encuentro
        # instead of Ganare el encuentro)

        options = ["ganara el encuentro", "ganador del encuentro", "apuestas al set", "jugador - ganara 1 set",
                   "set actual - ganador", "handicap - 2 opciones - juegos ganados", "ganador",
                   "total de juegos - 2 opciones", "encuentro - handicap"]

        string = self.info["bet"]

        # Calculate the Jaro similarity index to all the options and take the biggest one
        closest_league_match = closest_string_match(string, options, th=0.85)
        if closest_league_match["value"] is not None:
            self.info["bet"] = closest_league_match["value"]
        else:
            self.error += "The bet {} is not within the possible options \n".format(self.info["bet"])
            self.info["bet"] = None

    def map_tournament(self):
        """Map the tournament provided in the pick description to the correct one within the ps3838 API"""
        if self.info["tournament"] is None:
            return

        string = self.info["tournament"]

        # Import all the leagues from the ps3838 API
        sport_id = 33
        # my_bet = Betting(auth=(username, password))
        leagues = rows_to_columns(get_all_leagues(sport_id, auth=self.bet_auth))
        league_names = list(set([league.split(" - ")[0] for league in leagues["name"]]))

        # Define some mapping points (some tournaments must be mapped manually), as the Levenshtein Distance
        # is not enough for finding the best match (e.g Praga is the spanish word for Prague, but it will
        # have a better match to the portuguese city of Braga)
        mapping = {"queens": "london", "marsella": "marseille", "copa davis": "davis cup",
                   "burdeos": "bordeaux", "jjoo": "olympics", "roland garros": "atp french open",
                   "ginebra": "geneva", "san petersburgo": "st. petersburg", "open australia": "australian open",
                   "londres": "london", "napoles": "napoli", "praga": "prague", "amberes": "antwerp",
                   "roseto": "roseto degli abruzzi", "us open wta": "wta us open", "varsovia": "warsaw",
                   "french open": "atp french open"}

        # Remove Fase previa and F. previa from the string
        string = string.lower()
        string = string.replace("fase previa", "")
        string = string.replace("f. previa", "")
        string = string.replace("fase prev.", "")

        # Replace CHALL or CHALLENGER or CH by Atp Challenger
        string = string.split(" ")
        if string[0] in ["challenger", "chall", "ch"]:
            string[0] = "atp challenger"
        string = " ".join(string)

        # Replace specific tournaments by its correct name following the mapping dic
        for key in mapping.keys():
            if key in string:
                string = string.replace(key, mapping[key])
                break

        # Strip string
        string = string.strip()

        # Calculate the Jaro similarity index to all the options and take the ps3838 league with the
        # highest score
        closest_league_match = closest_string_match(string, league_names, th=0.5)["value"]

        if closest_league_match is not None:
            league = list(filter(lambda x: (closest_league_match in x["name"]) &
                                           (x["has_offerings"] is True), columns_to_rows(leagues)))

            if len(league) > 0:
                self.info["tournament"] = closest_league_match
            else:
                self.error += "The tournament {} is not running at the moment \n".format(closest_league_match)
                self.info["tournament"] = None
        else:
            self.warning += "The tournament {} could not be found \n".format(string)
            self.info["tournament"] = None

    def map_bet(self):
        """Use the information about the bet extracted to obtain the necessary parameters for finding the correct
        line in the ps3838 API"""
        grand_slams = ["atp australian open", "atp french open", "atp wimbledon", "atp us open"]

        bet = self.info["bet"]
        if bet is None:
            return

        if bet.lower() in ["ganara el encuentro", "ganador del encuentro"]:
            self.info["bet_type"] = "MONEYLINE"
            self.info["resulting_unit"] = "Sets"  # previously Regular
            self.info["period"] = 0
            self.info["handicap"] = 0

        elif bet.lower() == "set actual - ganador":
            # It is moneyline on live. Now it is related to the period. So option will be PlayerName and period will be
            # the set
            self.info["bet_type"] = "MONEYLINE"
            self.info["resulting_unit"] = "Sets"  # previously Regular
            self.info["period"] = self.info["current_set"]
            # self.info["option"] += " To Win Set"  # Previously. period was 0 and option was this
            self.info["handicap"] = 0

        elif bet.lower() == "jugador - ganara un set":
            # Team sets handicap (e.g. Player 1 +1.5 Sets)
            self.info["bet_type"] = "SPREAD"
            self.info["resulting_unit"] = "Sets"
            self.info["period"] = 0
            if self.info["tournament"] in grand_slams:
                self.info["handicap"] = "+2.5"
            else:
                self.info["handicap"] = "+1.5"
            # self.info["option"] += " ({} Sets)".format(self.info["handicap"])

        elif bet.lower() == "apuestas al set":
            # Pre match team sets handicap (e.g. Player 1 -1.5 Sets)
            self.info["bet_type"] = "SPREAD"
            self.info["resulting_unit"] = "Sets"
            self.info["period"] = 0

            # Extract the winning difference (2 or 3 sets)
            diff = self.info["option"].lower().split("ganara")[1].split("-")[0].strip()
            # Calculate the handicap by subtracting 0.5
            hdp = int(diff) - 0.5
            hdp = "-{}".format(str(hdp))
            self.info["handicap"] = "{}".format(str(hdp))
            # Unfortunately, the API is changing things related to bet type. Currently, resulting unit can only be
            # Sets or Games. For sets, sometimes the event name is PlayerName (Sets) and sometimes only PlayerName.
            # As the Jaro Similarity will allow to match PlayerName to both PlayerName (Sets) and PlayerName, our
            # option will just be the name of the player. Be careful as this can change in the near future again
            self.info["option"] = self.info[self.info["option_team"]]

        elif bet.lower() == "handicap - 2 opciones - juegos ganados":
            # Pre match team games handicap bet (e.g. Player1 +5.5 games)
            self.info["bet_type"] = "SPREAD"
            self.info["resulting_unit"] = "Games"
            self.info["period"] = 0

            # Extract the handicap
            player = self.info[self.info["option_team"]]
            hdp = float(self.info["option"].split(player)[1].strip())
            self.info["handicap"] = hdp
            self.info["option"] += " (Games)"

        elif bet.lower() == "total de juegos - 2 opciones":
            # Pre match total games handicap bet (e.g. +35.5 games)
            self.info["bet_type"] = "TOTAL_POINTS"
            self.info["resulting_unit"] = "Games"
            self.info["period"] = 0

            # Option is in the format (Mas de 35.5 or menos de 35.5)
            hdp = float(self.info["option"].split("de")[1].strip())
            sign = "OVER" if "mas" in self.info["option"] else "UNDER"
            self.info["handicap"] = float(hdp)
            self.info["side"] = sign
