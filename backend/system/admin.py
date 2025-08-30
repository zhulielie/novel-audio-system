from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Department, Role, Menu, Dict, DictData, OperationLog, LoginLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理"""
    
    list_display = ['username', 'nickname', 'email', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['username', 'nickname', 'email', 'phone']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {
            'fields': ('nickname', 'avatar', 'phone', 'last_login_ip', 'roles')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('扩展信息', {
            'fields': ('nickname', 'email', 'phone')
        }),
    )
    
    filter_horizontal = ['roles']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """部门管理"""
    
    list_display = ['name', 'code', 'parent', 'leader', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['sort', 'created_at']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理"""
    
    list_display = ['name', 'code', 'data_scope', 'is_active', 'created_at']
    list_filter = ['data_scope', 'is_active', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['sort', 'created_at']
    
    filter_horizontal = ['menus', 'departments']


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    """菜单管理"""
    
    list_display = ['name', 'parent', 'menu_type', 'path', 'visible', 'sort']
    list_filter = ['menu_type', 'visible', 'is_frame', 'is_cache']
    search_fields = ['name', 'path', 'component']
    ordering = ['sort', 'created_at']


@admin.register(Dict)
class DictAdmin(admin.ModelAdmin):
    """字典类型管理"""
    
    list_display = ['name', 'type', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'type']
    ordering = ['-created_at']


@admin.register(DictData)
class DictDataAdmin(admin.ModelAdmin):
    """字典数据管理"""
    
    list_display = ['dict_type', 'label', 'value', 'sort', 'is_active']
    list_filter = ['dict_type', 'is_active', 'is_default']
    search_fields = ['label', 'value']
    ordering = ['dict_type', 'sort']


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    """操作日志管理"""
    
    list_display = ['title', 'oper_name', 'business_type', 'status', 'oper_time']
    list_filter = ['business_type', 'status', 'operator_type', 'oper_time']
    search_fields = ['title', 'oper_name', 'oper_ip']
    ordering = ['-oper_time']
    
    readonly_fields = ['oper_time']


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    """登录日志管理"""
    
    list_display = ['user_name', 'ipaddr', 'login_location', 'status', 'login_time']
    list_filter = ['status', 'login_time']
    search_fields = ['user_name', 'ipaddr', 'login_location']
    ordering = ['-login_time']
    
    readonly_fields = ['login_time']
