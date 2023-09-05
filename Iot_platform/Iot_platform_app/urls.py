from . import views
from django.urls import path

urlpatterns = [
    path('',views.login,name='login'),
    path('signup/',views.signup,name='signup'),
    path('dashboard/',views.dashboard_home,name='dashboard'),
    path('login_details/',views.login_details,name='login_details'),
    path('registered/',views.register_data,name='regsiter'),
    path('create device/',views.add_device,name='add_device'),
    path('device_page/<devicename>',views.device_page,name='device_page'),
    path('profile/',views.profile_page,name='profile_page'),
    path('profile_edited/',views.edit_profile,name='edit_profile'),
    path('edit_device/<device_name>',views.edit_device,name='edit_device'),
    path('edit_device/insert_dashboard/',views.insert_dashboard,name='insert_dashboard'),
    path('subscribe_topic/<device_name>',views.mqtt_view_subscribe,name='subscribe'),
    path('publish_topic/<device_name>',views.publish_data,name='publish'),
    path('edit_device/delete_dashboard/',views.delete_data_dashboard,name='delete_dashboard'),
    path('Analytics/',views.analytics,name='analytics'),
    path('Analytics/graph/',views.graph,name='graph'),
    path('load_template/',views.load_graph_template,name="load_template"),
    path('Analytics/calculate_data/',views.calculate_data,name='calculate_data'),
    path('logout/',views.logout,name='logout'),
    path('dashboard/delete_location/',views.delete_device,name='delete_location'),

    path('create_admin/',views.create_admin,name='create_admin'),
    path('add_data/',views.admin_login_data,name='add_admin'),
    path('admin_page/',views.admin_login_page,name='admin_login_page'),
    path('admin_register/',views.admin_signin,name='admin_register'),
    path('userdetails/',views.user_data,name='userdetails'),
  
    path('userdetails/<id>',views.views_data,name='details'),
    path('userdetails/device_details/',views.user_devices,name='device_details')




]
