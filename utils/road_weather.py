import requests


def get_weather_data(station_id):
    data = None
    api_url = f"https://tie.digitraffic.fi/api/weather/v1/stations/{station_id}/data"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()

    return data


def get_nearest_road_weather_station(latitude, longitude):
    api_url = "https://tie.digitraffic.fi/api/weather/v1/stations"

    # Send a request to the API to retrieve road weather station data
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()

        nearest_station = None
        min_distance = float('inf')

        for station in data['features']:
            # Retrieve the station's latitude and longitude from the coordinates list
            station_latitude = station['geometry']['coordinates'][1]
            station_longitude = station['geometry']['coordinates'][0]

            # Calculate the distance between the station and the current location
            distance = ((latitude - station_latitude) ** 2 +
                        (longitude - station_longitude) ** 2) ** 0.5

            # Update the nearest station if the current station is closer
            if distance < min_distance:
                min_distance = distance
                nearest_station = station

        if nearest_station:
            return nearest_station
        else:
            return "No road weather station found."
    else:
        return "Unable to retrieve road weather station data."


# Example usage
latitude = 65.1699
longitude = 25.25384

result = get_nearest_road_weather_station(latitude, longitude)
print(result)
result = get_weather_data(result['properties']['id'])

my_values = ['ILMA', 'TIE_1', 'TIE_2', 'KESKITUULI', 'MAKSIMITUULI', 'SADE_INTENSITEETTI', 'SADESUMMA_LIUKUVA_24H']

for s in result['sensorValues']:
    if (s['name'] in my_values):
        print(f"{s['id']}: {s['name']}: {s['value']} {s['unit']}")
