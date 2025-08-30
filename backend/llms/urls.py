from django.urls import path
from . import views

app_name = 'llms'

urlpatterns = [
    # LLM模型相关URL
    path('models/', views.llm_model_list, name='llm_model_list'),
    path('models/create/', views.create_llm_model, name='create_model'),
    path('models/<int:model_id>/', views.llm_model_detail, name='model_detail'),
    
    # API密钥相关URL
    path('api-keys/', views.api_key_list, name='api_key_list'),
    path('api-keys/create/', views.create_api_key, name='create_api_key'),
    path('api-keys/<int:api_key_id>/test/', views.test_api_key, name='test_api_key'),
    
    # LLM请求相关URL
    path('requests/', views.llm_request_list, name='request_list'),
    path('requests/send/', views.send_llm_request, name='send_request'),
    path('requests/<int:request_id>/', views.llm_request_detail, name='request_detail'),
    
    # 统计相关URL
    path('statistics/', views.llm_statistics, name='statistics'),
]