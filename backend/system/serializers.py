from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Department, Role, Menu, Dict, DictData, OperationLog, LoginLog


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    
    password = serializers.CharField(write_only=True, required=False)
    roles_info = serializers.SerializerMethodField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'nickname', 'email', 'phone', 'avatar',
            'is_active', 'is_staff', 'is_superuser', 'last_login',
            'last_login_ip', 'created_at', 'updated_at', 'password',
            'roles_info', 'department_name'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'last_login': {'read_only': True},
        }
    
    def get_roles_info(self, obj):
        """获取用户角色信息"""
        return [{'id': role.id, 'name': role.name, 'code': role.code} 
                for role in obj.roles.all()]
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""
    
    children = serializers.SerializerMethodField(read_only=True)
    leader_name = serializers.CharField(source='leader.nickname', read_only=True)
    
    class Meta:
        model = Department
        fields = '__all__'
    
    def get_children(self, obj):
        """获取子部门"""
        children = obj.children.filter(is_active=True).order_by('sort')
        return DepartmentSerializer(children, many=True).data


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    
    menu_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    department_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    
    class Meta:
        model = Role
        fields = '__all__'
    
    def create(self, validated_data):
        menu_ids = validated_data.pop('menu_ids', [])
        department_ids = validated_data.pop('department_ids', [])
        
        role = super().create(validated_data)
        
        if menu_ids:
            role.menus.set(menu_ids)
        if department_ids:
            role.departments.set(department_ids)
        
        return role
    
    def update(self, instance, validated_data):
        menu_ids = validated_data.pop('menu_ids', None)
        department_ids = validated_data.pop('department_ids', None)
        
        role = super().update(instance, validated_data)
        
        if menu_ids is not None:
            role.menus.set(menu_ids)
        if department_ids is not None:
            role.departments.set(department_ids)
        
        return role


class MenuSerializer(serializers.ModelSerializer):
    """菜单序列化器"""
    
    children = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Menu
        fields = '__all__'
    
    def get_children(self, obj):
        """获取子菜单"""
        children = obj.children.filter(visible=True).order_by('sort')
        return MenuSerializer(children, many=True).data


class DictSerializer(serializers.ModelSerializer):
    """字典类型序列化器"""
    
    class Meta:
        model = Dict
        fields = '__all__'


class DictDataSerializer(serializers.ModelSerializer):
    """字典数据序列化器"""
    
    dict_type_name = serializers.CharField(source='dict_type.name', read_only=True)
    
    class Meta:
        model = DictData
        fields = '__all__'


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器"""
    
    class Meta:
        model = OperationLog
        fields = '__all__'


class LoginLogSerializer(serializers.ModelSerializer):
    """登录日志序列化器"""
    
    class Meta:
        model = LoginLog
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('用户名或密码错误')
            if not user.is_active:
                raise serializers.ValidationError('用户账号已被禁用')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('用户名和密码不能为空')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """用户个人信息序列化器"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'email', 'phone', 'avatar']
        read_only_fields = ['username']


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError('两次输入的密码不一致')
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('原密码错误')
        return value
