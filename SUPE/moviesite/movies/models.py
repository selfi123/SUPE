from django.db import models

class Actor(models.Model):
    name = models.CharField(max_length=255, unique=True)
    profile_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    year = models.IntegerField(blank=True, null=True, db_index=True)
    imdb_id = models.CharField(max_length=15, unique=True)
    poster_url = models.URLField(blank=True, null=True)
    backdrop_url = models.URLField(blank=True, null=True)
    overview = models.TextField(blank=True, null=True)
    movie_id = models.IntegerField(default=0)  # or any appropriate default value
    genres = models.JSONField(blank=True, null=True, db_index=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    popularity = models.FloatField(blank=True, null=True)
    actors = models.ManyToManyField(Actor, related_name="movies")

    def __str__(self):
        return self.title
