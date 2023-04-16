from django.urls import path
from . import views

app_name = 'gui'

# URL Configuration
urlpatterns = [
    path('', views.index, name='index'),
    path('Create_Interface/', views.create_interface, name='Create_Interface'),
    path('Run_Controller/', views.run_controller, name='Run_Controller'),
    path('Start_Server_A/', views.start_server_A, name='Start_Server_A'),
    path('Start_Server_B/', views.start_server_B, name='Start_Server_B'),
    path('Stop_Server_A/', views.stop_server_A, name='Stop_Server_A'),
    path('Stop_Server_B/', views.stop_server_B, name='Stop_Server_B'),
    path('start_client/', views.start_client, name='start_client'),
    path('stop_client/', views.stop_client, name='stop_client'),
    path('set_auto_migration_on/', views.set_auto_migration_on),
    path('set_auto_migration_off/', views.set_auto_migration_off),
    path('migrate_all_to_B/', views.migrate_all_to_B),
    path('migrate_all_to_A/', views.migrate_all_to_A),
    path('migrate_to_A/', views.migrate_to_A, name='migrate_to_A'),
    path('migrate_to_B/', views.migrate_to_B, name='migrate_to_B'),
    path('write_dummy_sessions_A/', views.write_dummy_sessions_A),
    path('write_dummy_sessions_B/', views.write_dummy_sessions_B),

]
