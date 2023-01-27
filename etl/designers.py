import util

def go(db):
    print("designers in progress")

    if db.has_collection('Designers'):
        db.delete_collection('Designers')
    designers_coll = db.create_collection('Designers')

    games_coll = db.collection("Games")

    if db.has_collection('ByDesigner'):
        db.delete_collection('ByDesigner')
    by_designer_coll = db.create_collection('ByDesigner', edge=True)

    with open("../data/designers_reduced.csv", "r", newline="") as f:
        util.handle_adjacency_csv(f, db, games_coll, designers_coll, by_designer_coll)

if __name__=="__main__":
    go(util.open_db())
