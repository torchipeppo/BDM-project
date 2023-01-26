import util

def go(db):
    print("designers in progress")

    if db.has_collection('Designers'):
        db.delete_collection('Designers')
    designers_coll = db.create_collection('Designers')

    games_coll = db.collection("Games")

    if db.has_collection('HasDesigner'):
        db.delete_collection('HasDesigner')
    has_designer_coll = db.create_collection('HasDesigner', edge=True)

    with open("../data/designers_reduced.csv", "r", newline="") as f:
        util.handle_adjacency_csv(f, db, games_coll, designers_coll, has_designer_coll)

    # TODO La presenza del Low-Exp Designer potrebbe dar fastidio

if __name__=="__main__":
    go(util.open_db())
