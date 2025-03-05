from django.urls import path 
from .import views 

urlpatterns = [
    path("index", views.index, name="index"),
    path("signin",views.signin,name="signin"),
    path("signout",views.signout,name="signout"),
    path("",views.landing, name="landing"),
    path("anim",views.amin,name="anim"),

    path("user_index", views.user_index, name="user_index"),
    path("manager_index", views.manager_index, name="manager_index"),
    path("bots",views.bots,name="bots"),
    path("update_company/<int:pk>",views.update_company,name="update_company"),
    path("update_user_profile/<int:pk>",views.update_user_profile,name="update_user_profile"),
    path("generate_api_key/<int:pk>",views.generate_api_key,name="generate_api_key"),

    path("generate_full_chat_report/<int:user_id>",views.generate_full_chat_report,name="generate_full_chat_report"),
     path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/user/<int:user_id>/', views.user_detailed_analytics, name='user_detailed_analytics'),
    path('analytics/download-pdf/', views.download_analytics_pdf, name='download_analytics_pdf'),
    path('analytics/chart-data/<int:user_id>/', views.get_chart_data, name='get_chart_data'),



    path("chatbot_response/", views.ChatBotAPI.as_view(), name="chatbot_response"),
    path("customer_details/",views.customer_details,name="customer_details")

]