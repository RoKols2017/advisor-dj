from django.urls import path
from . import views

app_name = 'printing'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('events/', views.PrintEventsView.as_view(), name='print_events'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    path('tree/', views.PrintTreeView.as_view(), name='print_tree'),
    path('import/users/', views.ImportUsersView.as_view(), name='import_users'),
    path('import/print-events/', views.ImportPrintEventsView.as_view(), name='import_print_events'),
] 