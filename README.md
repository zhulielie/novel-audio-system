# 智能小说管理系统

> 一个端到端的小说爬取、管理与 TTS 有声书生成系统。粘贴小说 URL → 自动下载章节 → 生成 MP3 有声书。

## 功能特性

- **智能爬虫**：粘贴和图书等小说目录 URL，自动解析并下载章节
- **小说管理**：小说列表、章节管理、在线阅读器
- **TTS 合成**：基于 Microsoft Edge TTS，一键生成有声书 MP3
- **工作流编排**：从 URL 到 MP3 的完整 pipeline
- **本地 Fallback**：和图书在线爬取被 Cloudflare 拦截时，自动使用本地示例数据完成演示

## 技术栈

- 后端：Django 5.2.5 + Django REST Framework + django-q2 + SQLite
- 前端：Vue 3 + Vite + TypeScript + Element Plus
- TTS：Microsoft Edge TTS（在线，无需 GPU / 本地音色资源）
- 爬虫：cloudscraper + 本地文本解析 fallback

## 快速启动

### 环境要求

- Python 3.13+
- Node.js 20+
- Windows（当前脚本为 PowerShell 风格）

### 一键启动（推荐）

Windows 用户直接双击运行项目根目录的启动脚本：

```powershell
# PowerShell
.\start-demo.ps1

# 或双击
start-demo.bat
```

脚本会自动打开 3 个终端窗口并启动后端、任务队列和前端。若默认端口 5176 被占用，前端会自动递增到可用端口。

### 手动启动

```powershell
# 终端 1：Django 后端（端口 8000）
cd backend
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

# 终端 2：django-q2 任务队列
cd backend
.venv\Scripts\python.exe manage.py qcluster

# 终端 3：Vue 前端（端口 5176）
cd frontend
npx vite --port 5176
```

打开浏览器访问控制台打印的地址（通常是 http://localhost:5176）。

### 生产构建

```powershell
cd frontend
npm run build
```

构建产物位于 `frontend/dist/`。

## 体验流程

1. 打开前端地址，使用默认账号登录：
   - 用户名：`admin`
   - 密码：`admin123456`
2. 进入 **爬虫管理 → 智能爬虫**
3. 粘贴示例 URL：
   ```
   https://www.hetushu.com/book/1311/index.html
   ```
4. 选择要下载的章节范围（建议 1-3 章），点击 **导入并生成有声书**
5. 若和图书被 Cloudflare 拦截，会弹出确认框，点击 **确定导入** 使用本地示例数据继续体验
6. 导入成功后，点击 **下一步：生成 MP3 有声书**
7. 在 TTS 页面选择小说/章节，点击 **快速合成**
8. 等待任务完成，即可下载 MP3 音频

> 若和图书返回 403，系统会自动 fallback 到本地《国医高手》示例数据，确保演示可完整跑通。

## 项目结构

```
.
├── backend/          # Django 后端
│   ├── novels/       # 小说与章节 API
│   ├── tts/          # TTS 合成模块
│   └── ...
└── frontend/         # Vue3 前端
    ├── src/views/    # 页面
    └── dist/         # 构建产物
```

## 默认账号

- 管理员：`admin` / `admin123456`

## 端到端验证

项目根目录提供 `e2e_verify.py`，可自动跑通完整链路并生成截图：

**登录 → 爬虫导入 → 小说列表 → 在线阅读 → TTS 快速合成 → 任务完成 → 音频下载**

```powershell
cd backend
.venv\Scripts\python.exe ..\e2e_verify.py
```

> 运行前请确保 playwright 和 requests 已安装在后端虚拟环境中。

## 测试

### 后端 API 测试（pytest）

```powershell
cd backend
.venv\Scripts\python.exe -m pytest
```

覆盖：认证登录、小说/章节 CRUD、TTS 任务创建等。

### 前端单元测试（vitest）

```powershell
cd frontend
npm run test
```

已包含 Pinia store 等核心逻辑测试。

### 端到端测试

见上文 `e2e_verify.py`。

## 已知限制

- 和图书（hetushu.com）当前有 Cloudflare 防护，在线爬取可能 403，Demo 已用本地数据兜底

## 许可证

MIT
