[![GitHub Build](https://travis-ci.org/QwantResearch/idunn.svg?branch=master)](https://github.com/QwantResearch/idunn)
[![GitHub license](https://img.shields.io/github/license/QwantResearch/idunn.svg)](https://github.com/QwantResearch/idunn/blob/master/LICENSE)
[![Docker Pulls](https://img.shields.io/docker/pulls/qwantresearch/idunn.svg)](https://hub.docker.com/r/qwantresearch/idunn/)

# Idunn

- Idunn is an API to get [points-of-interest](https://en.wikipedia.org/wiki/Point_of_interest) information for QwantMaps.
- The POIs are taken from the [mimir](https://github.com/CanalTP/mimirsbrunn) ElasticSearch database.
- Why [Idunn](https://fr.wikipedia.org/wiki/Idunn) ? Because she is the wife of [Bragi](https://fr.wikipedia.org/wiki/Bragi) that is also [the main](https://github.com/CanalTP/mimirsbrunn/tree/master/libs/bragi) mimir API.

## API

- The API provides its OpenAPI schema with:
`GET /schema`

The main endpoints are:
* `/v1/places/{place_id}?lang={lang}&type={type}&verbosity={verbosity}` to get the details of a place (admin, street, address or POI). The `type` parameter belongs to the set `{'admin', 'street', 'address', 'poi'}`. The `verbosity` parameter belongs to the set `{'long', 'short'}`. The default verbosity is `long`.
* `/v1/pois/{poi_id}?lang={lang}` is the deprecated route to get the details of a POI.
* `/v1/status` to get the status of the API and associated ES cluster.
* `/v1/metrics` to get some metrics on the API that give statistics on the number of requests received, the duration of requests... This endpoint can be scraped by Prometheus.

## Running

- The dependencies are managed with [Pipenv](https://github.com/pypa/pipenv).
- To run the api you need to do:
```shell
pipenv install
```
- and then:
```shell
IDUNN_MIMIR_ES=<url_to_MIMIR_ES> IDUNN_WIKI_ES=<url_to_WIKI_ES> pipenv run python app.py
```
- you can query the API on port 5000:
```shell
curl localhost:5000/v1/places/toto?lang=fr&type=poi
```

### Configuration

The configuration can be given from different ways:
 1. a default settings is available in utils/default_settings.yaml
 2. a yaml settings file can be given with an env var IDUNN_CONFIG_FILE
    (the default settings is still loaded and overriden)
 3. specific variable can be overriden with env var. They need to be given like "IDUNN_{var_name}={value}"
    eg IDUNN_MIMIR_ES=...

## Testing

- To run the tests you need the dev dependencies:
`pipenv install --dev`

- Then you can run pytest:
`pipenv run pytest`

Note: this will require docker to be able to spawn an ES cluster.
