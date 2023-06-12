import math
import random

# Constants
EARTH_RADIUS = 6371  # in kilometers

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two GPS coordinates using the haversine formula.
    """
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = EARTH_RADIUS * c
    return distance

def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculates the initial bearing (in degrees) from the first point to the second point.
    """
    dlon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    bearing = (math.atan2(y, x) * 180 / math.pi + 360) % 360
    return bearing

def generate_curvy_route(start_lat, start_lon, end_lat, end_lon, num_waypoints, max_speed):
    """
    Generates a curvy route with at least a 90-degree turn, including bearing values.
    """
    waypoints = []

    # Calculate the total distance between start and end points
    total_distance = calculate_distance(start_lat, start_lon, end_lat, end_lon)

    # Generate intermediate waypoints along the route
    waypoints.append((start_lat, start_lon))
    current_lat, current_lon = start_lat, start_lon

    for _ in range(num_waypoints - 2):
        # Generate random latitude and longitude offsets
        lat_offset = random.uniform(-0.05, 0.05)
        lon_offset = random.uniform(-0.05, 0.05)

        # Calculate the new waypoint coordinates
        current_lat += lat_offset
        current_lon += lon_offset

        # Add the new waypoint to the list
        waypoints.append((current_lat, current_lon))

    waypoints.append((end_lat, end_lon))

    # Calculate the distance between each waypoint
    distances = [calculate_distance(*waypoints[i], *waypoints[i+1]) for i in range(num_waypoints-1)]

    # Calculate the time required to travel each distance segment based on the desired speed
    times = [distance / max_speed for distance in distances]

    # Calculate the bearing between each pair of consecutive waypoints
    bearings = [calculate_bearing(*waypoints[i], *waypoints[i+1]) for i in range(num_waypoints-1)]

    # Generate simulated GPS data
    gps_data = []
    current_speed = 0

    print(f"{bearings}")

    for i in range(num_waypoints):
        lat, lon = waypoints[i]
        distance_traveled = sum(distances[:i+1])
        elapsed_time = sum(times[:i+1])
        current_speed = max_speed
        bearing = bearings[i]
        gps_data.append({
            'latitude': lat,
            'longitude': lon,
            'speed': current_speed,
            'elapsed_time': elapsed_time,
            'bearing': bearing
        })

    return gps_data

# Example usage
start_latitude = 37.7749
start_longitude = -122.4194
end_latitude = 34.0522
end_longitude = -118.2437
num_waypoints = 10
max_speed = 60  # km/h

gps_data = generate_curvy_route(start_latitude, start_longitude, end_latitude, end_longitude, num_waypoints, max_speed)

# Print the simulated GPS data
for point in gps_data:
    print(f"Latitude: {point['latitude']}, Longitude: {point['longitude']}, Speed: {point['speed']}, Elapsed Time: {point['elapsed_time']}, Bearing: {point['bearing']}")