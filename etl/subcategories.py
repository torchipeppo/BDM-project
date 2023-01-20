import util

def go(db):
    if db.has_collection('Subcategories'):
        db.delete_collection('Subcategories')
    subcategories_coll = db.create_collection('Subcategories')

    games_coll = db.collection("Games")

    if db.has_collection('InSubCategory'):
        db.delete_collection('InSubCategory')
    in_sub_category_coll = db.create_collection('InSubCategory', edge=True)

    with open("../data/subcategories.csv", "r", newline="") as f:
        util.handle_adjacency_csv(f, games_coll, subcategories_coll, in_sub_category_coll)

if __name__=="__main__":
    go(util.open_db())
