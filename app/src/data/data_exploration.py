import matplotlib.pyplot as plt
import pandas as pd
import pickle
import datetime
import pytz
from collections import Counter
import jellyfish
import unidecode
import requests
import base64

username = "AC88012241"
password = "Bet.ps3838_1234"
my_headers1 = {"Accept": "application/json",
              "Content-Type": "application/json"}
query = {"sportId": 33}
r = requests.get('https://api.ps3838.com/v3/leagues.json', auth=(username, password), headers=my_headers1, params=query).json()
print(r)
utc = pytz.UTC
path = 'bet-history-images/'
with open(path + "/stats.pickle", "rb") as f:
    data = pickle.load(f)

data = pd.DataFrame(data)

# Number of times that a specific bet appears onver the whole dataset
#
# data1 = data.groupby(["bet"])["bet"].count().reset_index(name="counts")
# data1 = data1[data1["counts"] > 1].sort_values("counts", ascending=False)
# # print(data1)
# # data1.plot.bar(x="bet", y="counts")
# # plt.show()
#
# # We can see that the most common ones are "Ganador del encuentro" (LIVE bet) and
# # Ganara el encuentro (Pre match bet). In some cases, the OCR algorithm did not work perfectly and
# # the same bet has a slightly different name (as "Ganara el encuentra")
#
bets_to_keep = {"Ganara el encuentro": 0, "Ganador del encuentro": 0, "Apuestas al set": 0,
                "Jugador - ganara 1 set": 0, "Set actual - ganador": 0,
                "Handicap - 2 opciones - juegos ganados": 0, "Ganador": 0,
                "total de juegos - 2 opciones": 0, "Encuentro - Handicap": 0, }
#
x = list(bets_to_keep.keys())
#
def match_string(string, map_list):
    if string == None:
        dist = 0
    else:
        arr = [jellyfish.jaro_similarity(string.lower(), unidecode.unidecode(s.lower())) for s in map_list]
        dist = max(arr)
        idx = arr.index(dist)

        # print(string, ";", map_list[idx], ";", dist)
    if dist > 0.9:
        return map_list[idx]
    else:
        return None
#
# # Number of times that a specific bet appears (only over the updated pictures, i.e from 30/06/2021 onwards)
# data2 = data[data["date"] <= utc.localize(datetime.datetime(2021, 6, 30))]
# data3 = data2.groupby(["bet"])["bet"].count().reset_index(name="counts")
# data3 = data3[data3["counts"] > 0].sort_values("counts", ascending=False)
# # print(data3)
# data3.plot.bar(x="bet", y="counts")
#
#
data["new_bet"] = data["bet"].apply(lambda s: match_string(s, x))
data4 = data[data["new_bet"] != None]
data4 = data4.groupby(["new_bet"])["new_bet"].count().reset_index(name="counts")
data4 = data4[data4["counts"] > 0].sort_values("counts", ascending=False)
print(data4)
data4.plot.bar(x="new_bet", y="counts")

data41 = data[data["new_bet"] == "Apuestas al set"]
aa = data41.groupby(["option"])["option"].count().reset_index(name="counts").sort_values("counts", ascending=False)
bb = data41.groupby(["bet_type"])["bet_type"].count().reset_index(name="counts").sort_values("counts", ascending=False)
print(set(list(aa["option"])))
print(set(list(bb["bet_type"])))
print(bb)
print(data41[data41["bet_type"] == "Pre match"])

# IT can be seen that the most common bets are "Ganador del encuentro" and "Ganara el encuentro", followed
# by "Apuestas al set"


# Count the number of tournaments that appear. We want to check their names to map them
# against the names of the torunaments in the ps3838 api.

data5 = data.groupby("tournament")["tournament"].count().reset_index(name="counts").sort_values("counts", ascending=False)
print(list(data5["tournament"]))
print(len(list(data5["tournament"])))
data5.plot(x="tournament", y="counts")

df_leagues = pd.DataFrame()
# print(r["leagues"])
for i, league in enumerate(r["leagues"]):
    # print(league)
    df_leagues = df_leagues.append({
            "n": i,
            "id": league["id"],
            "name": league["name"]
        }, ignore_index=True)
#
print(df_leagues)


leagues = list(df_leagues["name"])
for i in range(len(leagues)):
    leagues[i] = leagues[i].split(" - ")[0]

leagues = list(set(leagues))
print(len(leagues))


def correct_tournament_name(string):
    mapping = {"queens": "london", "marsella": "marseille", "copa davis": "davis cup",
               "burdeos": "bordeaux", "jjoo": "olympics", "roland garros": "atp french open",
               "ginebra": "geneva", "san petersburgo": "st. petersburg", "open australia": "australian open",
               "londres": "london", "napoles": "napoli", "praga": "prague", "amberes": "antwerp",
               "roseto": "roseto degli abruzzi", "us open wta": "wta us open", "varsovia": "warsaw",
               "french open": "atp french open"}

    # Remove accents
    string = unidecode.unidecode(string)

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

    return string


data5["new_tournament"] = data5["tournament"].apply(lambda s: correct_tournament_name(s))
data5["league_old"] = data5["tournament"].apply(lambda s: match_string(s, leagues))
data5["league"] = data5["new_tournament"].apply(lambda s: match_string(s, leagues))
data5 = data5.dropna()


x1 = list(data5["new_tournament"])
x2 = list(data5["league"])
x4 = list(data5["league_old"])
x6 = list(data5["tournament"])
print(x1)
print(x2)
print(x1[0], x2[0])
print(jellyfish.jaro_similarity(x1[0], x2[0]))
x3 = [jellyfish.jaro_similarity(x1[i].lower(), x2[i].lower()) for i in range(len(x1))]
x5 = [jellyfish.jaro_similarity(x6[i].lower(), x4[i].lower()) for i in range(len(x6))]
plt.figure()
plt.hist(x3)

plt.figure()
plt.hist(x5)



# leagues = list(filter(lambda t: t != None, leagues))
# print(leagues)
# print(leagues.sort())
# for i in leagues:
#     print(i)
# plt.figure()
# plt.hist(list(data1.keys()), list(data1.values()))
plt.show()