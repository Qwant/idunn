## Directions API

### Endpoint

**GET** `/v1/directions/<start_lon>,<start_lat>;<end_lon>,<end_lat>`

* Query parameters
    
    * **`type`**  
    Accepted values:
        * `driving`
        * `cycling`
        * `walking`
        * `publictransport`
        * `driving-traffic` (*deprecated*)  
        For backward compatibility, equivalent to `driving`.
        
    * **`language`**: Default `en`
    
        
### Response examples


#### `cycling` / `driving` / `walking`

<details>
<summary>See the response</summary>

```json
{
    "data": {
        "routes": [
            {
                "distance": 259, 
                "duration": 120, 
                "geometry": {
                    "coordinates": [
                        [
                            2.340258, 
                            48.889997
                        ], 
                        [
                            2.340198, 
                            48.889826
                        ], 
                        [
                            2.340208, 
                            48.889676
                        ], 
                        [
                            2.340491, 
                            48.889691
                        ], 
                        [
                            2.340569, 
                            48.889695
                        ], 
                        [
                            2.340619, 
                            48.889697
                        ], 
                        [
                            2.34139, 
                            48.889731
                        ], 
                        [
                            2.342102, 
                            48.889762
                        ], 
                        [
                            2.342716, 
                            48.889785
                        ], 
                        [
                            2.342943, 
                            48.889792
                        ], 
                        [
                            2.343005, 
                            48.889877
                        ], 
                        [
                            2.343078, 
                            48.889975
                        ]
                    ], 
                    "type": "LineString"
                }, 
                "legs": [
                    {
                        "distance": 259, 
                        "duration": 120, 
                        "steps": [
                            {
                                "distance": 36, 
                                "duration": 58, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.340258, 
                                            48.889997
                                        ], 
                                        [
                                            2.340198, 
                                            48.889826
                                        ], 
                                        [
                                            2.340208, 
                                            48.889676
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Se diriger vers le sud sur la rue Saule", 
                                    "location": [
                                        2.340258, 
                                        48.889997
                                    ], 
                                    "modifier": null, 
                                    "type": "depart"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 200, 
                                "duration": 56, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.340208, 
                                            48.889676
                                        ], 
                                        [
                                            2.340491, 
                                            48.889691
                                        ], 
                                        [
                                            2.340569, 
                                            48.889695
                                        ], 
                                        [
                                            2.340619, 
                                            48.889697
                                        ], 
                                        [
                                            2.34139, 
                                            48.889731
                                        ], 
                                        [
                                            2.342102, 
                                            48.889762
                                        ], 
                                        [
                                            2.342716, 
                                            48.889785
                                        ], 
                                        [
                                            2.342943, 
                                            48.889792
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à gauche sur la rue Caulaincourt", 
                                    "location": [
                                        2.340208, 
                                        48.889676
                                    ], 
                                    "modifier": "left", 
                                    "type": "turn"
                                }, 
                                "mode": "BICYCLE", 
                                "stops": []
                            }, 
                            {
                                "distance": 22, 
                                "duration": 5, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.342943, 
                                            48.889792
                                        ], 
                                        [
                                            2.343005, 
                                            48.889877
                                        ], 
                                        [
                                            2.343078, 
                                            48.889975
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à gauche sur la rue du Mont Cenis", 
                                    "location": [
                                        2.342943, 
                                        48.889792
                                    ], 
                                    "modifier": "left", 
                                    "type": "turn"
                                }, 
                                "mode": "BICYCLE", 
                                "stops": []
                            }, 
                            {
                                "distance": 0, 
                                "duration": 0, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.343078, 
                                            48.889975
                                        ], 
                                        [
                                            2.343078, 
                                            48.889975
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Vous êtes arrivé à votre destination, sur la gauche", 
                                    "location": [
                                        2.343078, 
                                        48.889975
                                    ], 
                                    "modifier": "left", 
                                    "type": "arrive"
                                }, 
                                "mode": "BICYCLE", 
                                "stops": []
                            }
                        ], 
                        "summary": "Rue Saule, Rue Caulaincourt"
                    }
                ], 
                "price": null, 
                "summary": null
            }
        ]
    }, 
    "status": "success"
}
```
</details>

#### `publictransport`

*Some geometries are simplified for readability*


<details>
<summary>See the response</summary>

```json
{
    "data": {
        "routes": [
            {
                "distance": 7524, 
                "duration": 1680, 
                "geometry": {
                    "features": [
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.340236, 
                                        48.890073
                                    ], 
                                    [
                                        2.339149, 
                                        48.889738
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.339149, 
                                        48.889738
                                    ], 
                                    [
                                        2.338399, 
                                        48.8844
                                    ], 
                                    [
                                        2.321412, 
                                        48.865489
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "direction": "Mairie d'Issy (Issy-les-Moulineaux)", 
                                "lineColor": "007852", 
                                "mode": "SUBWAY", 
                                "network": "METRO", 
                                "num": "12"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.321412, 
                                        48.865489
                                    ], 
                                    [
                                        2.321194, 
                                        48.865678
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.321194, 
                                        48.865678
                                    ], 
                                    [
                                        2.329095, 
                                        48.86478
                                    ], 
                                    [
                                        2.336574, 
                                        48.862372
                                    ], 
                                    [
                                        2.340973, 
                                        48.86088
                                    ], 
                                    [
                                        2.347933, 
                                        48.85857
                                    ], 
                                    [
                                        2.352074, 
                                        48.857356
                                    ], 
                                    [
                                        2.361334, 
                                        48.855134
                                    ], 
                                    [
                                        2.369219, 
                                        48.852976
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "direction": "Château de Vincennes (Paris)", 
                                "lineColor": "FFCD00", 
                                "mode": "SUBWAY", 
                                "network": "METRO", 
                                "num": "1"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.369219, 
                                        48.852976
                                    ], 
                                    [
                                        2.368521, 
                                        48.853053
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }
                    ], 
                    "type": "FeatureCollection"
                }, 
                "legs": [
                    {
                        "distance": 7524, 
                        "duration": 1680, 
                        "steps": [
                            {
                                "distance": 88, 
                                "duration": 79, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.340236, 
                                            48.890073
                                        ], 
                                        [
                                            2.339149, 
                                            48.889738
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Marcher", 
                                    "location": [
                                        2.340236, 
                                        48.890073
                                    ], 
                                    "modifier": null, 
                                    "type": ""
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 2996, 
                                "duration": 660, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.339149, 
                                            48.889738
                                        ], 
                                        [
                                            2.338399, 
                                            48.8844
                                        ], 
                                        [
                                            2.337214, 
                                            48.882027
                                        ], 
                                        [
                                            2.337827, 
                                            48.878594
                                        ], 
                                        [
                                            2.337909, 
                                            48.876051
                                        ], 
                                        [
                                            2.331805, 
                                            48.876329
                                        ], 
                                        [
                                            2.326695, 
                                            48.875421
                                        ], 
                                        [
                                            2.324612, 
                                            48.869795
                                        ], 
                                        [
                                            2.321412, 
                                            48.865489
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": {
                                    "direction": "Mairie d'Issy (Issy-les-Moulineaux)", 
                                    "lineColor": "007852", 
                                    "network": "METRO", 
                                    "num": "12"
                                }, 
                                "maneuver": {
                                    "instruction": "Prendre le Métro 12", 
                                    "location": [
                                        2.339149, 
                                        48.889738
                                    ], 
                                    "modifier": null, 
                                    "type": ""
                                }, 
                                "mode": "SUBWAY", 
                                "stops": [
                                    {
                                        "location": [
                                            2.339149, 
                                            48.889738
                                        ], 
                                        "name": "Lamarck-Caulaincourt (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.338399, 
                                            48.8844
                                        ], 
                                        "name": "Abbesses (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.337214, 
                                            48.882027
                                        ], 
                                        "name": "Pigalle (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.337827, 
                                            48.878594
                                        ], 
                                        "name": "Saint-Georges (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.337909, 
                                            48.876051
                                        ], 
                                        "name": "Notre-Dame de Lorette (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.331805, 
                                            48.876329
                                        ], 
                                        "name": "Trinité-d'Estienne d'Orves (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.326695, 
                                            48.875421
                                        ], 
                                        "name": "Saint-Lazare (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.324612, 
                                            48.869795
                                        ], 
                                        "name": "Madeleine (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.321412, 
                                            48.865489
                                        ], 
                                        "name": "Concorde (Paris)"
                                    }
                                ]
                            }, 
                            {
                                "distance": 27, 
                                "duration": 252, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.321412, 
                                            48.865489
                                        ], 
                                        [
                                            2.321194, 
                                            48.865678
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Marcher", 
                                    "location": [
                                        2.321412, 
                                        48.865489
                                    ], 
                                    "modifier": null, 
                                    "type": ""
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 3791, 
                                "duration": 600, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.321194, 
                                            48.865678
                                        ], 
                                        [
                                            2.329095, 
                                            48.86478
                                        ], 
                                        [
                                            2.336574, 
                                            48.862372
                                        ], 
                                        [
                                            2.340973, 
                                            48.86088
                                        ], 
                                        [
                                            2.347933, 
                                            48.85857
                                        ], 
                                        [
                                            2.352074, 
                                            48.857356
                                        ], 
                                        [
                                            2.361334, 
                                            48.855134
                                        ], 
                                        [
                                            2.369219, 
                                            48.852976
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": {
                                    "direction": "Château de Vincennes (Paris)", 
                                    "lineColor": "FFCD00", 
                                    "network": "METRO", 
                                    "num": "1"
                                }, 
                                "maneuver": {
                                    "instruction": "Prendre le Métro 1", 
                                    "location": [
                                        2.321194, 
                                        48.865678
                                    ], 
                                    "modifier": null, 
                                    "type": ""
                                }, 
                                "mode": "SUBWAY", 
                                "stops": [
                                    {
                                        "location": [
                                            2.321194, 
                                            48.865678
                                        ], 
                                        "name": "Concorde (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.329095, 
                                            48.86478
                                        ], 
                                        "name": "Tuileries (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.336574, 
                                            48.862372
                                        ], 
                                        "name": "Palais-Royal (Musée du Louvre) (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.340973, 
                                            48.86088
                                        ], 
                                        "name": "Louvre-Rivoli (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.347933, 
                                            48.85857
                                        ], 
                                        "name": "Châtelet (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.352074, 
                                            48.857356
                                        ], 
                                        "name": "Hôtel de Ville (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.361334, 
                                            48.855134
                                        ], 
                                        "name": "Saint-Paul (le Marais) (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.369219, 
                                            48.852976
                                        ], 
                                        "name": "Bastille (Paris)"
                                    }
                                ]
                            }, 
                            {
                                "distance": 52, 
                                "duration": 47, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.369219, 
                                            48.852976
                                        ], 
                                        [
                                            2.368521, 
                                            48.853053
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Marcher", 
                                    "location": [
                                        2.369219, 
                                        48.852976
                                    ], 
                                    "modifier": null, 
                                    "type": ""
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }
                        ], 
                        "summary": "WALK-SUBWAY#12#METRO-WALK-SUBWAY#1#METRO-WALK-"
                    }
                ], 
                "price": {
                    "currency": "EUR", 
                    "group": false, 
                    "value": "1.9"
                }, 
                "summary": [
                    {
                        "distance": 88, 
                        "duration": 79, 
                        "info": null, 
                        "mode": "WALK"
                    }, 
                    {
                        "distance": 2996, 
                        "duration": 660, 
                        "info": {
                            "direction": "Mairie d'Issy (Issy-les-Moulineaux)", 
                            "lineColor": "007852", 
                            "network": "METRO", 
                            "num": "12"
                        }, 
                        "mode": "SUBWAY"
                    }, 
                    {
                        "distance": 27, 
                        "duration": 252, 
                        "info": null, 
                        "mode": "WALK"
                    }, 
                    {
                        "distance": 3791, 
                        "duration": 600, 
                        "info": {
                            "direction": "Château de Vincennes (Paris)", 
                            "lineColor": "FFCD00", 
                            "network": "METRO", 
                            "num": "1"
                        }, 
                        "mode": "SUBWAY"
                    }, 
                    {
                        "distance": 52, 
                        "duration": 47, 
                        "info": null, 
                        "mode": "WALK"
                    }
                ]
            }, 
            {
                "distance": 5823, 
                "duration": 4876, 
                "geometry": {
                    "features": [
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.34028, 
                                        48.89007
                                    ], 
                                    [
                                        2.3402, 
                                        48.88983
                                    ], 
                                    [
                                        2.34021, 
                                        48.88968
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.34021, 
                                        48.88968
                                    ], 
                                    [
                                        2.34049, 
                                        48.88969
                                    ], 
                                    [
                                        2.34294, 
                                        48.88979
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.34294, 
                                        48.88979
                                    ], 
                                    [
                                        2.34302, 
                                        48.88977
                                    ], 
                                    [
                                        2.34457, 
                                        48.88934
                                    ], 
                                    [
                                        2.3447, 
                                        48.88931
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.3447, 
                                        48.88931
                                    ], 
                                    [
                                        2.34491, 
                                        48.88925
                                    ], 
                                    [
                                        2.34792, 
                                        48.88842
                                    ], 
                                    [
                                        2.348, 
                                        48.8884
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.348, 
                                        48.8884
                                    ], 
                                    [
                                        2.34819, 
                                        48.88839
                                    ], 
                                    [
                                        2.34942, 
                                        48.88836
                                    ], 
                                    [
                                        2.34946, 
                                        48.88836
                                    ], 
                                    [
                                        2.34959, 
                                        48.88836
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.34959, 
                                        48.88836
                                    ], 
                                    [
                                        2.34959, 
                                        48.88827
                                    ], 
                                    [
                                        2.34958, 
                                        48.88789
                                    ], 
                                    [
                                        2.34957, 
                                        48.88783
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.34937, 
                                        48.887832
                                    ], 
                                    [
                                        2.349288, 
                                        48.884094
                                    ], 
                                    [
                                        2.351726, 
                                        48.880876
                                    ], 
                                    [
                                        2.35347, 
                                        48.878916
                                    ], 
                                    [
                                        2.356166, 
                                        48.875851
                                    ], 
                                    [
                                        2.360483, 
                                        48.871114
                                    ], 
                                    [
                                        2.362431, 
                                        48.869011
                                    ], 
                                    [
                                        2.364936, 
                                        48.867141
                                    ], 
                                    [
                                        2.365494, 
                                        48.866359
                                    ], 
                                    [
                                        2.36785, 
                                        48.864965
                                    ], 
                                    [
                                        2.370329, 
                                        48.8635
                                    ], 
                                    [
                                        2.374332, 
                                        48.861108
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "direction": "Château de Vincennes (Paris)", 
                                "lineColor": "A0006E", 
                                "mode": "BUS_CITY", 
                                "network": "RATP", 
                                "num": "56"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.37444, 
                                        48.86119
                                    ], 
                                    [
                                        2.37451, 
                                        48.86115
                                    ], 
                                    [
                                        2.37549, 
                                        48.86055
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.37549, 
                                        48.86055
                                    ], 
                                    [
                                        2.37546, 
                                        48.86049
                                    ], 
                                    [
                                        2.37584, 
                                        48.85944
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.37584, 
                                        48.85944
                                    ], 
                                    [
                                        2.37578, 
                                        48.85942
                                    ], 
                                    [
                                        2.37195, 
                                        48.85814
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.37195, 
                                        48.85814
                                    ], 
                                    [
                                        2.37179, 
                                        48.85809
                                    ], 
                                    [
                                        2.37166, 
                                        48.85804
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.37166, 
                                        48.85804
                                    ], 
                                    [
                                        2.37154, 
                                        48.85798
                                    ], 
                                    [
                                        2.3684, 
                                        48.85699
                                    ], 
                                    [
                                        2.36822, 
                                        48.85694
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.36822, 
                                        48.85694
                                    ], 
                                    [
                                        2.36824, 
                                        48.85689
                                    ], 
                                    [
                                        2.3687, 
                                        48.85495
                                    ], 
                                    [
                                        2.36873, 
                                        48.85482
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.36873, 
                                        48.85482
                                    ], 
                                    [
                                        2.36854, 
                                        48.85481
                                    ], 
                                    [
                                        2.36816, 
                                        48.8548
                                    ], 
                                    [
                                        2.36811, 
                                        48.8548
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.36811, 
                                        48.8548
                                    ], 
                                    [
                                        2.36812, 
                                        48.85476
                                    ], 
                                    [
                                        2.36815, 
                                        48.85426
                                    ], 
                                    [
                                        2.36817, 
                                        48.85386
                                    ], 
                                    [
                                        2.36817, 
                                        48.85382
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.36817, 
                                        48.85382
                                    ], 
                                    [
                                        2.36822, 
                                        48.85382
                                    ], 
                                    [
                                        2.36826, 
                                        48.85381
                                    ], 
                                    [
                                        2.36856, 
                                        48.85376
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.36856, 
                                        48.85376
                                    ], 
                                    [
                                        2.36855, 
                                        48.85373
                                    ], 
                                    [
                                        2.36815, 
                                        48.85294
                                    ], 
                                    [
                                        2.36815, 
                                        48.85292
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }, 
                        {
                            "geometry": {
                                "coordinates": [
                                    [
                                        2.36815, 
                                        48.85292
                                    ], 
                                    [
                                        2.36849, 
                                        48.853
                                    ]
                                ], 
                                "type": "LineString"
                            }, 
                            "properties": {
                                "mode": "WALK"
                            }, 
                            "type": "Feature"
                        }
                    ], 
                    "type": "FeatureCollection"
                }, 
                "legs": [
                    {
                        "distance": 5823, 
                        "duration": 4876, 
                        "steps": [
                            {
                                "distance": 44, 
                                "duration": 30, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.34028, 
                                            48.89007
                                        ], 
                                        [
                                            2.3402, 
                                            48.88983
                                        ], 
                                        [
                                            2.34021, 
                                            48.88968
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Se diriger vers le sud sur la rue Saule", 
                                    "location": [
                                        2.34028, 
                                        48.89007
                                    ], 
                                    "modifier": null, 
                                    "type": "depart"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 201, 
                                "duration": 141, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.34021, 
                                            48.88968
                                        ], 
                                        [
                                            2.34049, 
                                            48.88969
                                        ], 
                                        [
                                            2.34294, 
                                            48.88979
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à gauche sur la rue Caulaincourt", 
                                    "location": [
                                        2.34021, 
                                        48.88968
                                    ], 
                                    "modifier": "left", 
                                    "type": "turn"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 140, 
                                "duration": 98, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.34294, 
                                            48.88979
                                        ], 
                                        [
                                            2.34302, 
                                            48.88977
                                        ], 
                                        [
                                            2.34457, 
                                            48.88934
                                        ], 
                                        [
                                            2.3447, 
                                            48.88931
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Continuer tout droit sur la rue Custine", 
                                    "location": [
                                        2.34294, 
                                        48.88979
                                    ], 
                                    "modifier": "straight", 
                                    "type": "new name"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 262, 
                                "duration": 185, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.3447, 
                                            48.88931
                                        ], 
                                        [
                                            2.34491, 
                                            48.88925
                                        ], 
                                        [
                                            2.348, 
                                            48.8884
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tenir la droite sur la rue Custine", 
                                    "location": [
                                        2.3447, 
                                        48.88931
                                    ], 
                                    "modifier": "slight right", 
                                    "type": "fork"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 117, 
                                "duration": 84, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.348, 
                                            48.8884
                                        ], 
                                        [
                                            2.34819, 
                                            48.88839
                                        ], 
                                        [
                                            2.34942, 
                                            48.88836
                                        ], 
                                        [
                                            2.34946, 
                                            48.88836
                                        ], 
                                        [
                                            2.34959, 
                                            48.88836
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Continuer tout droit sur la rue Doudeauville", 
                                    "location": [
                                        2.348, 
                                        48.8884
                                    ], 
                                    "modifier": "straight", 
                                    "type": "new name"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 60, 
                                "duration": 41, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.34959, 
                                            48.88836
                                        ], 
                                        [
                                            2.34959, 
                                            48.88827
                                        ], 
                                        [
                                            2.34958, 
                                            48.88789
                                        ], 
                                        [
                                            2.34957, 
                                            48.88783
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à droite sur le boulevard Barbès", 
                                    "location": [
                                        2.34959, 
                                        48.88836
                                    ], 
                                    "modifier": "right", 
                                    "type": "turn"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 3492, 
                                "duration": 1560, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.34937, 
                                            48.887832
                                        ], 
                                        [
                                            2.349288, 
                                            48.884094
                                        ], 
                                        [
                                            2.351726, 
                                            48.880876
                                        ], 
                                        [
                                            2.35347, 
                                            48.878916
                                        ], 
                                        [
                                            2.356166, 
                                            48.875851
                                        ], 
                                        [
                                            2.360483, 
                                            48.871114
                                        ], 
                                        [
                                            2.362431, 
                                            48.869011
                                        ], 
                                        [
                                            2.364936, 
                                            48.867141
                                        ], 
                                        [
                                            2.365494, 
                                            48.866359
                                        ], 
                                        [
                                            2.36785, 
                                            48.864965
                                        ], 
                                        [
                                            2.370329, 
                                            48.8635
                                        ], 
                                        [
                                            2.374332, 
                                            48.861108
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": {
                                    "direction": "Château de Vincennes (Paris)", 
                                    "lineColor": "A0006E", 
                                    "network": "RATP", 
                                    "num": "56"
                                }, 
                                "maneuver": {
                                    "instruction": "Prendre le Bus 56", 
                                    "location": [
                                        2.34937, 
                                        48.887832
                                    ], 
                                    "modifier": null, 
                                    "type": ""
                                }, 
                                "mode": "BUS_CITY", 
                                "stops": [
                                    {
                                        "location": [
                                            2.34937, 
                                            48.887832
                                        ], 
                                        "name": "Château Rouge (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.349288, 
                                            48.884094
                                        ], 
                                        "name": "Barbes - Rochechouart (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.351726, 
                                            48.880876
                                        ], 
                                        "name": "Magenta - Maubeuge - Gare du Nord (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.35347, 
                                            48.878916
                                        ], 
                                        "name": "La Fayette - Magenta - Gare du Nord (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.356166, 
                                            48.875851
                                        ], 
                                        "name": "Magenta-Gare de l'Est (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.360483, 
                                            48.871114
                                        ], 
                                        "name": "Jacques Bonsergent (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.362431, 
                                            48.869011
                                        ], 
                                        "name": "République - Magenta (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.364936, 
                                            48.867141
                                        ], 
                                        "name": "République (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.365494, 
                                            48.866359
                                        ], 
                                        "name": "République - Voltaire (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.36785, 
                                            48.864965
                                        ], 
                                        "name": "Jean-Pierre Timbaud (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.370329, 
                                            48.8635
                                        ], 
                                        "name": "Oberkampf - Richard Lenoir (Paris)"
                                    }, 
                                    {
                                        "location": [
                                            2.374332, 
                                            48.861108
                                        ], 
                                        "name": "Saint-Ambroise (Paris)"
                                    }
                                ]
                            }, 
                            {
                                "distance": 105, 
                                "duration": 74, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.37444, 
                                            48.86119
                                        ], 
                                        [
                                            2.37451, 
                                            48.86115
                                        ], 
                                        [
                                            2.37537, 
                                            48.86063
                                        ], 
                                        [
                                            2.37549, 
                                            48.86055
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Se diriger vers le sud-est sur le boulevard Voltaire", 
                                    "location": [
                                        2.37444, 
                                        48.86119
                                    ], 
                                    "modifier": null, 
                                    "type": "depart"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 127, 
                                "duration": 92, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.37549, 
                                            48.86055
                                        ], 
                                        [
                                            2.37546, 
                                            48.86049
                                        ], 
                                        [
                                            2.37545, 
                                            48.86045
                                        ], 
                                        [
                                            2.37555, 
                                            48.86017
                                        ], 
                                        [
                                            2.37557, 
                                            48.86012
                                        ], 
                                        [
                                            2.37571, 
                                            48.85977
                                        ], 
                                        [
                                            2.37581, 
                                            48.85951
                                        ], 
                                        [
                                            2.37582, 
                                            48.85948
                                        ], 
                                        [
                                            2.37584, 
                                            48.85944
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à droite sur la rue Popincourt", 
                                    "location": [
                                        2.37549, 
                                        48.86055
                                    ], 
                                    "modifier": "right", 
                                    "type": "turn"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 320, 
                                "duration": 224, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.37584, 
                                            48.85944
                                        ], 
                                        [
                                            2.37578, 
                                            48.85942
                                        ], 
                                        [
                                            2.37195, 
                                            48.85814
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à droite sur la rue du Chemin Vert", 
                                    "location": [
                                        2.37584, 
                                        48.85944
                                    ], 
                                    "modifier": "right", 
                                    "type": "turn"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 24, 
                                "duration": 16, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.37195, 
                                            48.85814
                                        ], 
                                        [
                                            2.37179, 
                                            48.85809
                                        ], 
                                        [
                                            2.37166, 
                                            48.85804
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Continuer tout droit", 
                                    "location": [
                                        2.37195, 
                                        48.85814
                                    ], 
                                    "modifier": "straight", 
                                    "type": "new name"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 281, 
                                "duration": 203, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.37166, 
                                            48.85804
                                        ], 
                                        [
                                            2.37154, 
                                            48.85798
                                        ], 
                                        [
                                            2.3684, 
                                            48.85699
                                        ], 
                                        [
                                            2.36822, 
                                            48.85694
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tenir la droite sur la rue du Chemin Vert", 
                                    "location": [
                                        2.37166, 
                                        48.85804
                                    ], 
                                    "modifier": "slight right", 
                                    "type": "fork"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 239, 
                                "duration": 169, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.36822, 
                                            48.85694
                                        ], 
                                        [
                                            2.36824, 
                                            48.85689
                                        ], 
                                        [
                                            2.36873, 
                                            48.85482
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à gauche sur le boulevard Beaumarchais", 
                                    "location": [
                                        2.36822, 
                                        48.85694
                                    ], 
                                    "modifier": "left", 
                                    "type": "end of road"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 46, 
                                "duration": 31, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.36873, 
                                            48.85482
                                        ], 
                                        [
                                            2.36854, 
                                            48.85481
                                        ], 
                                        [
                                            2.36816, 
                                            48.8548
                                        ], 
                                        [
                                            2.36811, 
                                            48.8548
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à droite sur la rue Jean Beausire", 
                                    "location": [
                                        2.36873, 
                                        48.85482
                                    ], 
                                    "modifier": "right", 
                                    "type": "turn"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 110, 
                                "duration": 76, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.36811, 
                                            48.8548
                                        ], 
                                        [
                                            2.36812, 
                                            48.85476
                                        ], 
                                        [
                                            2.36815, 
                                            48.85426
                                        ], 
                                        [
                                            2.36817, 
                                            48.85386
                                        ], 
                                        [
                                            2.36817, 
                                            48.85382
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à gauche pour rester sur la rue Jean Beausire", 
                                    "location": [
                                        2.36811, 
                                        48.8548
                                    ], 
                                    "modifier": "left", 
                                    "type": "continue"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 30, 
                                "duration": 20, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.36817, 
                                            48.85382
                                        ], 
                                        [
                                            2.36822, 
                                            48.85382
                                        ], 
                                        [
                                            2.36826, 
                                            48.85381
                                        ], 
                                        [
                                            2.36856, 
                                            48.85376
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à gauche sur la rue de la Bastille", 
                                    "location": [
                                        2.36817, 
                                        48.85382
                                    ], 
                                    "modifier": "left", 
                                    "type": "end of road"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 99, 
                                "duration": 76, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.36856, 
                                            48.85376
                                        ], 
                                        [
                                            2.36855, 
                                            48.85373
                                        ], 
                                        [
                                            2.36815, 
                                            48.85294
                                        ], 
                                        [
                                            2.36815, 
                                            48.85292
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à droite", 
                                    "location": [
                                        2.36856, 
                                        48.85376
                                    ], 
                                    "modifier": "right", 
                                    "type": "turn"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }, 
                            {
                                "distance": 27, 
                                "duration": 19, 
                                "geometry": {
                                    "coordinates": [
                                        [
                                            2.36815, 
                                            48.85292
                                        ], 
                                        [
                                            2.36849, 
                                            48.853
                                        ]
                                    ], 
                                    "type": "LineString"
                                }, 
                                "info": null, 
                                "maneuver": {
                                    "instruction": "Tourner à gauche sur le boulevard Henri IV", 
                                    "location": [
                                        2.36815, 
                                        48.85292
                                    ], 
                                    "modifier": "left", 
                                    "type": "turn"
                                }, 
                                "mode": "WALK", 
                                "stops": []
                            }
                        ], 
                        "summary": "WALK-BUS_CITY#56#RATP-WALK-"
                    }
                ], 
                "price": {
                    "currency": "EUR", 
                    "group": false, 
                    "value": "1.9"
                }, 
                "summary": [
                    {
                        "distance": 824, 
                        "duration": 579, 
                        "info": null, 
                        "mode": "WALK"
                    }, 
                    {
                        "distance": 3492, 
                        "duration": 1560, 
                        "info": {
                            "direction": "Château de Vincennes (Paris)", 
                            "lineColor": "A0006E", 
                            "network": "RATP", 
                            "num": "56"
                        }, 
                        "mode": "BUS_CITY"
                    }, 
                    {
                        "distance": 1408, 
                        "duration": 1000, 
                        "info": null, 
                        "mode": "WALK"
                    }
                ]
            }
        ]
    }, 
    "status": "success"
}
```
</details>
