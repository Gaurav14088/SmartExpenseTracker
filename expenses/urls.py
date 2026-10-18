
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('transactions/', views.transactions, name='transactions'),

    path('expense/add/', views.expense_add, name='expense_add'),
    path('expense/edit/<int:pk>/', views.expense_edit, name='expense_edit'),
    path('expense/delete/<int:pk>/', views.expense_delete, name='expense_delete'),

    path('reports/', views.monthly_reports, name='monthly_reports'),
    path('reports/download/', views.download_report, name='download_report'),

    path('login/', views.user_login, name='user_login'),
    path('register/', views.user_register, name='user_register'),
    path('logout/', views.user_logout, name='user_logout'),
]
