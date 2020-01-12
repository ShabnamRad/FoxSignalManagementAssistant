from django.urls import path

from advertisement.views import follow, unfollow
from . import views

urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('search', views.search, name='search'),
    path('add_signal', views.add_signal, name='add_signal'),
    path('add_expert', views.add_expert, name='add_expert'),
    path('symbols', views.symbols_list, name='symbols'),
    path('profile', views.profile, name='profile'),
    path('expert_aggregation', views.expert_aggregate, name='expert_aggregation'),
    path('<int:signal_id>/', views.signal_detail, name='signal_detail'),
    path('<str:symbol_name>/', views.symbol_detail, name='symbol_detail'),
    path('expert/<int:expert_id>/', views.expert_page, name='expert_page'),
    path('chart/<int:ad>', views.LineChartJsonView.as_view(), name='chart'),
    path('chart/<str:symbol>/', views.SymbolChartJsonView.as_view(), name='symbol_chart'),
    path('follow/<int:expert_id>/', follow, name='follow'),
    path('unfollow/<int:expert_id>/', unfollow, name='unfollow'),
]