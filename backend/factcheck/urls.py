from django.urls import path
from .views import factCheck
from django.urls import include


urlpatterns = [
    path("check/", factCheck, name="factCheck"),
]

