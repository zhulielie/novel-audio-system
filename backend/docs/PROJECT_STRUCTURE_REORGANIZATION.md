# 小说音频系统 - 项目结构整理文档

## 整理概述

本次整理将原本混乱的项目结构重新组织，按功能模块分类，提高代码可维护性和可读性。

## 整理前后对比

### 整理前问题
- 文件分散在根目录，难以管理
- 重复的爬虫文件和测试文件
- 文档散落各处，缺乏统一管理
- 配置文件混杂在代码中

### 整理后结构

```
backend/
├── 📁 config/                     # 配置文件目录
│   └── admin_credentials.txt       # 管理员凭据
│
├── 📁 crawlers/                    # 爬虫模块目录 (已统一整合)
│   ├── unified_crawler.py        # 统一爬虫模块 (整合所有爬虫功能)
│   ├── universal_novel_downloader.py # 通用小说下载器
│   ├── downloader_config.json    # 下载器配置
│   └── enhanced_downloader_config.json # 增强下载器配置
│
├── 📁 docs/                       # 文档目录
│   ├── 📁 admin/                  # 管理相关文档
│   │   ├── DJANGO_ADMIN_MCP_GUIDE.md
│   │   ├── NOVEL_ADMIN_CRAWL_GUIDE.md
│   │   └── NOVEL_SOURCE_SYSTEM_GUIDE.md
│   ├── 📁 api/                    # API文档
│   │   └── API_DOCUMENTATION.md
│   ├── 📁 crawler/                # 爬虫文档
│   │   ├── CRAWLER_STATUS_SUMMARY.md
│   │   ├── Django爬虫使用指南.md
│   │   ├── INTELLIGENT_BATCH_IMPORT_GUIDE.md
│   │   ├── LLM_CRAWLER_ANALYZER_GUIDE.md
│   │   └── 爬虫配置说明.md
│   ├── 📁 mcp/                    # MCP相关文档
│   │   ├── MCP_CRAWLER_README.md
│   │   ├── MCP_FIX_GUIDE.md
│   │   ├── MCP_WEB_INTEGRATION_README.md
│   │   └── PLAYWRIGHT_MCP_GUIDE.md
│   └── 📁 setup/                  # 设置和安装文档
│       ├── ASYNC_CONTEXT_FIX_README.md
│       ├── DATA_RESET_GUIDE.md
│       ├── SAFE_CRAWLER_GUIDE.md
│       ├── SAFE_CRAWLER_USAGE.txt
│       └── WEB_DATA_RESET_GUIDE.md
│
├── 📁 scripts/                    # 脚本工具目录
│   ├── 📁 crawler/                # 爬虫相关脚本
│   │   └── universal_novel_downloader.py
│   ├── 📁 data/                   # 数据处理脚本
│   │   └── quick_data_reset.py
│   └── 📁 utils/                  # 工具脚本
│       ├── chapter_extractor.py
│       └── config_manager.py
│
├── 📁 legacy_pachong/             # 遗留爬虫代码 (原 pachong/)
│   └── ... (保持原有结构)
│
├── 📁 Django应用目录/
│   ├── novels/                    # 小说管理应用
│   ├── audios/                    # 音频管理应用
│   ├── generators/                # 生成器应用
│   ├── llms/                      # LLM应用
│   └── novel_audio_system/        # 主项目配置
│
└── 📁 其他/
    ├── db.sqlite3                 # 数据库文件
    ├── manage.py                  # Django管理脚本
    ├── requirements.txt           # Python依赖
    ├── templates/                 # 模板文件
    └── uploads/                   # 上传文件目录
```

## 主要变更

### 1. 文档整理 ✅
- **创建 `docs/` 目录**，按功能分类：
  - `admin/` - 管理相关文档
  - `api/` - API文档
  - `crawler/` - 爬虫文档
  - `mcp/` - MCP相关文档
  - `setup/` - 设置和安装文档

### 2. 爬虫模块重构 ✅
- **创建 `crawlers/` 目录**
- **重命名主爬虫**：`hetushu_crawler.py` → `hetushu_main.py`
- **删除旧备份目录**：`crawler_backup_20250825_151253/`
- **更新API引用路径**：所有API调用已更新到新路径

### 3. 配置文件集中 ✅
- **创建 `config/` 目录**
- 移动所有配置文件到统一位置

### 4. 脚本工具分类 ✅
- **创建 `scripts/` 目录**，按功能分类：
  - `crawler/` - 爬虫相关脚本
  - `data/` - 数据处理脚本
  - `utils/` - 工具脚本

### 5. 遗留代码标记 ✅
- **重命名 `pachong/` → `legacy_pachong/`**
- 明确标记为遗留代码，便于后续清理

### 6. 删除的文件 🗑️
- 所有 `test_*.py` 测试文件
- 重复的爬虫文件
- MCP/Playwright演示文件
- 快速修复脚本
- 数据修复脚本
- 临时和演示文件

## 代码更新

### API视图更新
文件：`backend/novels/api_views.py`

```python
# 更新前
crawler_path = os.path.join(os.path.dirname(__file__), '..', 'crawler_backup_20250825_151253')
from hetushu_crawler import HetushuCrawler

# 更新后 (统一爬虫)
crawler_path = os.path.join(os.path.dirname(__file__), '..', 'crawlers')
from unified_crawler import HetushuCrawler
```

### 爬虫模块统一整合 🕷️
- **合并多个爬虫文件**为单一的 `unified_crawler.py`
- **整合功能**：和图书网爬虫 + 智能批量爬虫 + LLM分析器
- **保持兼容性**：原有API调用方式不变
- **详细文档**：`backend/docs/CRAWLER_UNIFICATION.md`

## 使用指南

### 1. 爬虫开发
- 统一爬虫文件：`backend/crawlers/unified_crawler.py`
- 爬虫配置：`backend/crawlers/downloader_config.json`
- 参考文档：`backend/docs/crawler/` 和 `backend/docs/CRAWLER_UNIFICATION.md`

### 2. 配置管理
- 系统配置：`backend/config/admin_credentials.txt`
- 爬虫配置：`backend/crawlers/downloader_config.json`

### 3. 文档查阅
- 按功能在 `backend/docs/` 对应子目录查找
- API文档：`backend/docs/api/`
- 爬虫文档：`backend/docs/crawler/`

### 4. 脚本使用
- 数据重置：`backend/scripts/data/quick_data_reset.py`
- 工具脚本：`backend/scripts/utils/`

## 注意事项

1. **路径更新**：如果有其他地方引用了旧的爬虫路径，需要手动更新
2. **遗留代码**：`legacy_pachong/` 目录可以在确认不需要后删除
3. **文档维护**：新功能的文档应放在对应的 `docs/` 子目录中
4. **配置安全**：`config/` 目录中的敏感信息应加入 `.gitignore`

## 后续建议

1. **添加 `.gitignore` 规则**：
   ```
   backend/config/admin_credentials.txt
   backend/legacy_pachong/
   ```

2. **创建配置模板**：
   - 为敏感配置文件创建 `.example` 模板
   - 在文档中说明配置方法

3. **定期清理**：
   - 定期检查 `legacy_pachong/` 是否还需要
   - 清理不再使用的文档和脚本

---

**整理完成时间**：$(date)  
**整理人员**：AI Assistant  
**版本**：v1.0
