import util

def go(db):
    print("publishers in progress")

    if db.has_collection('Publishers'):
        db.delete_collection('Publishers')
    publishers_coll = db.create_collection('Publishers')

    games_coll = db.collection("Games")

    if db.has_collection('HasPublisher'):
        db.delete_collection('HasPublisher')
    has_publisher_coll = db.create_collection('HasPublisher', edge=True)

    with open("../data/publishers_reduced.csv", "r", newline="") as f:
        util.handle_adjacency_csv(f, db, games_coll, publishers_coll, has_publisher_coll)

    # TODO La presenza del Low-Exp Publisher potrebbe dar fastidio

if __name__=="__main__":
    go(util.open_db())
