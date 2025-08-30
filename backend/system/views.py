from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import User, Department, Role, Menu, Dict, DictData, OperationLog, LoginLog
from .serializers import (
    UserSerializer, DepartmentSerializer, RoleSerializer, MenuSerializer,
    DictSerializer, DictDataSerializer, OperationLogSerializer, LoginLogSerializer,
    LoginSerializer, UserProfileSerializer, ChangePasswordSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """用户管理视图集"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'nickname', 'email', 'phone']
    ordering_fields = ['id', 'username', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """获取当前用户信息"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """更新用户个人信息"""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """修改密码"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({'message': '密码修改成功'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """重置用户密码"""
        user = self.get_object()
        new_password = request.data.get('password', '123456')
        user.set_password(new_password)
        user.save()
        return Response({'message': f'密码已重置为: {new_password}'})


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门管理视图集"""
    
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['sort', 'created_at']
    ordering = ['sort']
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取部门树结构"""
        departments = self.queryset.filter(parent=None).order_by('sort')
        serializer = self.get_serializer(departments, many=True)
        return Response(serializer.data)


class RoleViewSet(viewsets.ModelViewSet):
    """角色管理视图集"""
    
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['sort', 'created_at']
    ordering = ['sort']
    
    @action(detail=True, methods=['get'])
    def menus(self, request, pk=None):
        """获取角色菜单权限"""
        role = self.get_object()
        menu_ids = list(role.menus.values_list('id', flat=True))
        return Response({'menu_ids': menu_ids})
    
    @action(detail=True, methods=['post'])
    def assign_menus(self, request, pk=None):
        """分配菜单权限"""
        role = self.get_object()
        menu_ids = request.data.get('menu_ids', [])
        role.menus.set(menu_ids)
        return Response({'message': '菜单权限分配成功'})


class MenuViewSet(viewsets.ModelViewSet):
    """菜单管理视图集"""
    
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'path', 'component']
    ordering_fields = ['sort', 'created_at']
    ordering = ['sort']
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取菜单树结构"""
        menus = self.queryset.filter(parent=None, visible=True).order_by('sort')
        serializer = self.get_serializer(menus, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_menus(self, request):
        """获取当前用户菜单"""
        user = request.user
        if user.is_superuser:
            # 超级管理员获取所有菜单
            menus = self.queryset.filter(parent=None, visible=True).order_by('sort')
        else:
            # 普通用户根据角色获取菜单
            role_ids = user.roles.values_list('id', flat=True)
            menu_ids = Role.objects.filter(id__in=role_ids).values_list('menus', flat=True)
            menus = self.queryset.filter(
                id__in=menu_ids, parent=None, visible=True
            ).order_by('sort')
        
        serializer = self.get_serializer(menus, many=True)
        return Response(serializer.data)


class DictViewSet(viewsets.ModelViewSet):
    """字典类型管理视图集"""
    
    queryset = Dict.objects.filter(is_active=True)
    serializer_class = DictSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'type']
    ordering = ['-created_at']


class DictDataViewSet(viewsets.ModelViewSet):
    """字典数据管理视图集"""
    
    queryset = DictData.objects.filter(is_active=True)
    serializer_class = DictDataSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['dict_type']
    search_fields = ['label', 'value']
    ordering_fields = ['sort', 'created_at']
    ordering = ['sort']
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """根据字典类型获取数据"""
        dict_type = request.query_params.get('type')
        if not dict_type:
            return Response({'error': '字典类型不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = self.queryset.filter(dict_type__type=dict_type).order_by('sort')
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """操作日志视图集"""
    
    queryset = OperationLog.objects.all()
    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business_type', 'status', 'operator_type']
    search_fields = ['title', 'oper_name', 'oper_ip']
    ordering = ['-oper_time']


class LoginLogViewSet(viewsets.ReadOnlyModelViewSet):
    """登录日志视图集"""
    
    queryset = LoginLog.objects.all()
    serializer_class = LoginLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['user_name', 'ipaddr', 'login_location']
    ordering = ['-login_time']


class AuthViewSet(viewsets.GenericViewSet):
    """认证相关视图集"""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """用户登录"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # 生成JWT令牌
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # 记录登录日志
            LoginLog.objects.create(
                user_name=user.username,
                ipaddr=self.get_client_ip(request),
                login_location='',  # 可以集成IP地址解析服务
                browser=request.META.get('HTTP_USER_AGENT', '')[:50],
                os='',  # 可以解析User-Agent获取操作系统
                status='0',  # 成功
                msg='登录成功'
            )
            
            # 更新最后登录IP
            user.last_login_ip = self.get_client_ip(request)
            user.save(update_fields=['last_login_ip'])
            
            return Response({
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'user_info': UserSerializer(user).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """用户登出"""
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': '登出成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """刷新令牌"""
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({'error': 'refresh_token不能为空'}, status=status.HTTP_400_BAD_REQUEST)
            
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token
            
            return Response({
                'access_token': str(access_token)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
