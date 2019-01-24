"""stories URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

app_name = 'stories'
urlpatterns = [
    path('', views.Recent.as_view(), name='recent'),
    path('list-by-author/<int:pk>/', views.ByAuthor.as_view(), name='list-by-author'),
    path('edit/<int:pk>/', views.Edit.as_view(), name='edit'),
    path('create/', views.Create.as_view(), name='create'),
    path('read/<int:pk>/', views.Read.as_view(), name='read'),
]
