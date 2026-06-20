# Novel Audio System / 智能小说有声书系统

一个端到端的小说爬取、管理与 TTS 有声书生成系统。粘贴小说目录 URL，即可自动提取目录、下载章节并生成有声书音频。

> **声明**：本项目仅提供本地自动化工具能力，代码本身不包含任何小说正文或音频。用户必须确保仅对自己拥有版权、已获授权或处于公共领域的内容使用本工具。

## 功能特性

- **智能目录提取**：粘贴小说目录页 URL，自动解析章节列表
- **Cloudflare / 反爬绕过**：当自动爬取被拦截时，可调用 Kimi WebBridge 在真实浏览器中完成验证并直接读取 DOM
- **章节下载与入库**：解析正文、去水印后写入数据库
- **TTS 有声书合成**：基于 Microsoft Edge TTS / GPT-SoVITS / CosyVoice 等引擎生成音频
- **Web 管理后台**：Django REST Framework + Vue 3 前后端分离，支持小说列表、章节管理、任务队列
- **异步任务队列**：django-q2 处理下载与合成任务

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 5.2.5 + Django REST Framework + django-q2 + SQLite |
| 前端 | Vue 3 + Vite + TypeScript + Element Plus |
| 爬虫 | cloudscraper + BeautifulSoup + Kimi WebBridge（可选） |
| TTS | Microsoft Edge TTS / GPT-SoVITS / CosyVoice / F5-TTS 等 |
| 任务队列 | django-q2 |

## 快速启动

### 环境要求

- Python 3.13+
- Node.js 20+
- Windows / Linux / macOS（开发主要在 Windows 上验证）

### 1. 后端

```powershell
# 进入后端目录
cd backend

# 复制环境变量模板（必须设置 SECRET_KEY）
copy ..\.env.example .env
# 然后编辑 .env，将 SECRET_KEY 替换为随机值：
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 创建并激活虚拟环境（推荐）
python -m venv .venv
.\.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 创建管理员（可选）
python manage.py createsuperuser

# 启动 Django 开发服务器
python manage.py runserver 0.0.0.0:8000

# 另起一个终端启动任务队列
python manage.py qcluster
```

### 2. 前端

```powershell
cd frontend

npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

### 3. 浏览器桥接（可选，用于绕过 Cloudflare）

安装并启动 [Kimi WebBridge](https://kimi-webbridge._example.com)（端口默认 `10086`）后，系统会在目录提取失败时自动提示在真实浏览器中完成验证。

## 使用流程

1. 打开前端页面 `http://localhost:5176`（Vite 默认端口，若被占用会自动顺延）
2. 粘贴小说目录页 URL，点击「提取目录」
3. 若站点启用 Cloudflare 验证，按弹窗提示在浏览器中完成验证
4. 选择章节范围，点击「下载章节」
5. 在 TTS 页面选择章节，点击「生成有声书」
6. 任务完成后下载音频文件

## 项目结构

```
.
├── backend/                 # Django 后端
│   ├── novels/              # 小说、章节、爬虫 API
│   ├── tts/                 # TTS 任务与合成服务
│   ├── crawlers/            # 爬虫实现
│   ├── generators/          # 音频生成器
│   ├── llms/                # LLM 相关模块
│   └── novel_audio_system/  # Django 配置
├── frontend/                # Vue 3 前端
│   └── src/
│       ├── views/           # 页面组件
│       └── layout/          # 布局组件
└── README.md
```

## 测试

```powershell
# 前端测试
cd frontend
npm run test

# 后端测试
cd backend
pytest
```

## 免责声明

本工具仅供学习研究和个人非商业用途。使用者应自行确保：

- 仅抓取自己拥有版权或已获授权的内容；
- 仅抓取公共领域作品；
- 遵守目标网站的 `robots.txt` 和服务条款；
- 不将本工具用于大规模爬取、二次分发或任何侵权行为。

开发者不对用户因使用本工具抓取、生成、传播第三方内容而产生的任何法律后果负责。

## 许可证

本项目代码采用 [Apache License 2.0](LICENSE) 开源。小说内容、生成的音频以及第三方模型权重均不属于本仓库授权范围。
