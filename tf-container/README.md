# bcproxy + tf + python + sqlite -container batmudille

Kontin build:

```
docker build --tag bcproxy-tf:0.1 .
```

Kopioi `worlds/example-worlds.tf` => `worlds/worlds.tf` jonne voi laittaa oikeat
tunnarit, tai voi jättää poiskin.

Käynnistä kontti:

```
./bcproxy-tf.sh
```

Tää ei yhdistä battiin automaattisesti että on mahdollisuus käyttää secondaryjä.

tmuxista poistuminen `ctrl-b :kill-session`

## Batmud configuration

Batmud configuration is almost the same as with GgrTF, only eqset added to `sc`:

```
cutter 9999
sc set H:{colorhp}/<maxhp> [{diffhp}] S:{colorsp}/<maxsp> [{diffsp}] E:{colorep}/<maxep> [{diffep}] $:<cash> [{diffcash}] exp:<exp> [{diffexp}] eqset:<eqset>
sc on
prompt PROMPT:>
```


## Python-deviympäristö

[Install UV](https://docs.astral.sh/uv/#getting-started)

``` sh
cd scripts
uv run pre-commit install
```

Editoria varten tarvinee globaalin pyrightin:

``` sh
uv tool install pyright
```

Jos haluaa käsin ajella niin

``` sh
uv run pre-commit
```


## Sekalaisia ohjeita

```
docker run --rm --tty --interactive bcproxy-tf:0.1
```

```
docker run -d --name bcproxy-tf bcproxy-tf:0.1
```

Käynnistä kontti taustalle ja anna sille nimi

```
docker exec -it bcproxy-tf bash
```

Ajaa `bash`-komennon interaktiivisesti kontissa nimeltä `bcproxy-tf`.

```
docker rm --force bcproxy-tf
```

Poistaa kontin `bcproxy-tf`, täytyy tehdä jotta uuden voi käynnistää.

```
docker ps -a
```

Listaa kaikki omalla koneella olevat kontit.

