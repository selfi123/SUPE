from django.shortcuts import render
from django.core.paginator import Paginator
from django.core.cache import cache
import requests
from django.http import Http404

API_KEY = '5dbb076a21a64be1dd6e0693a68091ab'
BASE_URL = 'https://api.themoviedb.org/3'
STREAM_URLS = [
    'https://vidlink.pro/movie/',
    'https://vidsrc.net/embed/movie/',
    'https://embed.su/embed/movie/',
    'https://multiembed.mov/?video_id=',
    'https://www.NontonGo.win/embed/movie/'
]
SERIES_STREAM_URLS = [
    'https://vidsrc.xyz/embed/tv/',
    'https://embed.su/embed/tv/',
    'https://multiembed.mov/?video_id=',
    'https://www.nontongo.win/embed/tv/'
]
def fetch_tmdb_data(endpoint, params=None):
    """Helper function to fetch data from TMDB API."""
    if params is None:
        params = {}
    params['api_key'] = API_KEY
    response = requests.get(f"{BASE_URL}{endpoint}", params=params)
    if response.status_code == 200:
        return response.json()
    return None

def movie_list(request):
    query = request.GET.get('query', '').strip()
    genre = request.GET.get('genre', '')
    year = request.GET.get('year', '')
    language = request.GET.get('language', '')
    page = request.GET.get('page', 1)

    # Build cache key for the movie list
    cache_key = f"movies_{query}_{genre}_{year}_{language}_{page}"
    movies_data = cache.get(cache_key)
    total_pages = cache.get(f"{cache_key}_total_pages")

    if movies_data is None or total_pages is None:
        params = {
            'sort_by': 'popularity.desc',
            'page': page,
        }

        # Fetch genre IDs for filtering
        genre_ids = {}
        genres_data = fetch_tmdb_data('/genre/movie/list')
        if genres_data:
            genre_ids = {genre['name']: genre['id'] for genre in genres_data['genres']}

        # Language mapping (TMDB uses ISO 639-1 codes)
        language_map = {
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Hindi': 'hi',
            'Japanese': 'ja'
        }

        # Apply filters whether there's a query or not
        if year:
            params['primary_release_year'] = year
        if language:
            params['with_original_language'] = language_map.get(language, language.lower())
        if genre:
            params['with_genres'] = genre_ids.get(genre, '')

        if query:
            # Use /discover/movie with with_text_query for filtered search
            params['with_text_query'] = query
            discover_data = fetch_tmdb_data('/discover/movie', params)
            if discover_data:
                movies_data = discover_data['results']
                total_pages = min(discover_data.get('total_pages', 1), 500)  # TMDB max is 500 pages
            else:
                # Fallback to /search/movie if no results with filters
                search_data = fetch_tmdb_data('/search/movie', {'query': query, 'page': page})
                if search_data and search_data.get('results'):
                    movies_data = search_data['results']
                    total_pages = min(search_data.get('total_pages', 1), 500)
                else:
                    # Check if it's an actor search
                    person_data = fetch_tmdb_data('/search/person', {'query': query})
                    if person_data and person_data.get('results'):
                        person_id = person_data['results'][0]['id']
                        movies_data = fetch_tmdb_data(f'/person/{person_id}/movie_credits')['cast']
                        total_pages = 1  # Actor credits don't paginate the same way
                    else:
                        movies_data = []
                        total_pages = 0
        else:
            # No query, just use /discover/movie with filters
            discover_data = fetch_tmdb_data('/discover/movie', params)
            if discover_data:
                movies_data = discover_data['results']
                total_pages = min(discover_data.get('total_pages', 1), 500)
            else:
                movies_data = []
                total_pages = 0

        # Filter movies to ensure they have an imdb_id or tmdb_id
        movies_data = [movie for movie in movies_data if movie.get('imdb_id') or movie.get('id')]
        cache.set(cache_key, movies_data, 60 * 60)
        cache.set(f"{cache_key}_total_pages", total_pages, 60 * 60)

    # Paginate the current page’s data only
    paginator = Paginator(movies_data, 20)  # 20 items per page
    page_obj = paginator.get_page(1)  # Use 1 here since we fetch page-specific data from TMDB
    paginator.num_pages = total_pages  # Override num_pages for navigation

    # Fetch unique filters dynamically
    unique_genres = cache.get('unique_genres')
    if not unique_genres:
        if genres_data:
            unique_genres = sorted(genre_ids.keys())
            cache.set('unique_genres', unique_genres, 60 * 60 * 24)

    unique_languages = cache.get('unique_languages')
    if not unique_languages:
        unique_languages = list(language_map.keys())
        cache.set('unique_languages', unique_languages, 60 * 60 * 24)

    unique_years = cache.get('unique_years')
    if not unique_years:
        current_year = 2025
        unique_years = list(range(current_year, 1900, -1))
        cache.set('unique_years', unique_years, 60 * 60 * 24)

    return render(request, 'movies/movie_list.html', {
        'movies': page_obj,
        'genres': unique_genres,
        'languages': unique_languages,
        'unique_year': unique_years,
        'actor': query if not movies_data and query else None,
        'page_obj': page_obj,
        'total_pages': total_pages,
        'current_page': int(page),
    })

def movie_detail(request, imdb_id=None, tmdb_id=None):
    if imdb_id:
        movie_data = fetch_tmdb_data(f'/find/{imdb_id}', {'external_source': 'imdb_id'})
        if not movie_data or not movie_data.get('movie_results'):
            raise Http404("Movie not found")
        tmdb_id = movie_data['movie_results'][0]['id']
    elif tmdb_id:
        tmdb_id = tmdb_id
    else:
        raise Http404("No valid ID provided")

    cache_key = f"movie_detail_{tmdb_id}"
    movie = cache.get(cache_key)
    if not movie:
        movie = fetch_tmdb_data(f'/movie/{tmdb_id}')
        credits = fetch_tmdb_data(f'/movie/{tmdb_id}/credits')
        if movie and credits:
            movie['credits'] = {'cast': credits['cast'][:10]}
            cache.set(cache_key, movie, 60 * 60)

    if not movie:
        raise Http404("Movie not found")

    cache_key_videos = f"movie_videos_{tmdb_id}"
    video_keys = cache.get(cache_key_videos)
    if video_keys is None:
        videos = fetch_tmdb_data(f'/movie/{tmdb_id}/videos')
        video_keys = [
            video["key"] for video in videos.get("results", [])
            if video.get("type") == "Trailer" and video.get("site") == "YouTube"
        ] if videos else []
        cache.set(cache_key_videos, video_keys, 60 * 60)

    return render(request, 'movies/movie_detail.html', {
        'movie': movie,
        'genres': movie.get('genres', []),
        'video_keys': video_keys,
        'stream_urls': STREAM_URLS,
    })
from django.core.paginator import Paginator
from django.shortcuts import render
from django.core.cache import cache
from datetime import datetime

def series_list(request):
    query = request.GET.get('query', '').strip()
    genre = request.GET.get('genre', '')
    year = request.GET.get('year', '')
    language = request.GET.get('language', '')
    page = request.GET.get('page', 1)

    cache_key = f"series_{query}_{genre}_{year}_{language}_{page}"
    series_data = cache.get(cache_key)
    total_pages = cache.get(f"{cache_key}_total_pages")

    if series_data is None or total_pages is None:
        params = {
            'sort_by': 'popularity.desc',  # Initial sort by popularity
            'page': page,
        }

        # Fetch genre IDs
        genre_ids = {}
        genres_data = fetch_tmdb_data('/genre/tv/list')
        if genres_data:
            genre_ids = {genre['name']: genre['id'] for genre in genres_data['genres']}

        # Language mapping
        language_map = {
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Hindi': 'hi',
            'Japanese': 'ja'
        }

        # Apply filters to params
        if year:
            params['first_air_date_year'] = year
        if language:
            params['with_original_language'] = language_map.get(language, language.lower())
        if genre and not query:
            params['with_genres'] = genre_ids.get(genre, '')

        if query:
            search_params = {
                'query': query,
                'page': page,
                'sort_by': 'popularity.desc',
            }
            if year:
                search_params['first_air_date_year'] = year
            if language:
                search_params['with_original_language'] = language_map.get(language, language.lower())

            search_data = fetch_tmdb_data('/search/tv', search_params)
            if search_data and search_data.get('results'):
                series_data = search_data['results']
                total_pages = min(search_data.get('total_pages', 1), 500)
            else:
                series_data = []
                total_pages = 0

            # Manually filter by genre if specified
            if genre:
                genre_id = genre_ids.get(genre)
                series_data = [series for series in series_data if genre_id in series.get('genre_ids', [])]
        else:
            discover_data = fetch_tmdb_data('/discover/tv', params)
            if discover_data:
                series_data = discover_data['results']
                total_pages = min(discover_data.get('total_pages', 1), 500)
            else:
                series_data = []
                total_pages = 0

        # Ensure valid series data
        series_data = [series for series in series_data if series.get('id') and series.get('first_air_date')]

        # Calculate a custom score with aggressive penalties/boosts
        current_date = datetime.now()
        current_year = current_date.year

        for series in series_data:
            popularity = series.get('popularity', 0)
            release_date_str = series.get('first_air_date', '1900-01-01')
            release_date = datetime.strptime(release_date_str, '%Y-%m-%d')
            release_year = release_date.year

            # Base recency score: normalized to 0-100 from 1900 to current year
            recency_score = (release_year - 1900) / (current_year - 1900) * 100

            # Adjust score based on year ranges
            if 1900 <= release_year < 1990:
                # Heavy penalty for 1900-1990: reduce popularity drastically
                adjusted_popularity = popularity * 0.2  # 80% reduction
                series['score'] = (0.8 * recency_score) + (0.2 * adjusted_popularity)
            else:  # 1990-current year
                # Boost for 1990+: full popularity + higher recency weight
                adjusted_popularity = popularity
                series['score'] = (0.8 * recency_score) + (0.2 * adjusted_popularity) + 20  # Add a flat boost

            # Debugging: Print scores to verify
            print(f"Series: {series.get('name')}, Year: {release_year}, Pop: {popularity}, Score: {series['score']}")

        # Sort by the custom score
        series_data = sorted(series_data, key=lambda x: x.get('score', 0), reverse=True)

        cache.set(cache_key, series_data, 60 * 60)
        cache.set(f"{cache_key}_total_pages", total_pages, 60 * 60)

    paginator = Paginator(series_data, 20)
    page_obj = paginator.get_page(page)
    paginator.num_pages = total_pages

    # Fetch unique filter options
    unique_genres = cache.get('series_unique_genres')
    if not unique_genres and genres_data:
        unique_genres = sorted(genre_ids.keys())
        cache.set('series_unique_genres', unique_genres, 60 * 60 * 24)

    unique_languages = cache.get('series_unique_languages')
    if not unique_languages:
        unique_languages = list(language_map.keys())
        cache.set('series_unique_languages', unique_languages, 60 * 60 * 24)

    unique_years = cache.get('series_unique_years')
    if not unique_years:
        current_year = 2025
        unique_years = list(range(current_year, 1900, -1))
        cache.set('series_unique_years', unique_years, 60 * 60 * 24)

    return render(request, 'movies/series_list.html', {
        'series': page_obj,
        'genres': unique_genres,
        'languages': unique_languages,
        'unique_year': unique_years,
        'page_obj': page_obj,
        'total_pages': total_pages,
        'current_page': int(page),
    })


def series_detail(request, tmdb_id=None):
    if not tmdb_id:
        raise Http404("No valid ID provided")

    cache_key = f"series_detail_{tmdb_id}"
    series = cache.get(cache_key)
    if not series:
        series = fetch_tmdb_data(f'/tv/{tmdb_id}')
        credits = fetch_tmdb_data(f'/tv/{tmdb_id}/credits')
        if series and credits:
            series['credits'] = {'cast': credits['cast'][:10]}
            cache.set(cache_key, series, 60 * 60)

    if not series:
        raise Http404("Series not found")

    # Fetch IMDb ID if available
    external_ids = fetch_tmdb_data(f'/tv/{tmdb_id}/external_ids')
    imdb_id = external_ids.get('imdb_id', '') if external_ids else ''

    # Fetch season and episode details
    seasons = series.get('seasons', [])
    season_details = []
    for season in seasons:
        if season['season_number'] > 0:  # Exclude "Specials" (season 0)
            season_data = fetch_tmdb_data(f'/tv/{tmdb_id}/season/{season["season_number"]}')
            if season_data:
                episodes = []
                for episode in season_data['episodes']:
                    episodes.append({
                        'episode_number': episode['episode_number'],
                        'overview': episode.get('overview', 'No description available.'),
                        'name': episode.get('name', f'Episode {episode["episode_number"]}'),
                        'still_path': episode.get('still_path', None),  # Fetch episode poster
                    })
                season_details.append({
                    'season_number': season['season_number'],
                    'episode_count': season_data['episodes'][-1]['episode_number'] if season_data['episodes'] else 0,
                    'episodes': episodes  # Add episode details
                })

    cache_key_videos = f"series_videos_{tmdb_id}"
    video_keys = cache.get(cache_key_videos)
    if video_keys is None:
        videos = fetch_tmdb_data(f'/tv/{tmdb_id}/videos')
        video_keys = [
            video["key"] for video in videos.get("results", [])
            if video.get("type") == "Trailer" and video.get("site") == "YouTube"
        ] if videos else []
        cache.set(cache_key_videos, video_keys, 60 * 60)

    return render(request, 'movies/series_detail.html', {
        'series': series,
        'imdb_id': imdb_id,
        'genres': series.get('genres', []),
        'video_keys': video_keys,
        'stream_urls': SERIES_STREAM_URLS,
        'seasons': season_details,
    })