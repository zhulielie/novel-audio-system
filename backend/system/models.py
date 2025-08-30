from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import json


class User(AbstractUser):
    """扩展用户模型 - 集成 django-vue3-admin 的用户系统"""
    
    # 基本信息
    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    
    # 状态信息
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    last_login_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='最后登录IP')
    
    # 权限相关
    roles = models.ManyToManyField('Role', blank=True, verbose_name='角色')
    
    # 时间信息
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'system_user'
    
    def __str__(self):
        return self.nickname or self.username


class Department(models.Model):
    """部门模型"""
    
    name = models.CharField(max_length=100, verbose_name='部门名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='部门编码')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='children', verbose_name='上级部门')
    level = models.PositiveIntegerField(default=1, verbose_name='层级')
    sort = models.PositiveIntegerField(default=0, verbose_name='排序')
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='led_departments', verbose_name='部门负责人')
    phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    email = models.EmailField(blank=True, verbose_name='邮箱')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '部门'
        verbose_name_plural = '部门'
        ordering = ['sort', 'id']
        db_table = 'system_department'
    
    def __str__(self):
        return self.name


class Role(models.Model):
    """角色模型"""
    
    name = models.CharField(max_length=50, unique=True, verbose_name='角色名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='角色编码')
    description = models.TextField(blank=True, verbose_name='角色描述')
    
    # 数据权限范围
    DATA_SCOPE_CHOICES = [
        (1, '全部数据权限'),
        (2, '自定义数据权限'),
        (3, '本部门数据权限'),
        (4, '本部门及以下数据权限'),
        (5, '仅本人数据权限'),
    ]
    data_scope = models.IntegerField(choices=DATA_SCOPE_CHOICES, default=1, verbose_name='数据范围')
    
    # 关联权限
    menus = models.ManyToManyField('Menu', blank=True, verbose_name='菜单权限')
    departments = models.ManyToManyField(Department, blank=True, verbose_name='数据权限部门')
    
    sort = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'
        ordering = ['sort', 'id']
        db_table = 'system_role'
    
    def __str__(self):
        return self.name


class Menu(models.Model):
    """菜单模型"""
    
    MENU_TYPE_CHOICES = [
        ('M', '目录'),
        ('C', '菜单'),
        ('F', '按钮'),
    ]
    
    name = models.CharField(max_length=50, verbose_name='菜单名称')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='children', verbose_name='父菜单')
    menu_type = models.CharField(max_length=1, choices=MENU_TYPE_CHOICES, verbose_name='菜单类型')
    
    # 路由信息
    path = models.CharField(max_length=200, blank=True, verbose_name='路由地址')
    component = models.CharField(max_length=200, blank=True, verbose_name='组件路径')
    perms = models.CharField(max_length=100, blank=True, verbose_name='权限标识')
    
    # 显示信息
    icon = models.CharField(max_length=50, blank=True, verbose_name='菜单图标')
    sort = models.PositiveIntegerField(default=0, verbose_name='显示排序')
    
    # 状态控制
    visible = models.BooleanField(default=True, verbose_name='显示状态')
    is_frame = models.BooleanField(default=False, verbose_name='是否外链')
    is_cache = models.BooleanField(default=False, verbose_name='是否缓存')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '菜单'
        verbose_name_plural = '菜单'
        ordering = ['sort', 'id']
        db_table = 'system_menu'
    
    def __str__(self):
        return self.name


class Dict(models.Model):
    """字典类型模型"""
    
    name = models.CharField(max_length=100, verbose_name='字典名称')
    type = models.CharField(max_length=100, unique=True, verbose_name='字典类型')
    remark = models.TextField(blank=True, verbose_name='备注')
    is_active = models.BooleanField(default=True, verbose_name='状态')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '字典类型'
        verbose_name_plural = '字典类型'
        db_table = 'system_dict'
    
    def __str__(self):
        return self.name


class DictData(models.Model):
    """字典数据模型"""
    
    dict_type = models.ForeignKey(Dict, on_delete=models.CASCADE, related_name='data', verbose_name='字典类型')
    label = models.CharField(max_length=100, verbose_name='字典标签')
    value = models.CharField(max_length=100, verbose_name='字典键值')
    sort = models.PositiveIntegerField(default=0, verbose_name='排序')
    css_class = models.CharField(max_length=100, blank=True, verbose_name='样式属性')
    list_class = models.CharField(max_length=100, blank=True, verbose_name='表格回显样式')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    is_active = models.BooleanField(default=True, verbose_name='状态')
    remark = models.TextField(blank=True, verbose_name='备注')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '字典数据'
        verbose_name_plural = '字典数据'
        ordering = ['sort', 'id']
        db_table = 'system_dict_data'
        unique_together = ['dict_type', 'value']
    
    def __str__(self):
        return f'{self.dict_type.name} - {self.label}'


class OperationLog(models.Model):
    """操作日志模型"""
    
    BUSINESS_TYPE_CHOICES = [
        (0, '其它'),
        (1, '新增'),
        (2, '修改'),
        (3, '删除'),
        (4, '授权'),
        (5, '导出'),
        (6, '导入'),
        (7, '强退'),
        (8, '生成代码'),
        (9, '清空数据'),
    ]
    
    OPERATOR_TYPE_CHOICES = [
        (1, '后台用户'),
        (2, '手机端用户'),
    ]
    
    # 操作信息
    title = models.CharField(max_length=50, verbose_name='模块标题')
    business_type = models.IntegerField(choices=BUSINESS_TYPE_CHOICES, default=0, verbose_name='业务类型')
    method = models.CharField(max_length=100, verbose_name='方法名称')
    request_method = models.CharField(max_length=10, verbose_name='请求方式')
    operator_type = models.IntegerField(choices=OPERATOR_TYPE_CHOICES, default=1, verbose_name='操作类别')
    
    # 操作人员
    oper_name = models.CharField(max_length=50, verbose_name='操作人员')
    dept_name = models.CharField(max_length=50, blank=True, verbose_name='部门名称')
    
    # 请求信息
    oper_url = models.CharField(max_length=255, verbose_name='请求URL')
    oper_ip = models.GenericIPAddressField(verbose_name='主机地址')
    oper_location = models.CharField(max_length=255, blank=True, verbose_name='操作地点')
    oper_param = models.TextField(blank=True, verbose_name='请求参数')
    
    # 响应信息
    json_result = models.TextField(blank=True, verbose_name='返回参数')
    status = models.IntegerField(default=0, verbose_name='操作状态')
    error_msg = models.TextField(blank=True, verbose_name='错误消息')
    
    # 时间信息
    oper_time = models.DateTimeField(default=timezone.now, verbose_name='操作时间')
    cost_time = models.BigIntegerField(default=0, verbose_name='消耗时间')
    
    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'
        ordering = ['-oper_time']
        db_table = 'system_operation_log'
    
    def __str__(self):
        return f'{self.title} - {self.oper_name}'


class LoginLog(models.Model):
    """登录日志模型"""
    
    user_name = models.CharField(max_length=50, verbose_name='用户账号')
    ipaddr = models.GenericIPAddressField(verbose_name='登录IP地址')
    login_location = models.CharField(max_length=255, blank=True, verbose_name='登录地点')
    browser = models.CharField(max_length=50, blank=True, verbose_name='浏览器类型')
    os = models.CharField(max_length=50, blank=True, verbose_name='操作系统')
    status = models.CharField(max_length=1, verbose_name='登录状态')
    msg = models.CharField(max_length=255, blank=True, verbose_name='提示消息')
    login_time = models.DateTimeField(default=timezone.now, verbose_name='访问时间')
    
    class Meta:
        verbose_name = '登录日志'
        verbose_name_plural = '登录日志'
        ordering = ['-login_time']
        db_table = 'system_login_log'
    
    def __str__(self):
        return f'{self.user_name} - {self.login_time}'
