# 🛡️ 安全爬虫指南

## ⚠️ 重要提醒
**请务必遵循网站的robots.txt和服务条款，避免过度请求导致IP被封禁！**

## 📋 安全设置总览

### 当前默认设置
```python
# 请求频率限制
每日限制: 50次
每小时限制: 20次
每分钟限制: 5次

# 延时设置
下载间隔: 8秒
页面加载等待: 12秒
请求间隔: 5秒
随机延时: 3-12秒
```

## 🎛️ 配置方法

### 方法1：使用配置工具
```bash
cd backend
python safe_crawler_config.py
```

### 方法2：直接编辑配置文件
```bash
# 编辑配置文件
nano backend/safe_crawler_config.json
```

### 方法3：代码中调整
```python
from simple_playwright_service import SimplePlaywrightService

service = SimplePlaywrightService()
service.daily_request_limit = 30  # 调整每日限制
service.download_delay = 10      # 调整下载间隔
```

## 📊 风险等级推荐

### 🟢 安全模式（推荐新手）
```json
{
  "request_limits": {
    "daily_limit": 30,
    "hourly_limit": 10
  },
  "delays": {
    "download_delay": 15,
    "page_load_delay": 20,
    "request_interval": 10
  }
}
```

### 🟡 正常模式（推荐日常使用）
```json
{
  "request_limits": {
    "daily_limit": 50,
    "hourly_limit": 20
  },
  "delays": {
    "download_delay": 8,
    "page_load_delay": 12,
    "request_interval": 5
  }
}
```

### 🔴 激进模式（不推荐）
```json
{
  "request_limits": {
    "daily_limit": 100,
    "hourly_limit": 40
  },
  "delays": {
    "download_delay": 3,
    "page_load_delay": 5,
    "request_interval": 2
  }
}
```

## 🧑‍💻 行为模拟设置

### 启用人类行为模拟
```json
{
  "behavior_simulation": {
    "enable_scroll": true,
    "scroll_probability": 0.7,
    "reading_time_min": 8,
    "reading_time_max": 20
  }
}
```

### 模拟行为说明
- **页面滚动**: 随机滚动到不同位置
- **阅读时间**: 模拟人类阅读间隔
- **随机行为**: 70%概率执行滚动
- **多样化**: 每次访问行为不同

## 📈 实时监控

### 查看当前状态
```bash
# 在Django Admin中可以看到：
今日请求: 5/50
小时请求: 2/20
剩余可用: 45次
```

### 智能警告
- 接近每日限制时自动警告
- 超过限制时自动暂停
- 详细的日志记录

## 🛑 安全最佳实践

### 1. 遵守网站规则
```python
# 检查robots.txt
import requests
robots = requests.get("https://www.hetushu.com/robots.txt")
print(robots.text)
```

### 2. 分批下载
```python
# 不要一次性下载太多章节
MAX_CHAPTERS_PER_BATCH = 10

# 定期检查状态
if remaining_daily < 10:
    print("⚠️  剩余请求不足，建议暂停")
```

### 3. 错误处理
```python
# 遇到错误时增加延时
error_count = 0
if error_count > 3:
    time.sleep(60)  # 错误过多时暂停1分钟
```

### 4. IP轮换
```python
# 如果有条件，使用代理IP
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
}
```

## 🔍 故障排除

### 问题：请求被拒绝
```
解决方案：
1. 增加延时时间
2. 减少每日请求限制
3. 检查是否触发了频率限制
```

### 问题：页面加载失败
```
解决方案：
1. 增加页面加载等待时间
2. 检查网络连接
3. 尝试重新加载页面
```

### 问题：达到请求限制
```
解决方案：
1. 等待限制重置（每日/小时）
2. 降低请求频率
3. 分批次执行任务
```

## 📊 使用统计

### 安全模式效果
- **请求成功率**: >95%
- **平均延时**: 15秒/请求
- **每日容量**: 30章节
- **被封风险**: 极低

### 正常模式效果
- **请求成功率**: >90%
- **平均延时**: 8秒/请求
- **每日容量**: 50章节
- **被封风险**: 低

## ⚙️ 高级配置

### 自定义延时策略
```python
def custom_delay_strategy(self, chapter_count, elapsed_time):
    """自定义延时策略"""
    if chapter_count > 100:
        return max(15, self.download_delay * 1.5)  # 大量下载时延时更长
    elif elapsed_time > 3600:  # 1小时后
        return max(10, self.download_delay * 0.8)  # 逐渐减少延时
    else:
        return self.download_delay
```

### 动态频率控制
```python
def adaptive_rate_control(self, success_rate):
    """根据成功率动态调整频率"""
    if success_rate < 0.8:  # 成功率低于80%
        self.download_delay *= 1.2  # 增加延时
        print("⚠️  检测到失败率上升，增加延时")
    elif success_rate > 0.95:  # 成功率高于95%
        self.download_delay *= 0.9  # 减少延时
        print("✅  成功率良好，减少延时")
```

## 🎯 快速开始

### 1. 应用安全模式
```bash
cd backend
python safe_crawler_config.py
# 选择 "safe" 模式
```

### 2. 测试配置
```bash
cd backend
python test_simple_playwright.py
```

### 3. 开始下载
```bash
# 访问Django Admin
# 选择小说 -> 点击 "🎭 Playwright自动下载"
```

## 📞 联系与支持

如果遇到问题或需要调整配置，请：

1. **查看日志**: 检查控制台输出
2. **调整设置**: 使用配置工具修改参数
3. **重启服务**: 确保配置生效
4. **分批测试**: 先小批量测试再大规模使用

**记住：安全第一，慢即是快！🚀**
