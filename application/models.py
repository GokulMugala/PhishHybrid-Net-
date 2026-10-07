from django.db import models

class Prediction(models.Model):
    url = models.TextField()
    predicted_label = models.CharField(max_length=32)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.predicted_label}: {self.url[:60]}"
