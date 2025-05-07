import json
import pycountry
import tkinter as tk
from tkinter import filedialog
from django.core.management.base import BaseCommand
from movies.models import Movie, Actor
import datetime


class Command(BaseCommand):
    help = "Load movies from a JSON file into the database"

    def handle(self, *args, **kwargs):
        def select_file():
            """Open file dialog to select a JSON file."""
            root = tk.Tk()
            root.withdraw()  # Hide the main tkinter window
            file_path = filedialog.askopenfilename(
                title="Select a File",
                filetypes=[("JSON files", "*.json")]
            )
            return file_path

        def get_language_name(code):
            """Convert 2-character language code to full name."""
            try:
                return pycountry.languages.get(alpha_2=code).name
            except AttributeError:
                return code

        def validate_year(release_date):
            """
            Validate and extract year from release date.
            Returns an integer year or None if invalid.
            """
            if not release_date or release_date == "0000-00-00":
                return None
            try:
                year_str = release_date.split("-")[0]
                year = int(year_str)
                current_year = datetime.date.today().year
                if 1900 <= year <= current_year + 1:
                    return year
            except ValueError:
                return None
            return None

        file_path = select_file()
        if not file_path:
            self.stdout.write("No file selected, aborting process.")
            return

        with open(file_path, "r", encoding="utf-8") as file:
            movies_data = json.load(file)

            for title, movie in movies_data.items():
                imdb_id = movie.get('imdb_id')
                if not imdb_id:
                    self.stdout.write(f"Skipping movie '{title}' (missing IMDb ID)")
                    continue

                movie_id = movie.get('id')
                poster_path = movie.get('poster_path', "")
                backdrop_path = movie.get('backdrop_path', "")
                genres = movie.get('genres', [])
                overview = movie.get('overview', "")
                popularity = movie.get('popularity', "")

                release_date = movie.get('release_date', "")
                year = validate_year(release_date)
                if year is None:
                    self.stdout.write(f"Warning: Invalid year for movie '{title}' with release date '{release_date}'")

                language_code = movie.get('original_language', "")
                language = get_language_name(language_code)

                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750"
                backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else ""

                actors_data = movie.get('credits', {}).get('cast', [])
                actor_objects = []
                for actor_data in actors_data:
                    actor_name = actor_data.get('name')
                    profile_path = actor_data.get('profile_path', "")
                    profile_url = f"https://image.tmdb.org/t/p/w500{profile_path}" if profile_path else ""
                    actor, _ = Actor.objects.get_or_create(
                        name=actor_name,
                        defaults={'profile_url': profile_url}
                    )
                    #print(actor)
                    actor_objects.append(actor)

                defaults = {
                    'title': title,
                    'year': year,
                    'poster_url': poster_url,
                    'backdrop_url': backdrop_url,
                    'overview': overview,
                    'movie_id': movie_id,
                    'genres': genres,
                    'language': language,
                    'popularity': popularity,
                }
                print(f"Saving movie '{title}' with year '{year}'")
                if Movie.objects.filter(movie_id=movie_id).exists():
                    self.stdout.write(f"Skipping movie '{title}' (duplicate movie_id: {movie_id})")
                    continue

                movie_obj, _ = Movie.objects.update_or_create(
                    imdb_id=imdb_id,
                    defaults=defaults
                )
                movie_obj.actors.set(actor_objects)
                # Check the actors associated with the movie


        self.stdout.write("Movies loaded successfully!")
