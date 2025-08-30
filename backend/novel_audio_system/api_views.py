from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """自定义JWT登录视图"""
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    """用户注册视图"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # 自动生成JWT令牌
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': '注册成功'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """用户资料视图"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'user': serializer.data,
            'message': '资料更新成功'
        })


class ChangePasswordView(generics.UpdateAPIView):
    """修改密码视图"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': '密码修改成功，请重新登录'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """退出登录视图"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': '退出登录成功'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': f'退出登录失败: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info_view(request):
    """获取当前用户信息"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account_view(request):
    """删除账户"""
    password = request.data.get('password')
    
    if not password:
        return Response({
            'error': '请提供密码以确认删除操作'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    if not user.check_password(password):
        return Response({
            'error': '密码不正确'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 软删除：设置为非活跃状态
        user.is_active = False
        user.save()
        
        return Response({
            'message': '账户已删除'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': f'删除账户失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def check_username_view(request):
    """检查用户名是否可用"""
    username = request.data.get('username')
    
    if not username:
        return Response({
            'error': '请提供用户名'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    exists = User.objects.filter(username=username).exists()
    
    return Response({
        'available': not exists,
        'message': '用户名可用' if not exists else '用户名已被使用'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def check_email_view(request):
    """检查邮箱是否可用"""
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': '请提供邮箱地址'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    exists = User.objects.filter(email=email).exists()
    
    return Response({
        'available': not exists,
        'message': '邮箱可用' if not exists else '邮箱已被使用'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(request):
    """获取仪表板统计信息"""
    from novels.models import Novel, Chapter
    from audios.models import AudioProject
    from generators.models import Workflow, Task
    
    # 统计数据
    novels_count = Novel.objects.count()
    chapters_count = Chapter.objects.count()
    audio_projects_count = AudioProject.objects.count()
    workflows_count = Workflow.objects.count()
    
    # 最近活动
    recent_novels = Novel.objects.order_by('-created_at')[:5]
    recent_chapters = Chapter.objects.order_by('-created_at')[:5]
    recent_tasks = Task.objects.order_by('-created_at')[:5]
    
    return Response({
        'stats': {
            'novels': novels_count,
            'chapters': chapters_count,
            'audio_projects': audio_projects_count,
            'workflows': workflows_count
        },
        'recent_activity': {
            'novels': [{
                'id': novel.id,
                'title': novel.title,
                'created_at': novel.created_at
            } for novel in recent_novels],
            'chapters': [{
                'id': chapter.id,
                'title': chapter.title,
                'novel_title': chapter.novel.title,
                'created_at': chapter.created_at
            } for chapter in recent_chapters],
            'tasks': [{
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'created_at': task.created_at
            } for task in recent_tasks]
        }
    })