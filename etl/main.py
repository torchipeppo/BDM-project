import util
import games_etc
import artists
import designers
import mechanics
import publishers
import subcategories
import themes

db = util.open_db()

games_etc.go(db)
artists.go(db)
designers.go(db)
mechanics.go(db)
publishers.go(db)
subcategories.go(db)
themes.go(db)
