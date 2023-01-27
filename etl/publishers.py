import util

def go(db):
    print("publishers in progress")

    if db.has_collection('Publishers'):
        db.delete_collection('Publishers')
    publishers_coll = db.create_collection('Publishers')

    games_coll = db.collection("Games")

    if db.has_collection('ByPublisher'):
        db.delete_collection('ByPublisher')
    by_publisher_coll = db.create_collection('ByPublisher', edge=True)

    with open("../data/publishers_reduced.csv", "r", newline="") as f:
        util.handle_adjacency_csv(f, db, games_coll, publishers_coll, by_publisher_coll)

if __name__=="__main__":
    go(util.open_db())
