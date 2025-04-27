from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username

class RecentTrain(models.Model):
    number = models.CharField(max_length=10, unique=True)
    current_station_name = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    last_updated = models.DateTimeField()

    def __str__(self):
        return f"Train {self.number} - {self.current_station_name}"