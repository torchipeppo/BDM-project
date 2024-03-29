import csv
from arango import ArangoClient   # https://docs.python-arango.com/en/main/

WRITE_GAMES_PER_NODE_QUERY = r"""
    FOR node IN @@node_collection
    FOR g IN 1..1 INBOUND node @@edge_collection
    COLLECT n_key = node._key WITH COUNT INTO num
    UPDATE n_key WITH {number_of_games: num} IN @@node_collection
"""

def open_db():
    client = ArangoClient(hosts="http://localhost:8529")
    db = client.db("project_bgg_snake", username="root", password="password")
    return db

# consistency is key
def get_game_key_from_id(game_bgg_id):
    return f"game{game_bgg_id:>06}"  # left padding of zeros, min size 6
def get_game_arango_id(games_coll_name, game_bgg_id):
    return games_coll_name + "/" + get_game_key_from_id(game_bgg_id)

def handle_adjacency_csv(f, db, games_coll, other_coll, edge_coll):
    reader = csv.reader(f)

    # handle header row separately
    header_list = reader.__next__()
    id_index = None

    # add a node for each artist/designer/mechanic/whatever, BUT:
    # don't do that for the BGGId column (of course),
    # keep its index to refer to it later;
    # and don't reify (Uncredited) either, it makes no sense.
    for i in range(len(header_list)):
        if header_list[i] == "BGGId":
            assert id_index is None
            id_index = i
            header_list[i] = ""
            continue
        if header_list[i] == "(Uncredited)" or header_list[i] == "(Unknown)" or "Low-Exp" in header_list[i]:
            header_list[i] = ""
            continue
        # some themes start with "Theme_" for no reason
        if header_list[i][:6] == "Theme_":
            header_list[i] = header_list[i][6:]
        # for real names, reify
        metadata = other_coll.insert({"name": header_list[i]})
        # and write the vertex id onto the list, for easy reference
        header_list[i] = metadata["_id"]
    
    assert id_index is not None

    # handle all the OTHER rows, those of the proper adjacency matrix
    for row_list in reader:
        bgg_id = row_list[id_index]
        for (i, adj) in enumerate(row_list):
            if adj == "1" and header_list[i]:
                edge_coll.insert({
                    "_from": get_game_arango_id(games_coll.name, bgg_id),
                    "_to": header_list[i],
                })
    
    # write games per node
    db.aql.execute(
        WRITE_GAMES_PER_NODE_QUERY,
        bind_vars={
            "@node_collection": other_coll.name,
            "@edge_collection": edge_coll.name,
        }
    )
