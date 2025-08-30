# 小说爬虫系统 RESTful API 文档

## 基础信息

- **Base URL**: `http://127.0.0.1:8000/api/`
- **认证方式**: JWT Token
- **Content-Type**: `application/json`
- **分页**: 支持标准分页参数 `page` 和 `page_size`

## 认证接口

### 1. 用户登录
```
POST /api/auth/login/
```
**请求体**:
```json
{
    "username": "your_username",
    "password": "your_password"
}
```
**响应**:
```json
{
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
}
```

### 2. 刷新Token
```
POST /api/auth/refresh/
```
**请求体**:
```json
{
    "refresh": "jwt_refresh_token"
}
```

### 3. 获取用户信息
```
GET /api/auth/user/
```
**Headers**: `Authorization: Bearer {access_token}`

## 核心资源接口

### 小说管理 (Novels)

#### 1. 获取小说列表
```
GET /api/novels/
```
**查询参数**:
- `page`: 页码
- `page_size`: 每页数量
- `search`: 搜索关键词 (标题、作者、描述)
- `status`: 状态筛选
- `is_active`: 是否激活
- `ordering`: 排序字段 (`created_at`, `updated_at`, `title`)

#### 2. 创建小说
```
POST /api/novels/
```
**请求体**:
```json
{
    "title": "小说标题",
    "author": "作者名",
    "description": "小说描述",
    "status": "ongoing",
    "is_active": true
}
```

#### 3. 获取单个小说
```
GET /api/novels/{id}/
```

#### 4. 更新小说
```
PUT /api/novels/{id}/
PATCH /api/novels/{id}/
```

#### 5. 删除小说
```
DELETE /api/novels/{id}/
```

#### 6. 获取小说章节
```
GET /api/novels/{id}/chapters/
```

#### 7. 批量导入章节
```
POST /api/novels/{id}/batch_import/
```
**请求体**:
```json
{
    "source_id": 1,
    "max_chapters": 100
}
```

### 章节管理 (Chapters)

#### 1. 获取章节列表
```
GET /api/chapters/
```
**查询参数**:
- `novel`: 小说ID筛选
- `search`: 搜索章节标题或内容
- `ordering`: 排序字段

#### 2. 创建章节
```
POST /api/chapters/
```
**请求体**:
```json
{
    "novel": 1,
    "title": "章节标题",
    "content": "章节内容",
    "chapter_number": 1,
    "chapter_sort_number": 1
}
```

#### 3. 获取单个章节
```
GET /api/chapters/{id}/
```

#### 4. 获取章节内容
```
GET /api/chapters/{id}/content/
```

#### 5. 按小说获取章节
```
GET /api/chapters/by_novel/?novel_id={novel_id}
```

### 小说来源管理 (Novel Sources)

#### 1. 获取来源列表
```
GET /api/novel-sources/
```
**查询参数**:
- `source_type`: 来源类型筛选
- `is_active`: 是否激活
- `search`: 搜索名称或URL

#### 2. 创建来源
```
POST /api/novel-sources/
```
**请求体**:
```json
{
    "name": "来源名称",
    "base_url": "https://example.com",
    "source_type": "website",
    "is_active": true,
    "priority": 1
}
```

## 爬虫功能接口 (Novel Source Relations)

### 1. 获取小说来源关系列表
```
GET /api/novel-source-relations/
```
**查询参数**:
- `novel`: 小说ID筛选
- `source`: 来源ID筛选
- `is_primary`: 是否主要来源
- `search`: 搜索小说标题、来源名称或URL
- `ordering`: 排序字段 (`created_at`, `last_sync_at`)

### 2. 创建小说来源关系
```
POST /api/novel-source-relations/
```
**请求体**:
```json
{
    "novel": 1,
    "source": 1,
    "source_url": "https://example.com/novel/123",
    "is_primary": true
}
```

### 3. 基础爬取
```
POST /api/novel-source-relations/{id}/crawl_basic/
```
**功能**: 自动检测网站类型并使用相应爬虫进行基础爬取
**响应**:
```json
{
    "success": true,
    "message": "成功爬取 10 个新章节",
    "total_chapters": 50,
    "crawler_type": "hetushu"
}
```

### 4. 高级爬取
```
POST /api/novel-source-relations/{id}/crawl_advanced/
```
**请求体**:
```json
{
    "max_chapters": 100,
    "start_chapter": 1,
    "overwrite_existing": false,
    "delay_between_requests": 1.0,
    "retry_count": 3
}
```
**响应**:
```json
{
    "success": true,
    "message": "高级爬取完成",
    "stats": {
        "total_processed": 50,
        "saved_chapters": 30,
        "updated_chapters": 10,
        "skipped_chapters": 10,
        "crawler_type": "universal"
    }
}
```

### 5. 获取爬取状态
```
GET /api/novel-source-relations/crawl_status/
```
**响应**:
```json
{
    "total_relations": 25,
    "active_relations": 20,
    "recent_synced": 5,
    "supported_sites": ["hetushu.com", "biquge.com", "其他通用站点"]
}
```

### 6. 智能批量导入
```
POST /api/novel-source-relations/simple_batch_import/
```
**请求体**:
```json
{
    "source_url": "https://example.com/novel/123",
    "novel_title": "小说标题",
    "novel_author": "作者名",
    "source_id": 1
}
```

## HTTP状态码说明

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `204 No Content`: 删除成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或Token无效
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

## 错误响应格式

```json
{
    "success": false,
    "message": "错误描述",
    "errors": {
        "field_name": ["具体错误信息"]
    }
}
```

## 分页响应格式

```json
{
    "count": 100,
    "next": "http://127.0.0.1:8000/api/novels/?page=3",
    "previous": "http://127.0.0.1:8000/api/novels/?page=1",
    "results": [
        // 数据列表
    ]
}
```

## 使用建议

### 前端对接建议

1. **认证流程**:
   - 用户登录获取access_token
   - 在所有API请求头中添加: `Authorization: Bearer {access_token}`
   - Token过期时使用refresh_token刷新

2. **错误处理**:
   - 统一处理HTTP状态码
   - 401状态码时重新登录
   - 显示友好的错误信息给用户

3. **爬虫功能使用**:
   - 先创建小说和来源关系
   - 使用基础爬取进行快速测试
   - 使用高级爬取进行精细控制
   - 定期检查爬取状态

4. **性能优化**:
   - 使用分页避免一次加载过多数据
   - 合理使用搜索和筛选参数
   - 缓存不经常变化的数据

### API组织方式

**推荐由后端(我)来组织API结构**，原因:
1. 确保RESTful规范的一致性
2. 统一的错误处理和响应格式
3. 更好的安全性和权限控制
4. 便于API版本管理和文档维护

前端只需要按照此文档进行对接即可。如有特殊需求，可以讨论后由后端进行相应调整。