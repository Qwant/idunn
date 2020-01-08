"""
Implement GeocodeJson specification as defined here:
https://github.com/geocoders/geocodejson-spec/tree/master/draft
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, PositiveInt


class FeaturePropertiesGeocoding(BaseModel):
    type: str
    accuracy: Optional[PositiveInt]
    label: Optional[str]
    name: Optional[str]
    housenumber: Optional[str]
    street: Optional[str]
    locality: Optional[str]
    postcode: Optional[str]
    city: Optional[str]
    district: Optional[str]
    country: Optional[str]
    state: Optional[str]
    country: Optional[str]
    admin: dict = {}
    geohash: Optional[str]

class FeatureProperties(BaseModel):
    geocoding: FeaturePropertiesGeocoding

class Feature(BaseModel):
    type: str = 'Feature'
    geometry: dict
    properties: FeatureProperties

class Geocoding(BaseModel):
    version: str = '0.1.0'
    licence: Optional[str]
    attribution: Optional[str]
    query: Optional[str]

class GeocodeJson(BaseModel):
    type: str = 'FeatureCollection'
    geocoding: Geocoding = Geocoding()
    features: List[Feature]
