# Idunn

Idunn is an API to get [POI](https://en.wikipedia.org/wiki/Point_of_interest) information for QwantMaps.

The POIs are taken from the [mimir](https://github.com/CanalTP/mimirsbrunn) ElasticSearch database.

## API

The API provides its OpenAPI schema with:
`GET /schema`

The main endpoints are:

* `/v1/pois/{poi_id}?lang={lang}` to get the detail of a POI.


## Running

The dependencies are managed with [Pipenv](https://github.com/pypa/pipenv).

To run the api you need to do:
`pipenv install`

and then
`IDUNN_ES_URL=<url_to_elasticsearch> pipenv run python app.py`

you can query the API on 4000:
`curl localhost:5000/v1/pois/toto?lang=fr`

### Configuration

The configuration can be given from different ways:
 1. a default settings is available in utils/default_settings.yaml
 2. a yaml settings file can be given with an env var IDUNN_CONFIG_FILE
    (the default settings is still loaded and overriden)
 3. specific variable can be overriden with env var. They need to be given like "IDUNN_{var_name}={value}"
    eg IDUNN_ES_URL=...

## Testing

To run the tests you need the dev dependencies:
`pipenv install --dev`

Then you can run pytest:
`pipenv run pytest tests`

Note: this will require docker to be able to spawn an ES cluster.

## Why "Idunn"

[Idunn](https://fr.wikipedia.org/wiki/Idunn) is the wife of [Bragi](https://fr.wikipedia.org/wiki/Bragi) that is also [the main](https://github.com/CanalTP/mimirsbrunn/tree/master/libs/bragi) mimir API.
