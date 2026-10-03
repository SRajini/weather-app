from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.environ.get("OPENWEATHER_API_KEY")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/weather")
def weather():

    city = request.args.get("city")

    if not city:
        return jsonify({
            "error": "Please enter a city name."
        })

    # -----------------------------------------
    # CURRENT WEATHER
    # -----------------------------------------

    current_url = "https://api.openweathermap.org/data/2.5/weather"

    current_params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    current_response = requests.get(
        current_url,
        params=current_params
    )

    if current_response.status_code != 200:

        return jsonify({
            "error": "City not found. Please enter a valid city."
        })

    current_data = current_response.json()


    # -----------------------------------------
    # 5-DAY FORECAST
    # -----------------------------------------

    forecast_url = "https://api.openweathermap.org/data/2.5/forecast"

    forecast_params = {
        "lat": current_data["coord"]["lat"],
        "lon": current_data["coord"]["lon"],
        "appid": API_KEY,
        "units": "metric"
    }

    forecast_response = requests.get(
        forecast_url,
        params=forecast_params
    )

    if forecast_response.status_code != 200:

        return jsonify({
            "error": "Unable to get forecast data."
        })

    forecast_data = forecast_response.json()


    # -----------------------------------------
    # CURRENT WEATHER DATA
    # -----------------------------------------

    weather_data = {

        "city": current_data["name"],

        "country": current_data["sys"]["country"],

        "temperature": current_data["main"]["temp"],

        "description":
            current_data["weather"][0]["description"],

        "humidity":
            current_data["main"]["humidity"],

        "wind":
            current_data["wind"]["speed"],

        "rain":
            current_data.get("rain", {}).get("1h", 0),

        "hourly": [],

        "daily": []

    }


    # -----------------------------------------
    # HOURLY FORECAST
    # -----------------------------------------

    for item in forecast_data["list"][:6]:

        weather_data["hourly"].append({

            "time": item["dt"],

            "temperature":
                item["main"]["temp"],

            "description":
                item["weather"][0]["description"]

        })


    # -----------------------------------------
    # DAILY FORECAST
    # -----------------------------------------

    daily_data = {}


    for item in forecast_data["list"]:

        date = item["dt_txt"].split(" ")[0]

        temperature = item["main"]["temp"]

        description = item["weather"][0]["description"]


        if date not in daily_data:

            daily_data[date] = {

                "date": item["dt"],

                "min": temperature,

                "max": temperature,

                "description": description

            }

        else:

            daily_data[date]["min"] = min(
                daily_data[date]["min"],
                temperature
            )

            daily_data[date]["max"] = max(
                daily_data[date]["max"],
                temperature
            )


    # Take first 5 forecast days
    weather_data["daily"] = list(
        daily_data.values()
    )[:5]


    return jsonify(weather_data)


if __name__ == "__main__":
    app.run(debug=True)