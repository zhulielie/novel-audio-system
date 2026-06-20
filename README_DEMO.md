# 智能小说管理系统 — Demo 指南

> 一个最小可用的端到端演示：粘贴和图书小说 URL → 自动下载章节 → 生成 MP3 有声书。

## 快速启动

```bash
# 1. 启动后端（端口 8000）
cd backend
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

# 2. 启动 TTS 任务队列（新窗口）
cd backend
.venv\Scripts\python.exe manage.py qcluster

# 3. 启动前端（新窗口，端口 5176）
cd frontend
npx vite --port 5176
```

## 体验流程

1. 打开 http://localhost:5176
2. 使用默认账号登录：
   - 用户名：`admin`
   - 密码：`admin123456`
3. 进入 **爬虫管理 → 智能爬虫**
4. 粘贴示例 URL：
   ```
   https://www.hetushu.com/book/1311/index.html
   ```
5. 选择要下载的章节范围（建议 1-3 章），点击 **导入并生成有声书**
6. 导入成功后，点击 **下一步：生成 MP3 有声书**
7. 在 TTS 页面选择章节，点击 **快速合成**
8. 等待任务完成，即可下载 MP3 音频

## 环境说明

- 后端：Django 5.2.5 + DRF + django-q2 + SQLite
- 前端：Vue 3 + Vite + TypeScript + Element Plus
- TTS：Microsoft Edge TTS（在线，无需 GPU / 本地音色资源）
- 爬虫：cloudscraper + 和图书解析

## 关于和图书 Cloudflare 保护

当前和图书（hetushu.com）对自动请求有 Cloudflare 防护，在线爬取可能会返回 403。Demo 已内置本地 fallback：当在线爬取失败时，会自动使用本地示例小说《国医高手》第 1-5 章数据完成导入，确保演示流程可完整跑通。

## 本次聚焦的垂直链路

为突出 "URL → 章节 → MP3" 的核心体验，Demo 隐藏了系统管理、来源管理、VoxCPM 调参、批量下载等非必需模块。

## 已知问题

- 前端 build 时 Rollup 会提示部分 chunk > 500KB，这是 Element Plus 等依赖导致的，不影响构建和运行。
- 和图书在线爬取目前处于不可用状态，后续可通过轮换 UA、代理池或专用浏览器绕过 Cloudflare。
