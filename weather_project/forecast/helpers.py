from django.shortcuts import render
import requests
from datetime import datetime

#Helpers

#City to coords
def get_coords(city_name):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}"
    try:
        data = requests.get(url).json()
        results = data.get("results")
        if results:
            first_result = results[0]
            return first_result["latitude"], first_result["longitude"]
    except Exception:
        pass
    return None, None

#Pulls from API
def get_forecast(lat, lon):
    try:
        points_data = requests.get(f"https://api.weather.gov/points/{lat},{lon}").json()
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = requests.get(forecast_url).json()
        first_period = forecast_data["properties"]["periods"][0]
        return first_period
    except Exception:
        return None

#Filter
def forecast(period):
    if not period:
        return None

    start = datetime.fromisoformat(period["startTime"])
    end = datetime.fromisoformat(period["endTime"])
    duration = end - start
    temp_c = (period["temperature"] - 32) * 5 / 9

    return {
        "name": period["name"],
        "shortForecast": period["shortForecast"],
        "temperature": period["temperature"],
        "temperatureUnit": period["temperatureUnit"],
        "temperatureC": round(temp_c, 1),
        "wind": f"{period['windSpeed']} {period['windDirection']}",
        "start": start.strftime("%Y-%m-%d %I:%M %p"),
        "end": end.strftime("%Y-%m-%d %I:%M %p"),
        "duration": duration,
    }

#Fixed for UB
def get_fixed_weather():
    stations_url = "https://api.weather.gov/gridpoints/BUF/38,53/stations"
    stations_data = requests.get(stations_url).json()

    stations_list = stations_data.get("observationStations", [])
    if not stations_list:
        return None

    station_url = stations_list[0]
    latest_obs_url = f"{station_url}/observations/latest"

    obs_data = requests.get(latest_obs_url).json()
    props = obs_data["properties"]

    temp_c = props["temperature"]["value"]
    wind_speed = props["windSpeed"]["value"]
    wind_dir = props["windDirection"]["value"]

    return {
        "temperatureC": temp_c,
        "temperatureF": round(temp_c * 9 / 5 + 32, 1) if temp_c is not None else None,
        "windSpeed": wind_speed,
        "windDirection": wind_dir,
        "description": props.get("textDescription"),
        "time": props.get("timestamp")
    }

#Today's 
def get_today_high_low(lat, lon):
    from datetime import datetime
    import pytz
    import requests

    # Fetch forecast periods (same as before)
    forecast_url = f"https://api.weather.gov/points/{lat},{lon}"
    data = requests.get(forecast_url).json()
    forecast_periods_url = data["properties"]["forecast"]
    forecast_data = requests.get(forecast_periods_url).json()
    periods = forecast_data["properties"]["periods"]

    now_utc = datetime.utcnow()
    today_periods = []
    for p in periods:
        start_time = datetime.fromisoformat(p["startTime"].replace("Z", "+00:00"))
        if start_time.date() == now_utc.date():
            today_periods.append(p)

    highs = [p["temperature"] for p in today_periods if p["isDaytime"]]
    lows = [p["temperature"] for p in today_periods if not p["isDaytime"]]

    high_f = max(highs) if highs else None
    low_f = min(lows) if lows else None

    def f_to_c(f):
        return round((f - 32) * 5/9, 1) if f is not None else None

    return {
        "highF": high_f,
        "lowF": low_f,
        "highC": f_to_c(high_f),
        "lowC": f_to_c(low_f),
        "unit": "F"
    }

#Multiple days
def get_forecast_periods(lat, lon):
    import requests
    from datetime import datetime

    url = f"https://api.weather.gov/points/{lat},{lon}"
    points_data = requests.get(url).json()
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = requests.get(forecast_url).json()
    periods = forecast_data["properties"]["periods"]

    forecast_list = []
    for p in periods:
        temp_f = p["temperature"]
        temp_c = round((temp_f - 32) * 5/9, 1)
        forecast_list.append({
            "name": p["name"],
            "temperatureF": temp_f,
            "temperatureC": temp_c,
            "shortForecast": p["shortForecast"],
            "isDaytime": p["isDaytime"]
        })
    return forecast_list



#Django
from django.shortcuts import render
from .helpers import get_coords, get_forecast, forecast, get_fixed_weather

def weather_view(request):
    forecast_data = None
    error_message = None
    selected_choice = None
    lat = lon = None
    city_input = ""

    if request.method == "POST":
        selected_choice = request.POST.get("choice1")

        #Choice
        if selected_choice == "c":
            try:
                lat = float(request.POST.get("latitude"))
                lon = float(request.POST.get("longitude"))
            except (TypeError, ValueError):
                error_message = "Invalid coordinates. Please enter valid numbers."

        elif selected_choice == "n":
            city_input = request.POST.get("city", "")
            lat, lon = get_coords(city_input)
            if lat is None or lon is None:
                error_message = "Could not find coordinates for that city."

        #Use
        if lat is not None and lon is not None:
            period = get_forecast(lat, lon)
            forecast_data = forecast(period)

    #Fixed
    fixed_current = get_fixed_weather()

    return render(request, "forecast/weather.html", {
        "forecast": forecast_data,
        "fixed_current": fixed_current, 
        "error": error_message,
        "selected_choice": selected_choice,
        "lat": request.POST.get("latitude", ""),
        "lon": request.POST.get("longitude", ""),
        "city_input": city_input
    })
