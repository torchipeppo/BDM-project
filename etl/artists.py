import util

def go(db):
    print("artists in progress")

    if db.has_collection('Artists'):
        db.delete_collection('Artists')
    artists_coll = db.create_collection('Artists')

    games_coll = db.collection("Games")

    if db.has_collection('ByArtist'):
        db.delete_collection('ByArtist')
    by_artist_coll = db.create_collection('ByArtist', edge=True)

    with open("../data/artists_reduced.csv", "r", newline="") as f:
        util.handle_adjacency_csv(f, db, games_coll, artists_coll, by_artist_coll)

if __name__=="__main__":
    go(util.open_db())
