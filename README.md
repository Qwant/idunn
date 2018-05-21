# Idunn

Idunn is an API to get [POI](https://en.wikipedia.org/wiki/Point_of_interest) information for QwantMaps.

The POIs are taken from the [mimir](https://github.com/CanalTP/mimirsbrunn) ElasticSearch database.

## API

The API provides its OpenAPI schema with:
`GET /schema`

The main endpoints are:

* `/v1/poi/{poi_id}?lang={lang}` to get the detail of a POI.


## Running

The dependencies are managed with [Pipenv](https://github.com/pypa/pipenv).

To run the api you need to do:
`pipenv install`

and then
`ES_URL=<url_to_elasticsearch> pipenv run python app.py`

you can query the API on 4000:
`curl localhost:5000/v1/poi/toto?lang=fr`

## Testing

To run the tests you need the dev dependencies:
`pipenv install --dev`

Then you can run pytest:
`pipenv run pytest tests`

Note: this will require docker to be able to spawn an ES cluster.

## Why "Idunn"

[Idunn](https://fr.wikipedia.org/wiki/Idunn) is the wife of [Bragi](https://fr.wikipedia.org/wiki/Bragi) that is also [the main](https://github.com/CanalTP/mimirsbrunn/tree/master/libs/bragi) mimir API.
