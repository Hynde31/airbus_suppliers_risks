# suppliers_data.py — structure complète des fournisseurs, sites, risques, incidents...

SUPPLIERS = [
    {
        "name": "Safran",
        "component": "Engine",
        "criticality": "High",
        "dual_sourcing": False,
        "sites": [
            {
                "city": "Paris",
                "country": "France",
                "lat": 48.8566,
                "lon": 2.3522,
                "stock_days": 14,
                "lead_time": 90,
                "on_time_delivery": 96,
                "incidents": 2
            },
            {
                "city": "Casablanca",
                "country": "Morocco",
                "lat": 33.5731,
                "lon": -7.5898,
                "stock_days": 7,
                "lead_time": 110,
                "on_time_delivery": 92,
                "incidents": 3
            },
        ]
    },
    {
        "name": "Spirit AeroSystems",
        "component": "Fuselage",
        "criticality": "High",
        "dual_sourcing": False,
        "sites": [
            {
                "city": "Wichita",
                "country": "USA",
                "lat": 37.6872,
                "lon": -97.3301,
                "stock_days": 10,
                "lead_time": 120,
                "on_time_delivery": 85,
                "incidents": 5
            },
        ]
    },
    {
        "name": "Liebherr",
        "component": "Landing Gear",
        "criticality": "Medium",
        "dual_sourcing": True,
        "sites": [
            {
                "city": "Lindenberg",
                "country": "Germany",
                "lat": 47.6029,
                "lon": 10.0113,
                "stock_days": 30,
                "lead_time": 80,
                "on_time_delivery": 90,
                "incidents": 1
            },
        ]
    },
    {
        "name": "Collins Aerospace",
        "component": "Avionics",
        "criticality": "Medium",
        "dual_sourcing": True,
        "sites": [
            {
                "city": "Cedar Rapids",
                "country": "USA",
                "lat": 41.9779,
                "lon": -91.6656,
                "stock_days": 22,
                "lead_time": 95,
                "on_time_delivery": 88,
                "incidents": 2
            },
        ]
    },
    {
        "name": "Honeywell",
        "component": "Electrical Systems",
        "criticality": "Low",
        "dual_sourcing": True,
        "sites": [
            {
                "city": "San Jose",
                "country": "USA",
                "lat": 37.3382,
                "lon": -121.8863,
                "stock_days": 18,
                "lead_time": 60,
                "on_time_delivery": 94,
                "incidents": 4
            }
        ]
    }
]
