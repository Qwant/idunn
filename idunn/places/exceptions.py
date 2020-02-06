class InvalidPlaceId(ValueError):
    def __init__(self, place_id):
        self.id = place_id
        self.message = f"Invalid place id: '{place_id}'"
        super().__init__(self.message)
