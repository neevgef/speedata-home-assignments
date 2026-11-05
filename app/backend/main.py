# Imports
import os
import logging

from fastapi import FastAPI
import requests
import uvicorn

# Environment Variables
BACKEND_HOST = os.getenv("BACKEND_HOST", '0.0.0.0')
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
logger = logging.getLogger(__name__)



# Initialize FastAPI Application
app = FastAPI()


@app.get("/weather", name="Get Weather")
async def get_weather(city: str):
    # Step 1: Convert the city name to latitude and longitude
    
    geo_params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    
    try:
        geo_response = requests.get(GEOCODING_URL, params=geo_params, timeout=100)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
    except requests.RequestException as error:
        logger.exception("Geocoding API request failed when fetching coordinates for city: %s", city)
        logger.exception("Error details: %s", error)
        return {"error": f"Failed to fetch weather data for {city}, please try again later."}

    if not geo_data.get("results"):
        return {"error": f"City {city} not found."}

    # Extract coordinates and structural details
    location = geo_data["results"][0]
    lat = location["latitude"]
    lon = location["longitude"]
    full_name = f"{location['name']}, {location.get('country', '')}"

    # Step 2: Fetch the current temperature using the coordinates
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
        "timezone": "auto"
    }

    try:
        weather_response = requests.get(FORECAST_URL, params=weather_params, timeout=100)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
    except requests.RequestException as error:
        logger.exception("Weather API forecast request failed for city: %s", city)
        logger.exception("Error details: %s", error)
        return {"error": f"Failed to fetch weather data for {city}, please try again later."}
    
    # Extract the temperature and corresponding unit
    current_temp = weather_data["current"]["temperature_2m"]
    temp_unit = weather_data["current_units"]["temperature_2m"]
    
    return f"The current temperature in {full_name} is {current_temp}{temp_unit}."
    

@app.get("/health", name="Health Check")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True, log_level=LOG_LEVEL)
