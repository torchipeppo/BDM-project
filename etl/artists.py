import util

def go(db):
    if db.has_collection('Artists'):
        db.delete_collection('Artists')
    artists_coll = db.create_collection('Artists')

    games_coll = db.collection("Games")

    if db.has_collection('HasArtist'):
        db.delete_collection('HasArtist')
    has_artist_coll = db.create_collection('HasArtist', edge=True)

    with open("../data/artists_reduced.csv", "r", newline="") as f:
        util.handle_adjacency_csv(f, games_coll, artists_coll, has_artist_coll)

    # TODO La presenza del Low-Exp Artist potrebbe dar fastidio

if __name__=="__main__":
    go(util.open_db())
