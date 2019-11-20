from django.urls import path

from . import views


urlpatterns = [
    path('ajax/upload_drawing/<int:node_id>/', views.ajax_upload_drawing,
        name='upload_drawing'),
]
