import requests
import time
import uuid
from datetime import datetime, timedelta
from app.src.utils.utils import closest_string_match, rows_to_columns, columns_to_rows


class Betting:
    def __init__(self, config, params={}):
        self.auth = (config["username"], config["password"])
        self.max_stake = config["max_stake"]
        self.bankroll = config["bankroll"]
        self.headers = {"Accept": "application/json",
                        "Content-Type": "application/json"}
        self.user_info = params
        self.bet_info = {}
        self.required_parameters = []
        self.error = ""
        self.warning = ""

        # If there are params, check if all of them have been passed and initialize some parameters
        # If there are no params, some methods as get_all_leagues, get_all_events or get_sport_id can still be used
        if params != {}:
            self.init_params()

    def init_params(self):
        """Initialize some parameters of the bet_info dictionary coming from the user parameters. If any of
        the necessary parameters are not given, an error message will be shown and the process broken"""

        required_params = ["sport", "bet_type", "resulting_unit", "option"]
        # Add some required parameters depending on the bet type
        if "bet_type" in self.user_info.keys():
            if self.user_info["bet_type"] in ["SPREAD", "TEAM_TOTAL_POINTS", "TOTAL_POINTS"]:
                required_params.append("handicap")
            if self.user_info["bet_type"] in ["SPREAD", "TEAM_TOTAL_POINTS", "MONEYLINE"]:
                required_params.append("option_team")
            if self.user_info["bet_type"] in ["TOTAL_POINTS ", "TEAM_TOTAL_POINTS"]:
                required_params.append("side")

        self.required_parameters = required_params

        # Check if there are any missing parameters, and throw a warning
        missing_params = list(filter(lambda x: x not in self.user_info.keys(), required_params))
        if len(missing_params) > 0:
            self.error += "The params {} are missing".format(", ".join(missing_params))
            return

        # Get sport id
        sport = get_sport_id(sport=self.user_info["sport"], auth=self.auth)
        self.bet_info["sport_id"] = sport["sport_id"]
        self.bet_info["sport_name"] = sport["sport_name"]
        # Get team
        if "option_team" in self.user_info.keys():
            if self.user_info["option_team"] == "home":
                self.bet_info["team"] = "Team1"
            elif self.user_info["option_team"] == "away":
                self.bet_info["team"] = "Team2"
        else:
            self.bet_info["team"] = ""
        # Get bet type
        self.bet_info["bet_type"] = self.user_info["bet_type"]
        # Get handicap
        if "handicap" in self.user_info.keys():
            self.bet_info["handicap"] = self.user_info["handicap"]
        else:
            self.bet_info["handicap"] = 0
        # Get side
        if "side" in self.user_info.keys():
            self.bet_info["side"] = self.user_info["side"]
        else:
            self.bet_info["side"] = ""
        # Get stake
        if "stake" in self.user_info.keys():
            self.bet_info["stake"] = self.user_info["stake"]
        else:
            self.bet_info["stake"] = 0

    def set_fixtures(self):
        """This method calls the PS3838 betting API and gets the league id and name, as well as the event id"""

        try:
            # Get all possible events (if a league is given, all events from that
            league_filter = self.user_info["tournament"] if "tournament" in self.user_info.keys() else ""
            all_events = get_all_events(sport_id=self.bet_info["sport_id"], league=league_filter, auth=self.auth)

            # List of events taking only the winner option
            all_events = rows_to_columns(all_events)
            winner_events = list(all_events[self.user_info["option_team"]])
            # Take the event name from the previous list that best matches the pick option
            event_name = closest_string_match(self.user_info["option"], winner_events, th=0.75)["value"]
            # filter to keep only the resulting event (taking into account if it is live)
            all_events = columns_to_rows(all_events)
            # If we are handling with games handicaps, some points must be taken into account, as
            # PS3838 games bets are a bit unclear sometimes
            if self.user_info["resulting_unit"] == "Games":
                if "Games" in event_name:
                    pass
                elif "Sets)" in event_name:
                    self.user_info["resulting_unit"] = "Sets"
                    event_name = event_name[:-12]
                else:
                    self.user_info["resulting_unit"] = "Games"

            events = list(filter(lambda x: (x[self.user_info["option_team"]] == event_name) &
                                           (x["resulting_unit"] == self.user_info["resulting_unit"]), all_events))

            # Take all possible events for later checking the odds which one to choose
            if len(events) > 0:
                events_id = rows_to_columns(events)["event_id"]
                live_status = rows_to_columns(events)["live_status"]
                self.bet_info["possible_events"] = events_id
                self.bet_info["league_id"] = int(events[0]["league_id"])
                self.bet_info["league_name"] = events[0]["league_name"]
                self.bet_info["possible_live_status"] = live_status

            else:
                self.error += "No possible event has been found \n"

        except IndexError as err:
            self.error += "\nThere has been an error trying to find the event: "
            self.error += "IndexError: " + str(err)

    def odds(self):
        """This method calls the PS3838 betting API and gets the odds and bet type"""

        try:

            query = {
                "sportId": self.bet_info["sport_id"],
                "oddsFormat": "Decimal",
                "eventIds": self.bet_info["possible_events"],
            }
            print(query)
            # Check if any of the proposed events has status == 1. In case yes, use it for finding the line. Otherwise,
            # wait for 30 seconds and try again. It is possible that during a period of time, a line is not available.
            # Try for a maximum of 5 times. If no line is found, then just throw an error
            for _ in range(5):
                r_odds = requests.get("https://api.ps3838.com/v3/odds", auth=self.auth, params=query).json()
                for event in r_odds["leagues"][0]["events"]:
                    for period in event["periods"]:
                        if period["status"] == 1:
                            self.bet_info["event_id"] = event["id"]
                            self.bet_info["live_status"] = self.bet_info["possible_live_status"][
                                self.bet_info["possible_events"].index(event["id"])]
                            break
                if "event_id" not in self.bet_info.keys():
                    self.error += "No available event has been found \n"
                    time.sleep(30)
                else:
                    break
        except KeyError:
            self.error += "There has been an error previous to finding the odds \n"

    def set_line(self):
        """This method calls the PS3838 betting API and gets the specific line we want to bet on"""
        try:
            query = {
                "leagueId": self.bet_info["league_id"],
                "oddsFormat": "Decimal",
                "sportId": self.bet_info["sport_id"],
                "eventId": self.bet_info["event_id"],
                "periodNumber": 0,
                "betType": self.bet_info["bet_type"],
                "team": self.bet_info["team"],
                "handicap": self.bet_info["handicap"],
                "side": self.bet_info["side"]
            }

            # Search for the line given the proposed event id. Sometimes it won't be found, so wait for 30 seconds
            # and try again. Try for a maximum of 5 times.
            for _ in range(5):
                r_line = requests.get("https://api.ps3838.com/v2/line", auth=self.auth, params=query).json()

                if r_line["status"] == "SUCCESS":
                    self.bet_info["line_id"] = r_line["lineId"]
                    self.bet_info["odds"] = r_line["price"]
                    self.bet_info["min_risk_stake"] = r_line["minRiskStake"]
                    break
                else:
                    self.error += "\n There has been an error trying to find the line \n"
                    self.error += str(r_line) + "\n"
                    time.sleep(30)

        except KeyError as err:
            self.error += "\nThere has been an error before setting the line: "
            self.error += "KeyError: " + str(err)

    def set_betting_units(self):
        """Calculate the amount of money to place in the bet, regarding stake and bank information"""

        try:
            # r_balance = requests.get("https://api.ps3838.com/v1/client/balance", auth=self.auth).json()
            # balance = r_balance["availableBalance"]

            bank = self.bankroll
            if self.bet_info["stake"] == 0:
                quantity = self.bet_info["min_risk_stake"]
            else:
                stake = min(self.bet_info["stake"], self.max_stake)
                quantity = stake * bank / 100
                quantity = max(quantity, self.bet_info["min_risk_stake"])

            self.bet_info["quantity"] = quantity

        except KeyError as err:
            self.error += "\nThere has been an error trying to calculate the betting units: "
            self.error += "KeyError: " + str(err)

    def place_bet(self):
        """Place a bet using the ps3838 api, according to the betting parameters generated"""
        try:
            data = {
                "oddsFormat": "Decimal",
                "uniqueRequestId": str(uuid.uuid4()),
                "acceptBetterLine": True,
                "stake": self.bet_info["quantity"],
                "winRiskStake": "Risk",
                "lineId": self.bet_info["line_id"],
                "altLineId": None,
                "pitcher1MustStart": False,
                "pitcher2MustStart": False,
                "fillType": "FILLANDKILL",
                "sportId": self.bet_info["sport_id"],
                "eventId": self.bet_info["event_id"],
                "periodNumber": 0,
                "betType": self.bet_info["bet_type"],
                "team": self.bet_info["team"],
                "side": self.bet_info["side"],
                "handicap": self.bet_info["handicap"]
            }

            for _ in range(3):
                r_bet = requests.post("https://api.ps3838.com/v2/bets/place", auth=self.auth,
                                      headers=self.headers, json=data).json()

                if r_bet["status"] == "ACCEPTED":
                    self.bet_info["placed_bet"] = r_bet["straightBet"]
                    break
                elif r_bet["status"] == "PENDING_ACCEPTANCE":
                    time.sleep(30)
                    last_bet = self.get_last_placed_bet()
                    if last_bet["uniqueRequestId"] == r_bet["uniqueRequestId"] and \
                            last_bet["betStatus"] == "NOT_ACCEPTED":
                        pass
                    elif last_bet["uniqueRequestId"] == r_bet["uniqueRequestId"] and \
                            last_bet["betStatus"] == "ACCEPTED":
                        self.bet_info["placed_bet"] = last_bet
                        break

                elif r_bet["status"] == "PROCESSED_WITH_ERROR" and r_bet["errorCode"] == "LINE_CHANGED":
                    self.error += "\n There has been an error trying to place the bet: LINE CHANGED"
                else:
                    self.error += "There has been an error trying to place the bet"
                    self.error += str(r_bet)
                    break
        except (KeyError, IndexError) as err:
            self.error += "\nThere has been an error trying to place the bet: "
            self.error += "Error: " + str(err)

    def get_last_placed_bet(self):
        """Retrieve the bets placed in the last 5 minutes. This will allow to avoid placing the same bet
        more than once """

        query = {
            "betlist": "ALL",
            "fromDate": (datetime.now() - timedelta(minutes=5)).isoformat() + "Z",
            "toDate": datetime.now().isoformat() + "Z",
        }
        r = requests.get("https://api.ps3838.com/v3/bets", auth=self.auth, params=query).json()

        return r["straightBets"][-1]

        # If the bet we want to place is the same as any of the bets placed in the last five minutes, do not place it.
        # last_bet = r["straightBets"][-1]
        # if last_bet["betType"] == self.bet_info["bet_type"] and last_bet["sportId"] == self.bet_info["sport_id"] and \
        #     last_bet["leagueId"] == self.bet_info["league_id"] and last_bet["eventId"] == self.bet_info["event_id"]\
        #         and last_bet["teamName"] == self.bet_info["option"]:
        #     return True
        # return False


def get_sport_id(sport, auth):
    """This method calls the PS3838 betting API and gets the sport name and id
    :param sport: sport name to match with the ps3838 api sports
    :param auth: tuple with username and password to connect to the ps3838 API
    :return dic: with the ps3838 sport name and the sport id"""

    # Create the request
    r_sports = requests.get("https://api.ps3838.com/v3/sports", auth=auth).json()["sports"]
    # Filter to obtain the sport id and sport name matching the one provided by the user
    sport = list(filter(lambda x: x["name"] == sport, r_sports))[0]

    return {"sport_name": sport["name"], "sport_id": sport["id"]}


def get_all_leagues(sport_id, auth):
    """Get a list of dictionaries where the keys are league name and league id of the all the possible
    leagues for a given sport.
    :param sport_id: the id of the sport from which to retrieve the leagues
    :param auth: tuple with username and password to connect to the ps3838 API
    :return leagues: list of dictionaries with the following keys: ["name", "id"]
    """
    query = {"sportId": sport_id}
    r = requests.get('https://api.ps3838.com/v3/leagues.json', auth=auth, params=query).json()

    leagues = []
    for i, league in enumerate(r["leagues"]):
        leagues.append({
            "name": league["name"],
            "id": league["id"],
            "has_offerings": league["hasOfferings"]
        })

    return leagues


def get_all_events(sport_id, league, auth):
    """Get a list of dictionaries where the keys are league name, league id, event_id, home and away
     of the all the possible events for a given league.
    :param sport_id: the id of the sport from which to retrieve the leagues
    :param league: league from which to retrieve the events
    :param auth: tuple with username and password to connect to the ps3838 API
    :return df: list of dictionaries with the following keys:
                ["league_name", "league_id", "event_id", "home", "away"]
    """
    query = {"sportId": sport_id}
    r = requests.get('https://api.ps3838.com/v3/fixtures.json', auth=auth, params=query).json()["league"]

    if league != "" and league is not None:
        leagues = list(filter(lambda x: league in x["name"], r))
    else:
        leagues = r
    # print("LEAGUES: ", leagues)
    df = []
    for league in leagues:
        for event in league["events"]:
            current_event = {
                    "league_name": league["name"],
                    "league_id": league["id"],
                    "event_id": event["id"],
                    "home": event["home"],
                    "away": event["away"],
                    "resulting_unit": event["resultingUnit"],
                    "live_status": event["liveStatus"]
                }

            if event["status"] == "O":
                df.append(current_event)

    return df
