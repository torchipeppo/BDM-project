import util

def go(db):
    print("mechanics in progress")

    if db.has_collection('Mechanics'):
        db.delete_collection('Mechanics')
    mechanics_coll = db.create_collection('Mechanics')

    games_coll = db.collection("Games")

    if db.has_collection('HasMechanic'):
        db.delete_collection('HasMechanic')
    has_mechanic_coll = db.create_collection('HasMechanic', edge=True)

    with open("../data/mechanics.csv", "r", newline="") as f:
        util.handle_adjacency_csv(f, db, games_coll, mechanics_coll, has_mechanic_coll)

if __name__=="__main__":
    go(util.open_db())
