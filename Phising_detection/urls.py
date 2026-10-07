from django.contrib import admin
from django.urls import path
from application import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("upload/", views.upload_dataset, name="upload"),
    path("train/", views.train_models_view, name="train"),
    path("predict/", views.predict_view, name="predict"),
    path("evaluation/", views.evaluation_view, name="evaluation"),
]
