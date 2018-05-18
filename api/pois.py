

def fetch_es_poi(id, lang) -> dict:
    # TODO!
    return {'name': 'toto', 'id': id, 'lang': lang}


def make_response(es_poi):
    # TODO!
    return es_poi


def get_poi(id, lang):
    es_poi = fetch_es_poi(id, lang)

    return make_response(es_poi)
