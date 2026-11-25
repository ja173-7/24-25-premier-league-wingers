import pandas as pd
import unicodedata

df = pd.read_csv("data/players_data-2024_2025.csv")
pl = df[df["Comp"].str.contains("Premier League", na=False)].copy()

needed = ["Min", "Gls", "Ast", "xG", "xAG", "SoT", "Att Pen", "KP", "SCA", "PPA",
          "CrsPA", "Succ", "PrgC", "PrgR", "Mis", "Dis"]
missing = [c for c in needed if c not in pl.columns]
if missing:
    print("Missing columns:", missing)
    print(list(pl.columns))
    raise SystemExit

for c in needed:
    pl[c] = pd.to_numeric(pl[c].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

def clean(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()

# Full names where a short one could match someone else ("saka" was matching Wan-Bissaka)
wingers = ["salah", "bukayo saka", "mbeumo", "jacob murphy", "elanga", "bowen", "mitoma",
           "trossard", "martinelli", "doku", "savio", "anthony gordon",
           "brennan johnson", "kulusevski", "madueke", "semenyo", "kudus", "garnacho",
           "amad diallo", "luis diaz", "pedro neto", "harvey barnes", "leon bailey",
           "iliman ndiaye", "hudson-odoi", "harry wilson", "gakpo", "heung",
           "ismaila sarr", "sancho", "schade", "kluivert", "ouattara",
           "adama traore", "dibling", "rashford"]

pl["key"] = pl["Player"].apply(clean)
w = pl[pl["key"].str.contains("|".join(wingers))]
print("Not found:", [n for n in wingers if not w["key"].str.contains(n).any()])

w = w.groupby("Player").agg({**{c: "sum" for c in needed}, "Squad": " / ".join}).reset_index()
print("Under 900 minutes:", list(w[w["Min"] < 900]["Player"]))
w = w[w["Min"] >= 900].copy()
nineties = w["Min"] / 90
w["Losses"] = w["Mis"] + w["Dis"]
w["GA"] = w["Gls"] + w["Ast"]
w["xGA"] = w["xG"] + w["xAG"]

# Every stat per 90: name -> column in the data
stats = {"Goals + assists": "GA", "Goals": "Gls", "Assists": "Ast",
         "xG + xA": "xGA", "xG": "xG", "xA": "xAG",
         "Shots on target": "SoT", "Box touches": "Att Pen", "Chance creation": "SCA",
         "Key passes": "KP", "Passes into box": "PPA", "Crosses into box": "CrsPA",
         "Dribbles": "Succ", "Progressive carries": "PrgC", "Passes received": "PrgR",
         "Ball losses": "Losses"}
for name, col in stats.items():
    w[name + " p90"] = w[col] / nineties

# Season total, so a full season of output counts more than half a season
w["Season goals + assists"] = w["GA"]

# z-score = how far above or below the average winger
def z(s):
    return (s - s.mean()) / s.std()

def to_100(s):
    return ((s - s.min()) / (s.max() - s.min()) * 100).round(1)

# 5 categories. Question: who had the best SEASON? So what actually
# happened (goals + assists) counts most, xG + xA checks it wasn't luck,
# and involvement stats (chances, dribbles) support it.
categories = {
    "End product": {"Goals + assists p90": 1, "Season goals + assists": 1},
    "Chance quality": {"xG + xA p90": 1},
    "Creating": {"Chance creation p90": 1, "Key passes p90": 1, "Passes into box p90": 1,
                 "Crosses into box p90": 1, "Shots on target p90": 1, "Box touches p90": 1},
    "Dribbling": {"Dribbles p90": 1, "Progressive carries p90": 1, "Passes received p90": 1},
    "Ball security": {"Ball losses p90": -1},   # minus = fewer losses is better
}
category_weights = {"End product": 0.45, "Chance quality": 0.20, "Creating": 0.15,
                    "Dribbling": 0.15, "Ball security": 0.05}

total = 0
for cat, inside in categories.items():
    raw = sum(z(w[col]) * wt for col, wt in inside.items()) / sum(abs(v) for v in inside.values())
    cat_z = z(raw)
    w[cat] = to_100(cat_z)
    total = total + cat_z * category_weights[cat]

w["Score"] = to_100(total)
for name in stats:
    w[name + " p90"] = w[name + " p90"].round(2)

final = w.sort_values("Score", ascending=False).reset_index(drop=True)
final.insert(0, "Rank", range(1, len(final) + 1))

print(len(final), "wingers")
print()
print("Gls and Ast = season totals. Everything after Ast is PER 90:")
print("GA90 = goals + assists, xG = expected goals, xA = expected assists, OnTgt = shots on target,")
print("BoxT = touches in box, SCA = chance creation, KP = key passes, BoxP = passes into box,")
print("Cross = crosses into box, Drib = successful dribbles, Carry = progressive carries,")
print("Recv = progressive passes received, Loss = ball losses (fewer is better)")
print()

# One table: player info, then every stat per 90, then the score at the end
cols = {"Goals + assists": "GA90", "xG": "xG", "xA": "xA", "Shots on target": "OnTgt",
        "Box touches": "BoxT", "Chance creation": "SCA", "Key passes": "KP",
        "Passes into box": "BoxP", "Crosses into box": "Cross", "Dribbles": "Drib",
        "Progressive carries": "Carry", "Passes received": "Recv", "Ball losses": "Loss"}

short_clubs = {"Manchester Utd": "Man Utd", "Manchester City": "Man City",
               "Newcastle Utd": "Newcastle", "Nott'ham Forest": "Forest",
               "Aston Villa": "Villa", "Crystal Palace": "Palace"}

table = final[["Rank", "Player", "Squad", "Min", "Gls", "Ast"]
              + [n + " p90" for n in cols] + ["Score"]].copy()
for long_name, short_name in short_clubs.items():
    table["Squad"] = table["Squad"].str.replace(long_name, short_name)
table.columns = ["Rank", "Player", "Club", "Min", "Gls", "Ast"] + list(cols.values()) + ["Score"]
print(table.to_string(index=False))

final.to_json("docs/data.json", orient="records", force_ascii=False, indent=1)
print()
print("Saved docs/data.json")