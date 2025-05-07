import requests
import json

def get_movie_details(api_key, movie_id):
    """
    Fetch detailed movie information by its TMDB ID.
    """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {'api_key': api_key}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching movie details for ID {movie_id}: {e}")
        return None

def get_movies_by_year(api_key, year):
    """
    Generator function to fetch movies for a given year, page by page.
    """
    url = "https://api.themoviedb.org/3/discover/movie"
    page = 1

    while True:
        params = {
            'api_key': api_key,
            'primary_release_year': year,
            'page': page,
            'sort_by': 'popularity.desc'
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data['results']:
                return  # Stop if no more results

            yield data['results']  # Yield the current page's results
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for year {year}, page {page}: {e}")
            return  # Stop on an error

def save_data_incrementally(movies_dict, output_file):
    """
    Save the movie data to a file incrementally.
    """
    try:
        with open(output_file, 'w') as f:
            json.dump(movies_dict, f, indent=4)
    except Exception as e:
        print(f"Error saving data to file: {e}")

def fetch_and_save_movies(api_key, start_year=2024, end_year=2025, batch_size=100):
    """
    Fetch movies from TMDB and save incrementally to a JSON file.
    """
    movies_dict = {}
    output_file = "movies.json"
    processed_count = 0

    for year in range(start_year, end_year + 1):
        print(f"Fetching movies for year {year}...")

        for movies in get_movies_by_year(api_key, year):
            for movie in movies:
                tmdb_id = movie['id']
                details = get_movie_details(api_key, tmdb_id)
                if details and 'imdb_id' in details:
                    # Add movie details to the dictionary
                    movies_dict[details['title']] = details
                    processed_count += 1

                    # Save data in batches
                    if processed_count % batch_size == 0:
                        save_data_incrementally(movies_dict, output_file)

    # Save any remaining data
    save_data_incrementally(movies_dict, output_file)
    print(f"Movies data has been saved incrementally to {output_file}")

# Example usage
if __name__ == "__main__":
    api_key = "5dbb076a21a64be1dd6e0693a68091ab"
    fetch_and_save_movies(api_key)
