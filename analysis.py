import pandas as pd

df = pd.read_csv("data/epl_player_stats_24_25.csv", encoding="utf-8-sig")

wingers = ["Salah", "Saka", "Mbeumo", "Jacob Murphy", "Elanga",
           "Bowen", "Mitoma", "Trossard", "Martinelli", "Doku",
           "Savinho", "Anthony Gordon", "Brennan Johnson", "Kulusevski", "Madueke",
           "Semenyo", "Kudus", "Garnacho", "Amad Diallo", "Luis D",
           "Pedro Neto", "Harvey Barnes", "Leon Bailey", "Iliman Ndiaye", "Hudson-Odoi",
           "Harry Wilson", "Gakpo", "Heung", "la Sarr", "Sancho",
           "Schade", "Kluivert", "Ouattara", "Adama Tra", "Dibling", "Rashford"]

w = df[df["Player Name"].str.contains("|".join(wingers))]
w = w[w["Minutes"] >= 900].copy()

nineties = w["Minutes"] / 90

w["Goals_p90"] = w["Goals"] / nineties
w["Assists_p90"] = w["Assists"] / nineties
w["GA_p90"] = (w["Goals"] + w["Assists"]) / nineties
w["Shots_p90"] = w["Shots"] / nineties
w["ShotsOnTarget_p90"] = w["Shots On Target"] / nineties
w["ProgCarries_p90"] = w["Progressive Carries"] / nineties
w["ShotCarries_p90"] = w["Carries Ended with Shot"] / nineties
w["ChanceCarries_p90"] = w["Carries Ended with Chance"] / nineties
w["Crosses_p90"] = w["Successful Crosses"] / nineties
w["FinalThird_p90"] = w["Successful fThird Passes"] / nineties
w["PossWon_p90"] = w["Possession Won"] / nineties
w["Dispossessed_p90"] = w["Dispossessed"] / nineties

cols = ["Player Name", "Club", "GA_p90", "Shots_p90", "ProgCarries_p90",
        "ChanceCarries_p90", "Crosses_p90", "Dispossessed_p90"]

ranked = w.sort_values("GA_p90", ascending=False)
print(ranked[cols].round(2).to_string(index=False))

weights = {"GA_p90": 3, "ShotsOnTarget_p90": 1, "ProgCarries_p90": 2,
           "ChanceCarries_p90": 2, "ShotCarries_p90": 1, "Crosses_p90": 1,
           "FinalThird_p90": 1, "PossWon_p90": 1, "Dispossessed_p90": -1}

score = 0
for stat, weight in weights.items():
 score = score + (w[stat] - w[stat].mean()) / w[stat].std() * weight

w["Score"] = ((score - score.min()) / (score.max() - score.min()) * 100).round(1)

final = w.sort_values("Score", ascending=False)
print(final[["Player Name", "Club", "Score"]].to_string(index=False))

check = ["Mohamed Salah", "Bukayo Saka", "Cody Gakpo", "Marcus Rashford"]
print(w[w["Player Name"].isin(check)].set_index("Player Name")[list(weights)].round(2).T)
