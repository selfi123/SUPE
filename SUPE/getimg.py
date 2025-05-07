import requests
url = "https://api.themoviedb.org/3/discover/movie"
params = {
    'api_key': "5dbb076a21a64be1dd6e0693a68091ab",
    'primary_release_year': 2012,
    'page': 1,
    'sort_by': 'popularity.desc'
}
response = requests.get(url, params=params)
data = response.json()
total_pages = data.get('total_pages', 0)
print(f"Total pages available: {total_pages}")
