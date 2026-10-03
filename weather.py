import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

API_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = 10  # seconds

UNIT_LABELS = {
    "metric":   {"temp": "°C", "speed": "m/s"},
    "imperial": {"temp": "°F", "speed": "mph"},
    "standard": {"temp": "K",  "speed": "m/s"},
}

COORD_PATTERN = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")


class WeatherError(Exception):
    """Raised for any user-facing weather lookup problem."""


# --------------------------------------------------------------------------
# Input handling
# --------------------------------------------------------------------------
def parse_location(raw: str) -> dict:
    """Turn user input into API query params (city name or lat/lon)."""
    raw = raw.strip()
    if not raw:
        raise WeatherError("Please enter a city name or coordinates.")

    match = COORD_PATTERN.match(raw)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        if not (-90 <= lat <= 90):
            raise WeatherError("Latitude must be between -90 and 90.")
        if not (-180 <= lon <= 180):
            raise WeatherError("Longitude must be between -180 and 180.")
        return {"lat": lat, "lon": lon}

    return {"q": raw}


# --------------------------------------------------------------------------
# API access
# --------------------------------------------------------------------------
def fetch_weather(location: str, api_key: str, units: str = "metric") -> dict:
    """Call the OpenWeatherMap API and return the parsed JSON."""
    params = parse_location(location)
    params.update({"appid": api_key, "units": units})

    try:
        response = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        raise WeatherError("The request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise WeatherError("Could not connect. Check your internet connection.")
    except requests.exceptions.RequestException as exc:
        raise WeatherError(f"Network error: {exc}")

    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        raise WeatherError("Invalid API key. (New keys can take a couple of hours to activate.)")
    if response.status_code == 404:
        raise WeatherError(f"Location not found: '{location}'. Try 'City,CountryCode' (e.g. 'Paris,FR').")
    if response.status_code == 429:
        raise WeatherError("API rate limit reached. Please wait and try again.")
    raise WeatherError(f"API error (HTTP {response.status_code}): {response.text[:150]}")


# --------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------
def wind_direction(degrees: float) -> str:
    """Convert wind degrees to a compass direction (e.g. 225 -> SW)."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return directions[round(degrees / 22.5) % 16]


def local_time(timestamp: int, tz_offset: int, fmt: str = "%H:%M") -> str:
    """Format a UTC timestamp in the location's local time."""
    tz = timezone(timedelta(seconds=tz_offset))
    return datetime.fromtimestamp(timestamp, tz=tz).strftime(fmt)


def weather_icon(condition_id: int, is_night: bool) -> str:
    """Pick an emoji based on OpenWeatherMap condition codes."""
    if 200 <= condition_id < 300:
        return "⛈️"
    if 300 <= condition_id < 400:
        return "🌦️"
    if 500 <= condition_id < 600:
        return "🌧️"
    if 600 <= condition_id < 700:
        return "❄️"
    if 700 <= condition_id < 800:
        return "🌫️"
    if condition_id == 800:
        return "🌙" if is_night else "☀️"
    if condition_id == 801:
        return "🌤️"
    if condition_id in (802, 803, 804):
        return "☁️"
    return "🌡️"


def display_weather(data: dict, units: str) -> None:
    """Print weather data in a readable card."""
    labels = UNIT_LABELS[units]

    city = data.get("name") or "Unknown location"
    country = data.get("sys", {}).get("country", "")
    coord = data.get("coord", {})
    main = data.get("main", {})
    wind = data.get("wind", {})
    cond = (data.get("weather") or [{}])[0]
    tz_offset = data.get("timezone", 0)
    sys_info = data.get("sys", {})

    now = data.get("dt", 0)
    sunrise, sunset = sys_info.get("sunrise"), sys_info.get("sunset")
    is_night = bool(sunrise and sunset and not (sunrise <= now <= sunset))
    icon = weather_icon(cond.get("id", 0), is_night)

    title = f"{city}, {country}" if country else city
    width = 46
    line = "═" * width

    print()
    print(f"╔{line}╗")
    print(f"║ {title:<{width - 1}}║")
    if coord:
        coords = f"Lat {coord.get('lat')}, Lon {coord.get('lon')}"
        print(f"║ {coords:<{width - 1}}║")
    print(f"║ {'Local time: ' + local_time(now, tz_offset, '%a %d %b, %H:%M'):<{width - 1}}║")
    print(f"╠{line}╣")

    condition_text = f"{icon}  {cond.get('description', 'N/A').title()}"
    print(f"  {condition_text}")
    print()
    print(f"  🌡️  Temperature : {main.get('temp', 'N/A')}{labels['temp']}"
          f"  (feels like {main.get('feels_like', 'N/A')}{labels['temp']})")
    print(f"  🔻 Min / Max    : {main.get('temp_min', 'N/A')}{labels['temp']}"
          f" / {main.get('temp_max', 'N/A')}{labels['temp']}")
    print(f"  💧 Humidity     : {main.get('humidity', 'N/A')}%")

    speed = wind.get("speed", "N/A")
    deg = wind.get("deg")
    direction = f" from {wind_direction(deg)} ({deg}°)" if deg is not None else ""
    print(f"  💨 Wind speed   : {speed} {labels['speed']}{direction}")
    if "gust" in wind:
        print(f"     Gusts        : {wind['gust']} {labels['speed']}")

    print(f"  🔽 Pressure     : {main.get('pressure', 'N/A')} hPa")
    print(f"  ☁️  Cloud cover  : {data.get('clouds', {}).get('all', 'N/A')}%")
    if "visibility" in data:
        print(f"  👁️  Visibility   : {data['visibility'] / 1000:.1f} km")
    if sunrise and sunset:
        print(f"  🌅 Sunrise      : {local_time(sunrise, tz_offset)}")
        print(f"  🌇 Sunset       : {local_time(sunset, tz_offset)}")
    print(f"╚{line}╝")
    print()


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def get_api_key(cli_key: str | None) -> str:
    key = cli_key or os.environ.get("OPENWEATHER_API_KEY") or "75e5964829ba7cd75bd14e8a96816a35"
    if not key:
        print("Error: No API key found.\n"
              "Set the OPENWEATHER_API_KEY environment variable or pass --api-key.\n"
              "Get a free key at https://openweathermap.org/api", file=sys.stderr)
        sys.exit(1)
    return key


def interactive_loop(api_key: str, units: str) -> None:
    print("🌍 Weather App — enter a city (e.g. 'Tokyo' or 'Paris,FR')")
    print("   or coordinates (e.g. '17.38,78.48'). Type 'q' to quit.\n")
    while True:
        try:
            location = input("Location> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return
        if location.lower() in {"q", "quit", "exit"}:
            print("Goodbye!")
            return
        try:
            display_weather(fetch_weather(location, api_key, units), units)
        except WeatherError as exc:
            print(f"⚠️  {exc}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Real-time weather from OpenWeatherMap.")
    parser.add_argument("location", nargs="?",
                        help="City name (e.g. 'London', 'Paris,FR') or coordinates 'lat,lon'")
    parser.add_argument("--units", choices=UNIT_LABELS.keys(), default="metric",
                        help="metric (°C, m/s), imperial (°F, mph) or standard (K, m/s)")
    parser.add_argument("--api-key", help="OpenWeatherMap API key (or set OPENWEATHER_API_KEY)")
    args = parser.parse_args()

    api_key = get_api_key(args.api_key)

    if not args.location:
        interactive_loop(api_key, args.units)
        return

    try:
        display_weather(fetch_weather(args.location, api_key, args.units), args.units)
    except WeatherError as exc:
        print(f"⚠️  {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
