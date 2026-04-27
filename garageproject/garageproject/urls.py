"""
URL configuration for garageproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from.import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/',views.homepage),
    path('signup/',views.signup),
    path('adduser/',views.adduser), #return dash
    path('login/',views.login),
    path('authenticate/',views.authenticate),
    path('dashboard/',views.dashboard),
    path('failure/',views.failure),
    path('bill/',views.bill),
    path('customer/', views.customer),
    path('vehicle/',views.vehicle),
    path('service/',views.service),
    # API endpoints for vehicles
    path('api/vehicles/list/', views.api_vehicles_list, name='api_vehicles_list'),
    path('api/customers/list/', views.api_customers_list, name='api_customers_list'),
    path('api/vehicle/add/', views.api_vehicle_add, name='api_vehicle_add'),
    path('api/vehicle/edit/<str:customer_id>/<str:vehicle_id>/', views.api_vehicle_edit, name='api_vehicle_edit'),
    path('api/vehicle/delete/<str:customer_id>/<str:vehicle_id>/', views.api_vehicle_delete, name='api_vehicle_delete'),
    path('api/services/list/', views.api_services_list, name='api_services_list'),
    path('profile/',views.profile),
    path('logout/', views.logout, name='logout'),
    path('api/update-profile/', views.api_update_profile, name='api_update_profile'),
    path('api/change-password/', views.api_change_password, name='api_change_password'),
    path('api/services/search/', views.api_search_services, name='api_search_services'),
    path('search/<str:service_id>/', views.service_detail, name='se'),
]
