from django.urls import path

from ukrbus.views import HomeView


urlpatterns = [

    path('', HomeView.as_view(), name='home'),

]
