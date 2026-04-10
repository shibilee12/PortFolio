import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

TMDB_API = settings.TMDB_API_KEY
BASE_URL = "https://api.themoviedb.org/3"

def home(request):
    search_query = request.GET.get('q')
    movies, trending, error = [], [], None

    try:
        trending = requests.get(f"{BASE_URL}/trending/movie/week?api_key={TMDB_API}").json().get('results', [])
        if search_query:
            url = f"{BASE_URL}/search/movie?api_key={TMDB_API}&query={search_query}"
        else:
            url = f"{BASE_URL}/movie/popular?api_key={TMDB_API}"
        movies = requests.get(url).json().get('results', [])
    except Exception as e:
        error = str(e)

    return render(request, "movieshome.html", {"movies": movies, "trending": trending, "error": error})


def movie_details(request, movie_id):
    """AJAX endpoint to return movie details and trailer."""
    try:
        details_url = f"{BASE_URL}/movie/{movie_id}?api_key={TMDB_API}&language=en-US"
        videos_url = f"{BASE_URL}/movie/{movie_id}/videos?api_key={TMDB_API}&language=en-US"

        details = requests.get(details_url).json()
        videos = requests.get(videos_url).json().get('results', [])

        # Find YouTube trailer
        trailer = next((v for v in videos if v['site'] == 'YouTube' and v['type'] == 'Trailer'), None)

        return JsonResponse({
            "title": details.get('title'),
            "overview": details.get('overview'),
            "poster": f"https://image.tmdb.org/t/p/w500{details.get('poster_path')}" if details.get('poster_path') else None,
            "release_date": details.get('release_date'),
            "rating": details.get('vote_average'),
            "trailer_key": trailer['key'] if trailer else None,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def base(request):
    return render(request, "base.html")
def homepage(request):
    return render(request, "home.html")
def settings(request):
    return render(request, "settings.html")