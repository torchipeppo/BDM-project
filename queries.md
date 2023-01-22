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



# TODO

* Tecnica: percorsi su grafo
* "gradi di separazione"
* "Mi è piaciuto molto QUESTO gioco da tavolo, me ne dici qualcuno con caratteristiche simili (e.g. meccaniche) e un alto rating?"
  (forse se uso un named graph posso mettere più categorie di nodi... anche i designer, magari)
  (tanto il grafo è bipartito :/ )
