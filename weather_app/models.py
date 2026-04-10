from django.db import models

# Create your models here.
from django.db import models

class CitySearch(models.Model):
    city_name = models.CharField(max_length=100)
    temperature = models.FloatField()
    description = models.CharField(max_length=100)
    icon = models.CharField(max_length=10)
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.city_name
