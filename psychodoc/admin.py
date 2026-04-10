from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import MoodEntry, JournalEntry

admin.site.register(MoodEntry)
admin.site.register(JournalEntry)
