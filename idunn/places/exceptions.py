class IdunnPlaceError(Exception):
    message = "Idunn place error"


class InvalidPlaceId(IdunnPlaceError):
    def __init__(self, place_id):
        self.id = place_id
        self.message = f"Invalid place id: '{place_id}'"


class RedirectToPlaceId(IdunnPlaceError):
    def __init__(self, target_id):
        self.target_id = target_id
        self.message = f"Place redirected to '{target_id}'"


class PlaceNotFound(IdunnPlaceError):
    message = "Place not found"

    def __init__(self, message=None):
        if message:
            self.message = message
