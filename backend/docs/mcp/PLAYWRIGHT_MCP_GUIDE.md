# 🎭 Playwright高级MCP功能指南

## 概述

新的Playwright集成提供了更强大的网页爬取能力，支持：

- 🔍 **智能反爬虫检测** - 自动识别验证码和人机验证
- 👁️ **有头浏览器模式** - 可视化处理验证码
- 🤖 **自动化下载流程** - 从第一章开始自动下载整本小说
- 🛡️ **手动干预支持** - 遇到问题时可手动处理

## 功能对比

| 功能 | 传统requests | Playwright |
|------|-------------|------------|
| 浏览器环境 | 模拟请求头 | 真实Chrome浏览器 |
| JavaScript | ❌ 不支持 | ✅ 完整支持 |
| 反爬虫检测 | 容易被识别 | 难以被识别 |
| 验证码处理 | ❌ 无法处理 | ✅ 可手动处理 |
| 动态内容 | ❌ 无法获取 | ✅ 完整获取 |
| 可视化调试 | ❌ 无界面 | ✅ 有头模式 |

## 安装和设置

### 1. 安装依赖

```bash
# 安装Playwright
pip install playwright>=1.40.0

# 安装浏览器（必需）
python backend/setup_playwright.py
```

### 2. 验证安装

```bash
# 运行测试脚本
python backend/setup_playwright.py
```

## 使用方法

### 方式1：Django Admin界面

1. **进入Admin**: `http://localhost:8000/admin/`
2. **选择章节**: 勾选任意章节（用于确定小说）
3. **选择操作**: `🎭 Playwright自动下载`
4. **执行操作**: 点击"执行"按钮

#### Admin操作流程：
```
🔄 正在启动Playwright浏览器...
✅ Playwright浏览器启动成功
🚀 开始自动下载小说: 《示例小说》
✅ Playwright自动下载完成!
📊 总章节数: 1810
🆕 新章节数: 150
✅ 成功下载: 148
❌ 下载失败: 2
```

### 方式2：程序化调用

```python
from playwright_mcp_service import PlaywrightMCPService
from novels.models import Novel

# 创建服务
service = PlaywrightMCPService()

# 设置有头浏览器（便于处理验证码）
service.setup_browser(headless=False)  # 有头模式

# 获取小说
novel = Novel.objects.first()

# 自动下载（从第1章开始）
result = service.auto_download_novel(novel, start_from_chapter=1)

print(f"下载结果: {result}")

# 关闭浏览器
service.close()
```

## 工作模式

### 1. **手动模式** (默认)
- 遇到验证码时暂停并提示用户处理
- 用户在浏览器中完成验证后继续
- 适合需要人工干预的场景

```python
service = PlaywrightMCPService()
service.setup_browser(headless=False)  # 有头模式
service.disable_auto_mode()  # 手动模式
```

### 2. **自动化模式**
- 跳过需要手动处理的内容
- 适合已验证过的网站
- 速度更快但可能遗漏部分内容

```python
service = PlaywrightMCPService()
service.setup_browser(headless=True)   # 无头模式
service.enable_auto_mode()             # 自动化模式
```

## 智能功能

### 1. **验证码检测**
系统能自动检测以下情况：
- 页面标题包含"验证"、"验证码"
- URL包含"verify"、"captcha"
- 页面出现验证码组件
- 人机验证iframe

### 2. **内容处理**
- ✅ 移除广告和网站标识
- ✅ 提取纯文本内容
- ✅ 保持段落格式
- ✅ 统计字数

### 3. **错误恢复**
- 🔄 网络错误自动重试
- 🔄 页面加载失败时重新加载
- 🔄 浏览器崩溃时自动重启

### 4. **进度监控**
- 📊 实时显示下载进度
- 📈 统计成功/失败章节数
- 📋 详细的处理日志

## 实际使用场景

### 场景1：新小说下载
```python
# 选中新小说后自动下载
service = PlaywrightMCPService()
service.setup_browser(headless=False)
result = service.auto_download_novel(new_novel, start_from_chapter=1)
```

### 场景2：更新现有小说
```python
# 只下载新章节
last_chapter = Chapter.objects.filter(novel=novel).order_by('-chapter_sort_number').first()
start_from = last_chapter.chapter_sort_number + 1
result = service.auto_download_novel(novel, start_from_chapter=start_from)
```

### 场景3：处理反爬虫网站
```python
# 有头模式处理验证码
service = PlaywrightMCPService()
service.setup_browser(headless=False)  # 显示浏览器窗口
service.disable_auto_mode()  # 遇到验证码时暂停
result = service.auto_download_novel(novel)
```

## 性能优化

### 1. **并发控制**
- 控制同时打开的页面数量
- 设置合理的延时间隔
- 避免对网站造成过大压力

### 2. **缓存机制**
- 缓存已下载的章节内容
- 避免重复下载
- 支持断点续传

### 3. **资源管理**
- 自动清理浏览器进程
- 控制内存使用
- 定期重启浏览器

## 故障排除

### 常见问题

#### 1. Playwright安装失败
```bash
# 手动安装
pip install playwright
playwright install chromium

# 验证安装
python -c "from playwright.async_api import async_playwright; print('安装成功')"
```

#### 2. 浏览器启动失败
```python
# 检查系统要求
# - Python 3.7+
# - 足够的内存和磁盘空间
# - 网络连接正常

# 尝试无头模式
service.setup_browser(headless=True)
```

#### 3. 验证码处理
```python
# 方法1: 手动处理
service.disable_auto_mode()  # 遇到验证码时暂停

# 方法2: 跳过有验证码的页面
service.enable_auto_mode()   # 自动跳过
```

#### 4. 下载速度慢
```python
# 减少延时
service.download_delay = 1

# 启用自动化模式
service.enable_auto_mode()
```

## 技术细节

### 浏览器配置
```python
browser_options = {
    'headless': False,  # 有头模式
    'args': [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
    ]
}
```

### 页面设置
```python
await page.set_viewport_size({"width": 1366, "height": 768})
await page.set_extra_http_headers({
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
})
```

## 升级指南

### 从传统requests升级

```python
# 旧代码
from novels.views import MCPClientService
service = MCPClientService()
content = service.get_page_content(url)

# 新代码
from playwright_mcp_service import PlaywrightMCPService
service = PlaywrightMCPService()
service.setup_browser(headless=False)
content = service.get_page_content(url)
```

### 从其他爬虫工具迁移

```python
# Selenium迁移
# from selenium import webdriver
# driver = webdriver.Chrome()

# Playwright替代
from playwright.async_api import async_playwright
playwright = await async_playwright().start()
browser = await playwright.chromium.launch()
```

## 安全注意事项

1. **遵守网站条款** - 确保爬取行为符合网站robots.txt和使用条款
2. **合理频率** - 避免过于频繁的请求
3. **资源管理** - 及时关闭浏览器和清理资源
4. **数据隐私** - 不要爬取涉及个人隐私的数据

## 总结

Playwright高级MCP功能提供了：

- 🚀 **更强的反爬虫能力**
- 👁️ **可视化调试支持**
- 🤖 **智能自动化流程**
- 🛡️ **完善的错误处理**
- 📊 **详细的进度监控**

这是目前最先进的网页爬取解决方案，特别适合处理复杂的反爬虫网站！
