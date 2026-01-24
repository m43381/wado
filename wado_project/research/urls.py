# research/urls.py
from django.urls import path
from . import views

app_name = 'research'

urlpatterns = [
    path('', views.ResearchAnalysisView.as_view(), name='analysis'),
    path('run/', views.RunAnalysisView.as_view(), name='run_analysis'),
    path('report/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('scenario/create/', views.CreateScenarioView.as_view(), name='create_scenario'),
    path('delete-report/', views.DeleteReportView.as_view(), name='delete_report'),
    path('get-statistics/', views.GetStatisticsView.as_view(), name='get_statistics'),
]