## Tutti i giochi di una certa famiglia
*(Query semplice, tecnica: regex)*

```sql
FOR f IN Families
    FILTER f.name =~ @family
    FOR g IN 1..1 INBOUND f InFamily
    RETURN g.name
```
Ad esempio, @family <- "Pandemic?" o "Mysterium?"


## Giochi per cui la community ha suggerito un'età minima inferiore a quella proposta dagli autori
*(Tecnica: attributi mancanti, comportamento del null)*

```sql
FOR g IN Games
    // FILTER g.age_com != null
    FILTER CEIL(g.age_com) < g.age_mfg
    RETURN {name:g.name, age_com:g.age_com, age_mfg:g.age_mfg}
```
Mostra che in ArangoDB, null è confrontabile ed è minore di qulsiasi numero, quindi va trattato esplicitamente decommentando la seconda riga.


## Peso medio per età minima
*(Tecnica: COLLECT, AGGREGATE (per range))*

```sql
for g in Games
    FILTER g.age_mfg != null AND g.weight != null
    COLLECT min_age = FLOOR((g.age_mfg - 1) / @age_range_width) * @age_range_width + 1
    AGGREGATE min_weight = MIN(g.weight),
              max_weight = MAX(g.weight),
              avg_weight = AVG(g.weight),
              num_games = COUNT(g.weight)
    LET max_age = min_age + @age_range_width - 1
    RETURN {
        age_range:{min:min_age, max:max_age},
        num_games,
        avg_weight,
        weight_range:{min:min_weight, max:max_weight}
    }
```
Ad esempio, @age_range_width <- 5


## Autori che hanno pubblicato X giochi con rating elevato
*(Tecnica: subquery, `array[*]`, c'è anche una (semplice) regex!)*

```sql
FOR d IN Designers
    FILTER d.name !~ "Low-Exp"
    LET good_games = (
        FOR g IN 1..1 INBOUND d HasDesigner
        FILTER g.rating_avg > @rating_threshold
        RETURN {name:g.name, rating:g.rating_avg}
    )
    LET gg_num = COUNT(good_games)
    FILTER gg_num >= @count_threshold
    SORT gg_num DESC
    RETURN {designer: d.name, games: good_games[*].name}
```
Ad esempio, @rating_threshold <- 8.5 e @count_threshold <- 2


## Top 3 giochi di ogni categoria
*(Tecnica: attributi arco)*

```sql
FOR c IN Categories
    FOR g, e IN 1..1 INBOUND c InCategory
    FILTER e.rank <= @topX
    COLLECT cat = c.name INTO groups = [e.rank, g.name]  //-- list in order to sort by rank
    RETURN {cat, top3games:SORTED(groups)[*][1]}
```
Ad esempio, @topX <- 3


## Per ogni artista, il suo tema preferito
*(Tecnica: percorsi su grafo (len 2), `array[*]`, `ALL <=`, COLLECT, AGGREGATE, subquery)*

```sql
FOR a IN Artists
    LET his_themes = (
        FOR g IN 1..1 INBOUND a HasArtist
        FOR t IN 1..1 OUTBOUND g HasTheme
        COLLECT theme = t.name WITH COUNT INTO num
        RETURN {theme, num}
    )  //-- subquery necessary to "step out" now and pick the max
    FOR t IN his_themes
        FILTER his_themes[*].num ALL <= t.num
        COLLECT artist = a.name INTO fav_themes = t.theme
        RETURN {artist, fav_themes}
```


## Studio sovrapposizione categorie e sottocategorie
*(Dominio, curiosità)*

```sql
FOR g IN Games
    FOR c IN 1..1 OUTBOUND g InCategory
    FOR s IN 1..1 OUTBOUND g InSubCategory
    COLLECT cat=c, subcat=s WITH COUNT INTO both
    LET both_over_cat = both/cat.number_of_games
    LET both_over_subcat = both/subcat.number_of_games
    SORT both_over_subcat DESC
    RETURN {
        cat_name:cat.name,
        subcat_name:subcat.name,
        both,
        cat:cat.number_of_games,
        "both/cat":both_over_cat,
        subcat:subcat.number_of_games,
        "both/subcat":both_over_subcat,
    }
```
Si scopre che: Cards (category) => Card Game (subcategory) all'80% ma non viceversa,
e che Cards (category) => Collectible Components al 75% e viceversa al 66%.
Non ci sono altre sovrapposizioni degne di nota.


## Nodi in comune a due giochi dati
*(Tecnica: K_PATHS)*

```sql
FOR g1 IN Games
    FILTER LOWER(g1.name) == LOWER(@name1)
    FOR g2 IN Games
    FILTER LOWER(g2.name) == LOWER(@name2)
    FOR path IN 2..2 ANY K_PATHS g1._id TO g2._id InCategory, InSubCategory, InFamily, HasArtist, HasDesigner, HasPublisher, HasMechanic, HasTheme
    //-- graph is bipartite (games, everything_else)
    //-- so this path is always [game, designer_mechanic_whatever, game].
    LET common_element = path.vertices[1].name
    LET connection_type = PARSE_IDENTIFIER(path.edges[0]._id).collection
    RETURN {common_element, connection_type}
```
Ad esempio, @game1 <- "Pandemic: Fall of Rome" e @game2 <- "Vast: The Crystal Caverns"


## 6 Gradi di Rodger MacGowan
*(Analisi grafo, dominio)*

```sql
//-- The best artists to play as Kevin Bacon are... Rodger B. MacGowan or Franz Vohwinkel
FOR a IN Artists
    //-- The "true" query is actually this subquery.
    LET dos_result = (
        FOR bacon IN Artists
        FILTER bacon.name == @bacon
        FOR v, e IN ANY SHORTEST_PATH a TO bacon HasArtist
        COLLECT start=a.name INTO path={name:v.name, is_game:IS_SAME_COLLECTION("Games", v)}
        LET degrees_of_separation = COUNT(path[* FILTER CURRENT.is_game])
        SORT degrees_of_separation DESC
        RETURN {start, degrees_of_separation, path:path[*].name}
    )[0]  //-- returns only one thing, but still in an aray b/c subquery
    //-- But I need to do some extra manipulation to make sure unconnected artists show up as null
    SORT dos_result.degrees_of_separation DESC
    RETURN {start: a.name, degrees_of_separation: dos_result.degrees_of_separation, path: dos_result.path}
```
Ad esempio, @bacon <- "Rodger B. MacGowan"

### Note

* Scelto proprio MacGowan perché è l'artista che ha illustrato più giochi. Trovato con banale query:

  `FOR a IN Artists SORT a.number_of_games DESC RETURN a`

* Tra l'altro, purtroppo il grafo giochi-autori è disconnesso.

* *(Poi ho provato anche a fare 6 gradi di Monopoli con connessioni HasDesigner, HasMechanic, HasPublisher, InFamily, ma ovviamente la complessità aumenta esponenzialmente, e non si ottiene una risposta in tempo utile.)*

## Recommendation System
*(Dominio, applicazione semi-realistica, analisi grafo)*

```sql
FOR start IN Games
    FILTER LOWER(start.name) == LOWER(@game_name)
    
    FOR end, _e, path IN 2..2 ANY start HasDesigner, HasMechanic, HasTheme, InCategory, InFamily
    FILTER end.rating_avg > @rating_threshold
    FILTER ABS(end.weight - start.weight) < @weight_threshold
    LET start_playtime = HAS(start, "playtime_com") ? start.playtime_com : {min:start.playtime_mfg, max:start.playtime_mfg}
    LET end_playtime = HAS(end, "playtime_com") ? end.playtime_com : {min:end.playtime_mfg, max:end.playtime_mfg}
    FILTER (start_playtime.min-@time_margin <= end_playtime.min-@time_margin AND end_playtime.min-@time_margin <= start_playtime.max+@time_margin) OR
           (end_playtime.min-@time_margin <= start_playtime.min-@time_margin AND start_playtime.min-@time_margin <= end_playtime.max+@time_margin)
    FILTER HAS(start, "players_com_good") AND HAS(end, "players_com_good")
           ?
           COUNT(INTERSECTION(start.players_com_good, end.players_com_good)) > 0 OR "More" IN start.players_com_good OR "More" IN end.players_com_good
           :
           (start.players_mfg.min <= end.players_mfg.min AND end.players_mfg.min <= start.players_mfg.max) OR
           (end.players_mfg.min <= start.players_mfg.min AND start.players_mfg.min <= end.players_mfg.max)
    
    //-- graph is bipartite (games, everything_else)
    //-- so this path is always [game, designer_mechanic_whatever, game].
    LET common_element = path.vertices[1]
    COLLECT start2=start, end2=end INTO common_elements_array=common_element
    LET common_designers = common_elements_array[* FILTER IS_SAME_COLLECTION("Designers", CURRENT._id)]
    LET num_common_designers = COUNT(common_designers)
    LET common_mechanics = common_elements_array[* FILTER IS_SAME_COLLECTION("Mechanics", CURRENT._id)]
    LET num_common_mechanics = COUNT(common_mechanics)
    LET common_themes = common_elements_array[* FILTER IS_SAME_COLLECTION("Themes", CURRENT._id)]
    LET num_common_themes = COUNT(common_themes)
    LET common_categories = common_elements_array[* FILTER IS_SAME_COLLECTION("Categories", CURRENT._id)]
    LET num_common_categories = COUNT(common_categories)
    LET common_families = common_elements_array[* FILTER IS_SAME_COLLECTION("Families", CURRENT._id)]
    LET num_common_families = COUNT(common_families)
    
    //-- b/c some families are so large they take up multiple spots
    FILTER NOT @exclude_same_family OR num_common_families==0
    
    LET reasons = RTRIM(CONCAT(UNION(
        [end2.name, " is recommended because it shares the following with ", start2.name, ": \n"],
        common_designers[* LIMIT @limit_designers RETURN CONCAT(CURRENT.name, " (designer), ")],
        num_common_designers > @limit_designers ? ["and ", num_common_designers-@limit_designers, " more designers, "] : [],
        common_mechanics[* LIMIT @limit_mechanics RETURN CONCAT(CURRENT.name, " (mechanic), ")],
        num_common_mechanics > @limit_mechanics ? ["and ", num_common_mechanics-@limit_mechanics, " more mechanics, "] : [],
        common_themes[* LIMIT @limit_themes RETURN CONCAT(CURRENT.name, " (theme), ")],
        num_common_themes > @limit_themes ? ["and ", num_common_themes-@limit_themes, " more themes, "] : [],
        common_categories[* LIMIT @limit_categories RETURN CONCAT(CURRENT.name, " (category), ")],
        num_common_categories > @limit_categories ? ["and ", num_common_categories-@limit_categories, " more categories, "] : [],
        common_families[* LIMIT @limit_families RETURN CONCAT(CURRENT.name, " (family), ")],
        num_common_families > @limit_families ? ["and ", num_common_families-@limit_families, " more families, "] : []
    )), "\r\n \t,")
    LET query_details = {
        start:start2.name,
        end:end2.name,
        num_common_designers,
        common_designers,
        num_common_mechanics,
        common_mechanics,
        num_common_themes,
        common_themes,
        num_common_categories,
        common_categories,
        num_common_families,
        common_families
    }
    
    SORT COUNT(common_elements_array) DESC
    LIMIT 10
    RETURN {
        recommendation:end2.name,
        reasons,
        //-- comment the documents for a simplified table view (for presentation's sake),
        //-- uncomment for full query output.
        //game_data:end2,
        //query_details,
    }
```
Esempio parametri (in JSON perché sono tanti):
```JSON
{
	"game_name": "Mysterium",
	"rating_threshold": 7,
	"weight_threshold": 1,
	"time_margin": 30,
	"exclude_same_family": false,
	"limit_designers": 2,
	"limit_mechanics": 4,
	"limit_themes": 2,
	"limit_categories": 2,
	"limit_families": 2
}
```


## Andamento (percentuale) kickstarter anno per anno
*(Dominio, andamento temporale)*

```sql
FOR g IN Games
    FILTER g.year >= @first_year  //-- Note: kickstarter launched in 2009
    COLLECT year = g.year INTO games_this_year = g
    LET games_tot = COUNT(games_this_year)
    LET games_kicked = COUNT(games_this_year[* FILTER CURRENT.is_kickstarted])
    RETURN {year, games_tot, kickstarter_perc: 100 * games_kicked / games_tot}
```
@first_year <- 2009


## Editori che hanno fatto più kickstarter
*(Dominio)*

```sql
FOR p IN Publishers
    FOR g IN 1..1 INBOUND p HasPublisher
    FILTER g.is_kickstarted
    COLLECT publisher = p WITH COUNT INTO kicked_games
    LET kicked_perc = kicked_games/publisher.number_of_games
    SORT @perc_sort ? kicked_perc : kicked_games DESC  //-- Try both modes!
    RETURN {publisher:publisher.name, kicked_games, kicked_perc}
```
@perc_sort <- true oppure false


## Distribuzione dei giochi per no. di giocatori per categoria
*(Dominio)*

```sql
FOR c IN Categories
    FOR g IN 1..1 INBOUND c InCategory
    //-- Construct an array that contains all integers in the range g.players_mfg (but not more than players_limit)
    LET players_array = (1..@players_limit)[* FILTER g.players_mfg.min <= CURRENT AND CURRENT <= g.players_mfg.max]
    //-- Collect so we get data from all games of each category together
    COLLECT cat = c INTO players_lists = players_array
    //-- Now basically count all occurrences of each number, so we get no. of games per player number
    FOR i IN 1..@players_limit
    COLLECT category = cat INTO players_stats = {
        players:i,
        //--                          v--Compute the fraction of games for each player no. wrt the total---v
        percent_of_games: ROUND(10000*COUNT(FLATTEN(players_lists)[* FILTER CURRENT==i])/cat.number_of_games)/100,
        //--              ^---------^       Convert it to percentage with a limited quantity of digits       ^--^
    }
    //-- Perpare readable version
    LET players_stats_readable = players_stats[* RETURN CONCAT(CURRENT.players, " players: ", CURRENT.percent_of_games, " % ")]
    //-- Done! Select one version
    //-- RETURN {category:category.name, number_of_games:category.number_of_games, players_stats}   //-- technical
    RETURN {category:category.name, number_of_games:category.number_of_games, players_stats_readable}   //-- readable
```
Ad esempio @players_limit <- 12


## Giochi popolari ispirati a film, TV o videogiochi
*(Tecnica: regex)*

```sql
FOR g IN Games
    FILTER g.num_user_ratings > @num_ratings_threshold
    FOR t IN 1..1 OUTBOUND g HasTheme
    FILTER LOWER(t.name) =~ "tv|television|film|movie|cinema|video ?game"
    SORT g.rating_avg DESC
    RETURN {g:g.name, r:g.rating_avg, rn:g.num_user_ratings, t:t.name}
```
Ad esempio @num_ratings_threshold <- 5000


## Giochi brutti che hanno in molti
*(Dominio)*

```sql
FOR g IN Games
    FILTER g.num_owned > 1000 AND g.rating_avg < 4
    RETURN {name:g.name, owned:g.num_owned, rating:g.rating_avg}
```


## Peso medio per durata di gioco
*(Variante di una query precedente, ha più senso)*

```sql
for g in Games
    FILTER g.playtime_mfg != null AND g.weight != null
    COLLECT min_playtime = FLOOR(g.playtime_mfg / @time_range_width) * @time_range_width
    AGGREGATE min_weight = MIN(g.weight),
              max_weight = MAX(g.weight),
              avg_weight = AVG(g.weight),
              num_games = COUNT(g.weight)
    LET max_playtime = min_playtime + @time_range_width - 1
    RETURN {
        //-- Display hours for readability, some games can be pretty long
        playtime_range:{min:min_playtime/60, max:(max_playtime+1)/60},
        num_games,
        avg_weight,
        weight_range:{min:min_weight, max:max_weight}
    }
```


## Scrivi in ogni categoria il numero di giochi che vi appartengono
*(Query di scrittura. Viene già eseguita dallo script Python per molti tipi di nodi.)*

```sql
FOR c IN Categories
    FOR g in 1..1 INBOUND c InCategory
    COLLECT cat_key = c._key WITH COUNT INTO num
    UPDATE cat_key WITH {games_no: num} IN Categories
```
