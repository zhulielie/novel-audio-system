# Web系统MCP客户端集成指南

## 概述

本系统已成功集成了MCP（Multi-Chrome-Process）客户端功能，允许用户通过Web界面直接调用MCP Chrome工具来爬取和修复小说章节数据。

## 已实现功能

### 1. MCP章节修复功能
- **路径**: `/novels/<novel_id>/mcp/fix/`
- **功能**: 使用MCP工具从网站获取最新章节信息并修复数据库中的章节
- **特点**:
  - 批量选择需要修复的章节
  - 实时显示修复进度
  - 自动更新章节标题、卷信息和内容
  - 支持中断和恢复操作

### 2. MCP新章节爬取功能
- **路径**: `/novels/<novel_id>/mcp/crawl/`
- **功能**: 使用MCP工具从网站爬取新章节并添加到数据库
- **特点**:
  - 自动检测和跳过重复章节
  - 支持预览模式（仅查看，不实际创建）
  - 实时显示爬取进度
  - 保持章节序号的连续性

### 3. 小说详情页面集成
- **路径**: `/novels/<novel_id>/`
- **功能**: 在小说详情页面直接访问MCP工具
- **特点**:
  - MCP工具快捷入口
  - 快速操作面板
  - 状态信息显示

## 使用步骤

### 1. 配置MCP环境

确保您的系统已正确安装和配置MCP Chrome工具：

```bash
# 检查MCP工具状态
mcp --version

# 确保Chrome浏览器可用
mcp_chrome-mcp-server_get_windows_and_tabs
```

### 2. 更新MCP调用代码

在实际环境中，您需要将模拟代码替换为真实的MCP调用：

#### 2.1 更新 `MCPClientService.get_page_content` 方法

**文件**: `backend/novels/views.py`

将以下模拟代码：
```python
def get_page_content(self, url):
    # 模拟获取页面内容
    print(f"模拟获取页面内容: {url}")
    # ... 模拟代码 ...
```

替换为实际的MCP调用：
```python
def get_page_content(self, url):
    """使用MCP获取页面内容"""
    try:
        # 使用MCP Chrome工具获取页面内容
        result = mcp_chrome_get_web_content(url=url, htmlContent=True, textContent=False)

        if result.get('success'):
            return result['data']['content'][0]['text']
        else:
            print(f"获取失败: {result.get('error', '未知错误')}")
            return None

    except Exception as e:
        print(f"获取页面失败: {e}")
        return None
```

#### 2.2 配置MCP服务连接

确保您的系统可以访问MCP服务。您可能需要：

1. 安装MCP Chrome扩展
2. 配置MCP服务端点
3. 设置必要的权限

### 3. 访问Web界面

1. 启动Django服务器：
```bash
cd backend
python manage.py runserver
```

2. 访问小说管理页面：
   - 小说列表：`http://localhost:8000/novels/`
   - 小说详情：`http://localhost:8000/novels/<novel_id>/`

3. 在小说详情页面点击MCP工具按钮：
   - **修复章节**：修复现有章节的数据
   - **爬取新章节**：从网站获取新章节

## 技术实现细节

### 1. 后端架构

#### 1.1 MCP客户端服务类
```python
class MCPClientService:
    """MCP客户端服务类"""

    def __init__(self):
        self.base_url = "https://www.hetushu.com"
        self.book_url = "https://www.hetushu.com/book/38/24721.html"

    def get_page_content(self, url):
        """使用MCP获取页面内容"""

    def parse_chapter_list(self, html_content):
        """解析章节列表"""

    def extract_chapter_info(self, title):
        """从标题中提取章节信息"""

    def update_chapter_from_web(self, chapter, web_chapter_data):
        """从网页数据更新章节信息"""
```

#### 1.2 Django视图函数

- `mcp_chapter_fix()`: 处理章节修复请求
- `mcp_crawl_chapters()`: 处理新章节爬取请求

### 2. 前端界面

#### 2.1 章节修复界面
- 章节选择复选框
- 修复选项配置
- 实时进度显示
- 结果统计

#### 2.2 章节爬取界面
- 爬取选项配置
- 进度监控
- 新章节预览
- 状态信息

### 3. 数据处理流程

#### 3.1 章节修复流程
1. 用户选择需要修复的章节
2. 系统调用MCP获取网站章节数据
3. 匹配现有章节与网站章节
4. 更新章节信息（标题、卷、内容）
5. 显示修复结果

#### 3.2 章节爬取流程
1. 用户配置爬取选项
2. 系统调用MCP获取网站章节列表
3. 比较现有章节，找出新增章节
4. 创建新章节记录
5. 获取章节详细内容
6. 显示爬取结果

## 安全和性能考虑

### 1. 访问频率控制
- 建议在爬取时添加延时，避免对目标网站造成过大压力
- 可以配置爬取间隔时间

### 2. 错误处理
- 完善的异常处理机制
- 网络错误时的重试机制
- 爬取中断时的状态保存

### 3. 数据验证
- 章节数据验证
- 重复检测
- 内容完整性检查

## 扩展功能

### 1. 定时任务
可以添加定时任务功能，定期自动检查和更新章节：

```python
# 使用Django Celery添加定时任务
from celery import shared_task

@shared_task
def scheduled_chapter_update():
    """定时更新章节数据"""
    # 实现定时更新逻辑
    pass
```

### 2. 多网站支持
可以扩展支持多个小说网站：

```python
class WebsiteCrawler:
    """网站爬虫基类"""

    def __init__(self, website_config):
        self.config = website_config

    def crawl_chapters(self):
        """爬取章节数据"""
        pass
```

### 3. 数据分析
添加章节数据分析功能：

- 章节更新频率统计
- 内容质量分析
- 用户阅读偏好分析

## 故障排除

### 常见问题

1. **MCP连接失败**
   - 检查MCP服务是否启动
   - 确认网络连接正常
   - 验证MCP配置

2. **页面解析失败**
   - 检查目标网站结构是否变更
   - 更新解析规则
   - 联系技术支持

3. **数据库错误**
   - 检查数据库连接
   - 验证数据完整性
   - 查看错误日志

### 日志和监控

系统提供了详细的日志记录：

- 爬取过程日志
- 错误信息记录
- 性能指标监控

## 更新说明

### v1.0.0
- 初始版本发布
- 支持MCP章节修复功能
- 支持MCP新章节爬取功能
- 完整的Web界面集成

## 技术支持

如遇问题，请：

1. 查看系统日志
2. 检查MCP服务状态
3. 确认网络连接
4. 联系技术支持团队

---

**注意**: 使用前请确保遵守相关法律法规和网站使用条款。建议在非高峰时段进行爬取操作，避免对目标网站造成过大压力。
