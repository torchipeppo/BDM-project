## Tutti i giochi di una certa famiglia
*(Query semplice)*

```sql
FOR f IN Families
    FILTER f.name == @family
    FOR g IN 1..1 INBOUND f InFamily
    RETURN g.name
```
Ad esempio, @family <- "Pandemic"


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
*(Tecnica: COLLECT, AGGREGATE)*

```sql
for g in Games
    COLLECT age = g.age_mfg
    AGGREGATE min_weight = MIN(g.weight),
              max_weight = MAX(g.weight),
              avg_weight = AVG(g.weight),
              num_games = COUNT(g.weight)
    RETURN {
        age, num_games, min_weight, avg_weight, max_weight
    }
```


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
        COLLECT theme = t.name AGGREGATE num = COUNT(g.name)
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


## 6 Gradi di Rodger MacGowan
*(Analisi grafo, dominio)*

```sql
FOR a IN Artists
    FOR rodger IN Artists
    FILTER rodger.name=="Rodger B. MacGowan"
    FOR v, e IN ANY SHORTEST_PATH a TO rodger HasArtist
    COLLECT start=a.name INTO path={name:v.name, is_game:IS_SAME_COLLECTION("Games", v)}
    LET degrees_of_separation = COUNT(path[* FILTER CURRENT.is_game])
    SORT degrees_of_separation DESC
    RETURN {start, degrees_of_separation, path:path[*].name}
```
N.B.: Scelto lui perché è l'artista che ha illustrato più giochi. Trovato con banale query:

`FOR a IN Artists SORT a.number_of_games DESC RETURN a`


# TODO

* Tecnica: K_PATHS, SHORTEST_PATH, K_SHORTEST_PATHS
* Tecnica: regex?
* "gradi di separazione" (artisti? meccaniche? publisher? temi?)
* "Mi è piaciuto molto QUESTO gioco da tavolo, me ne dici qualcuno con caratteristiche simili (e.g. meccaniche) e un alto rating?"
  (forse se uso un named graph posso mettere più categorie di nodi... anche i designer, magari)
  (tanto il grafo è bipartito :/ )


## Scrivi in ogni categoria il numero di giochi che vi appartengono
*(Query di scrittura. Viene già eseguita dallo script Python per molti tipi di nodi.)*

```sql
FOR c IN Categories
    FOR g in 1..1 INBOUND c InCategory
    COLLECT cat_key = c._key WITH COUNT INTO num
    UPDATE cat_key WITH {games_no: num} IN Categories
```
