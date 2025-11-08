from django.shortcuts import render
from .helpers import get_coords, get_forecast, forecast, get_fixed_weather, get_today_high_low, get_forecast_periods
from datetime import datetime
import pytz

#In views
def weather_view(request):
    forecast_data = None
    error_message = None
    selected_choice = None
    lat = lon = None
    city_input = ""
    daily_range = None 

    if request.method == "POST":
        selected_choice = request.POST.get("choice1")

        if selected_choice == "c":
            try:
                lat = float(request.POST.get("latitude"))
                lon = float(request.POST.get("longitude"))
            except (TypeError, ValueError):
                error_message = "Invalid coordinates."

        elif selected_choice == "n":
            city_input = request.POST.get("city", "")
            lat, lon = get_coords(city_input)
            if lat is None or lon is None:
                error_message = "Couldn't find that place."

        if lat is not None and lon is not None:
            period = get_forecast(lat, lon)
            forecast_data = forecast(period)
            forecast_data = get_forecast_periods(lat, lon)
            daily_range = get_today_high_low(lat, lon)

    fixed_current = get_fixed_weather()
    if fixed_current and fixed_current.get("time"):
        from datetime import datetime
        import pytz
        utc_time = datetime.fromisoformat(fixed_current["time"])
        eastern = pytz.timezone("America/New_York")
        local_time = utc_time.astimezone(eastern)
        fixed_current["time_local"] = local_time.strftime("%Y-%m-%d %I:%M %p")

    return render(request, "forecast/weather.html", {
        "forecast": forecast_data,
        "daily_range": daily_range,
        "fixed_current": fixed_current,
        "error": error_message,
        "selected_choice": selected_choice,
        "lat": request.POST.get("latitude", ""),
        "lon": request.POST.get("longitude", ""),
        "city_input": city_input
    })
