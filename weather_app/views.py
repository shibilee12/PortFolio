

import requests
from django.shortcuts import render
from django.conf import settings
from datetime import datetime
from .models import CitySearch

API_KEY = settings.OPENWEATHER_API_KEY 

# Get city image from Unsplash
def get_city_image(city):
    # Use Unsplash API if key exists
    access_key = getattr(settings, "UNSPLASH_ACCESS_KEY", None)
    if access_key:
        url = "https://api.unsplash.com/photos/random"
        params = {
            "query": f"{city} city",
            "orientation": "landscape",
            "client_id": access_key
        }
        try:
            res = requests.get(url, params=params, timeout=5)
            if res.status_code == 200:
                return res.json().get("urls", {}).get("regular")
        except:
            pass
    # fallback to unsplash random image URL
    return "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1600&q=80"

# Main view
def weather_dashboard(request):
    city = request.GET.get('city')
    weather_data = None
    forecast_data = None
    error = None

    history = CitySearch.objects.order_by('-searched_at')[:5]

    if city:
        try:
            # --- Current weather ---
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
            res = requests.get(url, timeout=5)
            data = res.json()
            if data.get("cod") != 200:
                raise Exception(data.get("message", "City not found"))

            weather_data = {
                "city": data["name"],
                "temperature": round(data["main"]["temp"], 1),
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "image": get_city_image(data["name"])
            }

            # --- Save recent search ---
            CitySearch.objects.create(
                city_name=weather_data['city'],
                temperature=weather_data['temperature'],
                description=weather_data['description'],
                icon=weather_data['icon']
            )
            if CitySearch.objects.count() > 5:
                CitySearch.objects.order_by('searched_at').first().delete()

            # --- Forecast (5-day) ---
            f_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
            f_res = requests.get(f_url, timeout=5)
            f_data = f_res.json()

            # Daily forecast
            forecast_daily = []
            seen_dates = set()
            for item in f_data.get("list", []):
                dt = datetime.fromtimestamp(item["dt"])
                date_str = dt.strftime("%Y-%m-%d")
                if date_str not in seen_dates and len(forecast_daily) < 5:
                    seen_dates.add(date_str)
                    forecast_daily.append({
                        "date": dt,
                        "temp": round(item["main"]["temp"], 1),
                        "desc": item["weather"][0]["description"],
                        "icon": item["weather"][0]["icon"]
                    })

            # Hourly data (next 12 intervals, 3h each)
            forecast_hourly = [{
                "dt": datetime.fromtimestamp(item["dt"]),
                "temp": round(item["main"]["temp"], 1)
            } for item in f_data.get("list", [])[:12]]

            forecast_data = {"daily": forecast_daily, "hourly": forecast_hourly}

        except Exception as e:
            error = str(e)

    context = {
        "weather_data": weather_data,
        "forecast": forecast_data,
        "history": history,
        "error": error
    }
    return render(request, "weather_dashboard.html", context)
