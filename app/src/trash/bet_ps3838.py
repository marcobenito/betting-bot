from app.src.project.betting import Betting, get_all_leagues
from decouple import config
import requests


username = "AC88012241"
password = "Bet.ps3838_1234"

import json
with open("../../config.json", "rb") as f:
    inputs = json.load(f)["bet"]

inputs["username"] = config("PS3838_USERNAME")
inputs["password"] = config("PS3838_PASSWORD")
inputs["bankroll"] = 100
get_all_leagues(33, (inputs["username"], inputs["password"]))
# print(config)
bet_info = {"sport": "Tennis", "tournament": "", "home": "Carlos Alcaraz", "away": "Maria Sakkari",
            "resulting_unit":"Sets", "option_team": "home", "option": "Carlos Alcaraz", "bet_type": "MONEYLINE",
            "live_status":0 , "handicap": 23.0, "side": "OVER"}
# auth = (inputs["username"], config["password"])
betting = Betting(inputs, bet_info)
if betting.error != "":
    print(betting.error)
else:
    betting.set_fixtures()
    print(betting.error)
    betting.odds()
    betting.set_line()
    betting.set_betting_units()

    # Step 5: Place bet using the generated parameters
    # betting.place_bet()
    print(betting.error)
    print(betting.bet_info)
# betting.fixtures()