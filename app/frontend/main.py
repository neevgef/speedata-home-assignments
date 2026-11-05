import os
import requests
from flask import Flask, render_template_string, request

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/weather")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))


# Initialize the Flask application.
app = Flask(__name__)

# HTML template for the main page rendered by the Flask application.
PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SkyWatch</title>
  </head>
  <body>
    <main>
      <h1>SkyWatch</h1>
      <form method="post">
        <label for="city">Enter a city to get the current weather:</label>
        <input id="city" name="city" type="text" value="{{ city }}"
               placeholder="Enter city name" required>
        <button type="submit">Submit</button>
      </form>
      {% if result %}<p role="status">{{ result }}</p>{% endif %}
      {% if error %}<p role="alert">{{ error }}</p>{% endif %}
    </main>
  </body>
</html>
"""


def get_weather(city_name):
    """
    Fetch weather data for the given city name from the backend service.

    Args:
        city_name (str): The name of the city to fetch weather for.

    Returns:
        tuple: (result, error) where result is the weather data (dict or None) and error is an error message (str or None).
    """
    try:
        response = requests.get(BACKEND_URL, params={"city": city_name}, timeout=100)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as error:
        return None, f"Error fetching weather data: {error}"


@app.route("/", methods=["GET", "POST"])
def index():
    city = ""
    result = None
    error = None

    if request.method == "POST":
        city = request.form.get("city", "").strip()
        if not city:
            error = "Please enter a city name."
        else:
            result, error = get_weather(city)

    return render_template_string(PAGE, city=city, result=result, error=error)


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
    )
