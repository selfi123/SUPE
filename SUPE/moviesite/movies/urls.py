from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('movie/imdb/<str:imdb_id>/', views.movie_detail, name='movie_detail'),
    path('movie/tmdb/<int:tmdb_id>/', views.movie_detail, name='movie_detail_tmdb'),
    path('series/', views.series_list, name='series_list'),
    path('series/tmdb/<int:tmdb_id>/', views.series_detail, name='series_detail'),
]