from .settings import settings


INDICES = {
    "admin": settings["PLACE_ADMIN_INDEX"],
    "street": settings["PLACE_STREET_INDEX"],
    "address": settings["PLACE_ADDRESS_INDEX"],
    "poi": settings["PLACE_POI_INDEX"],
    "poi-tripadvisor": settings["PLACE_POI_TRIPADVISOR_INDEX"],
}
