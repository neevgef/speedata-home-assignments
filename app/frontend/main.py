# Imports
from nicegui import ui
import requests

# Environment Variables
BACKEND_HOST = 'localhost'
BACKEND_PORT = 8000
BACKEND_URL = f'http://{BACKEND_HOST}:{BACKEND_PORT}/weather'


def get_weather(city_input):

    city_name = city_input.value
    if not city_name:
        ui.notify('Please enter a city name', type="negative", close_button=True)
        return

    try:
        response = requests.get(f'{BACKEND_URL}?city={city_name}', timeout=5)
        data = response.json()
        return data
    except requests.RequestException as e:
        ui.notify(f"Error fetching weather data: {e}", type="negative", close_button=True)


def main():
    # We create a class to center all the ui elements on the page
    ui.label('Enter a city to get the current weather:').classes('justify-center text-lg font-bold')
    city_input = ui.input('City', placeholder='Enter city name')
    ui.button('Submit', on_click=lambda: answer_label.set_text(get_weather(city_input)))
    answer_label = ui.label('')

    ui.run(title='SkyWatch', dark=False)


if __name__ in {"__main__", "__mp_main__"}:
    main()
