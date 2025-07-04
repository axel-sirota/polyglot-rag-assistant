"""OpenAI function definitions for flight search and other tools"""

# For Realtime API, tools need a different format
REALTIME_FLIGHT_SEARCH_FUNCTION = {
    "name": "search_flights",
    "description": "Search for flights between airports with real-time pricing and availability",
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {
                "type": "string", 
                "description": "Origin airport IATA code or city name (e.g., 'JFK' or 'New York')"
            },
            "destination": {
                "type": "string", 
                "description": "Destination airport IATA code or city name (e.g., 'LAX' or 'Los Angeles')"
            },
            "departure_date": {
                "type": "string", 
                "description": "Departure date in YYYY-MM-DD format"
            },
            "return_date": {
                "type": "string", 
                "description": "Optional return date in YYYY-MM-DD format for round trips"
            },
            "passengers": {
                "type": "integer", 
                "minimum": 1, 
                "maximum": 9,
                "description": "Number of passengers"
            },
            "cabin_class": {
                "type": "string", 
                "enum": ["economy", "premium", "business", "first"],
                "description": "Cabin class preference"
            }
        },
        "required": ["origin", "destination", "departure_date"]
    }
}

# Flight search function definition for Chat Completions API (standard pipeline)
FLIGHT_SEARCH_FUNCTION = {
    "type": "function",
    "function": REALTIME_FLIGHT_SEARCH_FUNCTION
}

# For Realtime API
REALTIME_GET_AIRPORT_CODE_FUNCTION = {
    "name": "get_airport_code",
    "description": "Convert a city name to its primary airport IATA code",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name to convert to airport code"
            }
        },
        "required": ["city"]
    }
}

# For Realtime API
REALTIME_GET_FLIGHT_DETAILS_FUNCTION = {
    "name": "get_flight_details",
    "description": "Get detailed information about a specific flight",
    "parameters": {
        "type": "object",
        "properties": {
            "flight_id": {
                "type": "string",
                "description": "Unique identifier for the flight"
            }
        },
        "required": ["flight_id"]
    }
}

# Get airport code function definition for Chat Completions
GET_AIRPORT_CODE_FUNCTION = {
    "type": "function",
    "function": REALTIME_GET_AIRPORT_CODE_FUNCTION
}

# Get flight details function definition for Chat Completions
GET_FLIGHT_DETAILS_FUNCTION = {
    "type": "function",
    "function": REALTIME_GET_FLIGHT_DETAILS_FUNCTION
}

# All available functions for Chat Completions API (standard pipeline)
ALL_FUNCTIONS = [
    FLIGHT_SEARCH_FUNCTION,
    GET_AIRPORT_CODE_FUNCTION,
    GET_FLIGHT_DETAILS_FUNCTION
]

# All available functions for Realtime API
REALTIME_FUNCTIONS = [
    REALTIME_FLIGHT_SEARCH_FUNCTION,
    REALTIME_GET_AIRPORT_CODE_FUNCTION,
    REALTIME_GET_FLIGHT_DETAILS_FUNCTION
]