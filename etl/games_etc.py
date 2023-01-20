import csv
import json  # for a stringified list
import re    # idem
from collections import defaultdict
import util

"""
games.csv column names:

BGGId, Name, Description, YearPublished, GameWeight, 
AvgRating, BayesAvgRating, StdDev, 
MinPlayers, MaxPlayers, ComAgeRec, LanguageEase, BestPlayers, GoodPlayers, 
NumOwned, NumWant, NumWish, NumWeightVotes, 
MfgPlaytime, ComMinPlaytime, ComMaxPlaytime, MfgAgeRec, 
NumUserRatings, NumComments, NumAlternates, 
NumExpansions, NumImplementations, IsReimplementation, 
Family, Kickstarted, ImagePath, 
Rank:boardgame, Rank:strategygames, Rank:abstracts, Rank:familygames, 
Rank:thematic, Rank:cgs, Rank:wargames, Rank:partygames, Rank:childrensgames, 
Cat:Thematic, Cat:Strategy, Cat:War, Cat:Family, Cat:CGS, 
Cat:Abstract, Cat:Party, Cat:Childrens
"""

CAT_thematic = {
    "arango_name": "thematic",
    "csv_name": "Cat:Thematic",
    "csv_rankname": "Rank:thematic",
}
CAT_strategy = {
    "arango_name": "strategy",
    "csv_name": "Cat:Strategy",
    "csv_rankname": "Rank:strategygames",
}
CAT_war = {
    "arango_name": "war",
    "csv_name": "Cat:War",
    "csv_rankname": "Rank:wargames",
}
CAT_family = {
    "arango_name": "family",
    "csv_name": "Cat:Family",
    "csv_rankname": "Rank:familygames",
}
CAT_cards = {
    "arango_name": "cards",
    "csv_name": "Cat:CGS",
    "csv_rankname": "Rank:cgs",
}
CAT_abstract = {
    "arango_name": "abstract",
    "csv_name": "Cat:Abstract",
    "csv_rankname": "Rank:abstracts",
}
CAT_party = {
    "arango_name": "party",
    "csv_name": "Cat:Party",
    "csv_rankname": "Rank:partygames",
}
CAT_children = {
    "arango_name": "children",
    "csv_name": "Cat:Childrens",
    "csv_rankname": "Rank:childrensgames",
}

CAT_LIST = [CAT_thematic,CAT_strategy,CAT_war,CAT_family,CAT_cards,CAT_abstract,CAT_party,CAT_children]

# CAT_CSV_CONV = {
#     "Cat:Thematic": CAT_thematic,
#     "Rank:thematic": CAT_thematic,
#     "Cat:Strategy": CAT_strategy,
#     "Rank:strategygames": CAT_strategy,
#     "Cat:War": CAT_war,
#     "Rank:wargames": CAT_war,
#     "Cat:Family": CAT_family,
#     "Rank:familygames": CAT_family,
#     "Cat:CGS": CAT_cards,
#     "Rank:cgs": CAT_cards,
#     "Cat:Abstract": CAT_abstract,
#     "Rank:abstracts": CAT_abstract,
#     "Cat:Party": CAT_party,
#     "Rank:partygames": CAT_party,
#     "Cat:Childrens": CAT_children,
#     "Rank:childrensgames": CAT_children,
# }

def go(db):

    # TODO vogliamo grafare pure l'anno di pubblicazione?
    #      per adesso boh, ma dipende anche da che query vogliamo fare...

    # reify categories, found at the end of games.csv
    if db.has_collection('Categories'):
        db.delete_collection('Categories')
    categories_coll = db.create_collection('Categories')

    if db.has_collection('InCategory'):
        db.delete_collection('InCategory')
    in_category_coll = db.create_collection('InCategory', edge=True)

    for cat in CAT_LIST:
        cat = cat["arango_name"]
        categories_coll.insert({"_key": cat, "name": cat})

    if db.has_collection('Games'):
        db.delete_collection('Games')
    games_coll = db.create_collection('Games')

    # note game families to reify later
    families = set()
    family_edges_by_family = defaultdict(list)

    with open("../data/games.csv", "r", newline="") as f:
        reader = csv.DictReader(f)
        for row_dict in reader:
            # alter the dict read from the CSV to better fit our graph-doc. DB
            # also, covert numeric data to numeric types.
            # can't instruct Python to do so b/c it only differentiates by quoted/unquoted fields,
            # and all fields here are unquoted.
            game_dict = dict()

            # define the primary key (replaces BDDId too.)
            game_dict["_key"]         = util.get_game_key_from_id(row_dict["BGGId"])
            game_dict["name"]         = row_dict["Name"]
            # desc is too tokenized to be useful
            # game_dict["description"]  = row_dict["Description"]
            game_dict["year"]         = int(row_dict["YearPublished"])
            game_dict["weight"]       = float(row_dict["GameWeight"])
            game_dict["rating_avg"]          = float(row_dict["AvgRating"])
            game_dict["rating_bayes_avg"]    = float(row_dict["BayesAvgRating"])
            game_dict["rating_bayes_stddev"] = float(row_dict["StdDev"])
            # turn min/max attributes into ranges
            game_dict["players_mfg"] = {
                "min": int(row_dict["MinPlayers"]),
                "max": int(row_dict["MaxPlayers"]),
            }
            if row_dict["ComAgeRec"]:
                game_dict["age_com"]        = float(row_dict["ComAgeRec"])
            if row_dict["LanguageEase"]:
                game_dict["language_ease"]  = float(row_dict["LanguageEase"])
            game_dict["players_com_best"]   = int(row_dict["BestPlayers"])
            # want a list of ints here, and it turns out
            # that I have the STRING representation of a list
            # there are apices inside, but w/e, I want numbers anyway
            good_players_str = row_dict["GoodPlayers"].replace("'", "")
            good_players_str = good_players_str.replace('"', '')
            # except there's a special value that wants to be a string
            # example: 6+ -> "More"
            good_players_str = re.sub(r"(\d+[+])", '"More"', good_players_str)
            game_dict["players_com_good"] = json.loads(good_players_str)
            game_dict["num_owned"]         = int(row_dict["NumOwned"])
            game_dict["num_want"]          = int(row_dict["NumWant"])
            game_dict["num_wish"]          = int(row_dict["NumWish"])
            game_dict["num_weight_votes"]  = int(row_dict["NumWeightVotes"])
            game_dict["playtime_mfg"] = int(row_dict["MfgPlaytime"])
            game_dict["playtime_com"] = {
                "min": int(row_dict["ComMinPlaytime"]),
                "max": int(row_dict["ComMaxPlaytime"]),
            }
            game_dict["age_mfg"] = int(row_dict["MfgAgeRec"])
            game_dict["num_user_ratings"] = int(row_dict["NumUserRatings"])
            game_dict["num_comments"] = int(row_dict["NumComments"])
            game_dict["num_alternates"] = int(row_dict["NumAlternates"])
            game_dict["num_expansions"] = int(row_dict["NumExpansions"])
            game_dict["num_implementation"] = int(row_dict["NumImplementations"])
            # "0" is truthy, thus the double cast
            game_dict["is_reimplementation"] = bool(int(row_dict["IsReimplementation"]))
            game_dict["is_kickstarted"] = bool(int(row_dict["Kickstarted"]))
            game_dict["rank"] = int(row_dict["Rank:boardgame"])

            # add game to DB, keep id for later
            metadata = games_coll.insert(game_dict)
            game_id = metadata["_id"]

            family = row_dict["Family"]
            if family:
                families.add(family)  # it's a set, multiple additions are no problem
                family_edges_by_family[family].append(game_id)

            # connect to categories, rank will be an edge attribute
            for cat in CAT_LIST:
                if row_dict[cat["csv_name"]] == "1":
                    in_category_coll.insert({
                        "_from": game_id,
                        "_to": categories_coll.name + "/" + cat["arango_name"],
                        "rank": row_dict[cat["csv_rankname"]],
                    })
    
    # reify families
    if db.has_collection('Families'):
        db.delete_collection('Families')
    families_coll = db.create_collection('Families')

    if db.has_collection('InFamily'):
        db.delete_collection('InFamily')
    in_family_coll = db.create_collection('InFamily', edge=True)

    for family_name in families:
        metadata = families_coll.insert({"name": family_name})
        family_id = metadata["_id"]
        for game_id in family_edges_by_family[family_name]:
            in_family_coll.insert({
                "_from": game_id,
                "_to": family_id,
            })

if __name__=="__main__":
    go(util.open_db())
