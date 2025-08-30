from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'menus', views.MenuViewSet)
router.register(r'dicts', views.DictViewSet)
router.register(r'dict-data', views.DictDataViewSet)
router.register(r'operation-logs', views.OperationLogViewSet)
router.register(r'login-logs', views.LoginLogViewSet)
router.register(r'auth', views.AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
]
