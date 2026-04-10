from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class MoodEntry(models.Model):
    MOOD_CHOICES = [
        ('happy', 'Happy'),
        ('neutral', 'Neutral'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
        ('anxious', 'Anxious'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    mood = models.CharField(max_length=8, choices=MOOD_CHOICES)
    notes = models.TextField(blank=True, null=True)
    sentiment = models.CharField(max_length=16, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.mood} on {self.date}"

class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    sentiment = models.CharField(max_length=16, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.date.strftime('%Y-%m-%d %H:%M')}"
