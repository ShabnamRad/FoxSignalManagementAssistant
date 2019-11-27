from django.urls import path

from . import views

urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('search', views.search, name='search'),
    path('add_signal', views.add_advertisement, name='add_advertisement'),
    path('<int:advertisement_id>/', views.advertisement_detail, name='advertisement_detail'),
    path('chart/<str:symbol>/<int:ad>', views.LineChartJsonView.as_view(), name='chart'),
]