from django.db import models

# Create your models here.
# movies/models.py
from django.db import models

class FavoriteMovie(models.Model):
    title = models.CharField(max_length=255)
    tmdb_id = models.IntegerField(unique=True)
    poster = models.URLField()
    release_date = models.CharField(max_length=20)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
