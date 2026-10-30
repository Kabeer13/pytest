from django.contrib import admin
from django.urls import path
from pokemon import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("learn/", views.learn, name="learn"),
    path("lab/", views.lab, name="lab"),
    path("coverage/", views.coverage_page, name="coverage"),
    path("api/pokemon/<str:name>/", views.pokemon_api, name="pokemon_api"),
    path("api/run-tests/", views.run_tests_api, name="run_tests_api"),
    path("api/run-tests/status/<str:request_id>/", views.run_tests_status_api, name="run_tests_status_api"),
]
