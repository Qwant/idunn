from enum import Enum


class ZoneType(str, Enum):
    Suburb = "suburb"
    CityDistrict = "city_district"
    City = "city"
    StateDistrict = "state_district"
    State = "state"
    CountryRegion = "country_region"
    Country = "country"
    NonAdministrative = "non_administrative"
