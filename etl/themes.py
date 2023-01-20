import util

def go(db):
    if db.has_collection('Themes'):
        db.delete_collection('Themes')
    themes_coll = db.create_collection('Themes')

    games_coll = db.collection("Games")

    if db.has_collection('HasTheme'):
        db.delete_collection('HasTheme')
    has_theme_coll = db.create_collection('HasTheme', edge=True)

    with open("../data/themes.csv", "r", newline="") as f:
        util.handle_adjacency_csv(f, games_coll, themes_coll, has_theme_coll)

if __name__=="__main__":
    go(util.open_db())
