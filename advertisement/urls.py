from django.urls import path

from . import views

urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('search', views.search, name='search'),
    path('add_signal', views.add_advertisement, name='add_advertisement'),
    path('add_expert', views.add_expert, name='add_expert'),
    path('symbols', views.symbols_list, name='symbols'),
    path('profile', views.profile, name='profile'),
    path('<int:advertisement_id>/', views.advertisement_detail, name='advertisement_detail'),
    path('<str:symbol_name>/', views.symbol_detail, name='symbol_detail'),
    path('expert/<str:expert_display_name>/', views.expert_page, name='expert_page'),
    path('chart/<str:symbol>/<int:ad>', views.LineChartJsonView.as_view(), name='chart'),
    path('chart/<str:symbol>/', views.SymbolChartJsonView.as_view(), name='symbol_chart'),
]