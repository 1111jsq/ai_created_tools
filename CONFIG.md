# 统一配置说明

本项目使用统一的 `.env` 文件管理所有子工程的配置信息。

## 快速开始

1. **复制配置模板**
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件**
   根据你的实际情况填写配置值，特别是 API 密钥等敏感信息。

3. **配置说明**
   - 所有配置项都有默认值，可以根据需要覆盖
   - 敏感信息（如 API 密钥）请勿提交到版本控制系统
   - `.env` 文件已在 `.gitignore` 中，不会被提交

## 配置项说明

### LLM 配置

```env
# LLM API Key
LLM_API_KEY=your_api_key_here

# LLM 基础 URL（默认 DeepSeek）
LLM_BASE_URL=https://api.deepseek.com

# LLM 模型名称
LLM_MODEL=deepseek-chat

# LLM 超时时间（秒）
LLM_TIMEOUT=60
```

### GitHub API 配置

```env
GITHUB_TOKEN=your_github_token_here
GITHUB_API_BASE=https://api.github.com
GITHUB_PER_PAGE=100
GITHUB_MAX_PAGES=10
```

### 代理配置（可选）

```env
HTTP_PROXY=
HTTPS_PROXY=
```

### 爬虫配置

```env
CRAWLER_REQUEST_DELAY=1.0
CRAWLER_TIMEOUT=30
CRAWLER_RETRY_TIMES=3
```

### LLM 处理配置

```env
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.7
LLM_CHUNK_CHARS=12000
LLM_CHUNK_OVERLAP=500
LLM_VERSIONS_PER_CHUNK=20
LLM_PRE_FILTER=false
```

### 项目路径配置（可选，通常使用默认值）

```env
SRC_DIR=src
DATA_DIR=data
RELEASES_DIR=data/releases
SUMMARIES_DIR=data/summaries
NEWS_SOURCES_PATH=get_agent_news/configs/sources.yaml
NEWS_LOG_PATH=get_agent_news/logs/app.log
FILE_ENCODING=utf-8
```

### 其他配置

```env
REPOSITORIES_CONFIG_FILE=repositories.yaml
LOG_LEVEL=INFO
```

## 子工程配置

所有子工程都会自动从项目根目录的 `.env` 文件读取配置：

- `get_sdk_release_change_log`: GitHub Releases 爬虫
- `get_agent_news`: 新闻爬虫
- `get_paper`: 论文爬虫
- `report`: 报告生成
- `common`: 公共模块（LLM 客户端等）

## 技术实现

- 使用 `python-dotenv` 库加载 `.env` 文件
- 统一的配置加载器：`common/config_loader.py`
- 自动查找项目根目录的 `.env` 文件
- 支持类型转换（str, int, float, bool）
- 向后兼容：如果 `.env` 文件不存在，会使用默认值

## 注意事项

1. **不要提交 `.env` 文件**：`.env` 文件包含敏感信息，已在 `.gitignore` 中
2. **使用 `.env.example` 作为模板**：团队成员可以基于此文件创建自己的 `.env`
3. **环境变量优先级**：如果同时设置了环境变量和 `.env` 文件，环境变量优先（`load_dotenv(override=False)`）
4. **路径配置**：所有路径配置都是相对于项目根目录的

