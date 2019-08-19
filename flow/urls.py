from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('flow/create/', views.create_flow, name='create_flow'),
    path('flow/init/<int:flow_id>/', views.initialize_flow, name='init_flow'),
    path('node/show/<int:node_id>/', views.show_node, name="show_node"),
    path('flow/show/<int:flow_id>/', views.show_flow, name="show_flow"),
    path('ajax/get/taskstat/', views.ajax_get_task_stat,
         name="ajax_get_task_stat"),
    path('ajax/get/tasklist/', views.ajax_get_task_list,
         name="ajax_get_task_list"),
    path('ajax/check/node_action/', views.ajax_check_node_action,
         name="ajax_check_node_action"),
    path('ajax/get/node_detail/', views.ajax_get_node_detail,
         name="ajax_get_node_detail"),
]
