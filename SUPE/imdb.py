'''import requests
import json

def get_movie_details(api_key, movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {'api_key': api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def get_movies_by_year(api_key, year, page):
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        'api_key': api_key,
        'primary_release_year': year,
        'page': page,
        'sort_by': 'popularity.desc'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()['results']
    return []

movies_dict = {}

# Example usage
api_key = "5dbb076a21a64be1dd6e0693a68091ab"

for year in range(2024 ,2026):
    print(f"Fetching movies for year {year}...")
    for page in range(1,21):
        movies = get_movies_by_year(api_key, year,page)
        for movie in movies:
            tmdb_id = movie['id']
            details = get_movie_details(api_key, tmdb_id)
            if details and 'imdb_id' in details:
                movies_dict[details['title']] =details
                print(details['title'])
# Save the dictionary to a JSON file
output_file = "movies.json"
with open(output_file, 'w') as f:
    json.dump(movies_dict, f, indent=4)

print(f"Movies data has been saved to {output_file}")
'''
import requests
import json

def search_movie_by_name(api_key, movie_name):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        'api_key': api_key,
        'query': movie_name,
        'page': 1  # You can change the page if you want more results
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()['results']
    return []

def get_movie_details(api_key, movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {'api_key': api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# Example usage
api_key = "5dbb076a21a64be1dd6e0693a68091ab"
movie_name = "ip man"  # Replace with the movie name you want to search for
movies_dict={}
# Search for the movie
movies = search_movie_by_name(api_key, movie_name)
if movies:
    for movie in movies:
        print(f"Found movie: {movie['title']} (ID: {movie['id']})")
        # Get more details about the movie (optional)
        details = get_movie_details(api_key, movie['id'])
        if details:
            movies_dict[details['title']] =details
else:
    print(f"No movies found with the name '{movie_name}'")
with open('movies.json','w') as file:
    json.dump(movies_dict, file, indent=4)
