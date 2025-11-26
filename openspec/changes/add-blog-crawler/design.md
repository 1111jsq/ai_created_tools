## Context
需要创建一个新的博客爬虫工程，用于从 AI 相关公司/产品的官方博客抓取文章。参考现有 `get_agent_news` 和 `get_sdk_release_change_log` 的架构模式，保持项目一致性和可维护性。

## Goals / Non-Goals
- Goals
  - 支持从多个博客网站抓取文章（列表页 + 详情页）
  - 将文章内容转换为 Markdown 格式并保存到本地
  - 支持配置驱动的多源管理（YAML 配置）
  - 遵循项目统一的代码规范和架构模式
  - 遵守礼貌爬取规范（robots.txt、延迟、超时）
- Non-Goals
  - 不实现复杂的反爬虫绕过机制
  - 不实现实时监控和增量更新（单次运行模式）
  - 不实现文章内容的 LLM 分析（仅抓取和保存）

## Decisions
- 工程结构：参考 `get_agent_news` 的结构，包含 `src/`、`data/`、`configs/` 目录
- 数据模型：定义 `BlogPost` 模型，包含标题、URL、发布时间、作者、正文内容、标签等字段
- 存储格式：Markdown 文件，按日期和来源组织目录结构（`data/exports/<timestamp>/markdown/<source>/<YYYY>/<MM>/<DD>/<slug>.md`）
- 配置管理：使用 YAML 配置文件定义博客源（URL、选择器、翻页规则等）
- 爬取策略：优先使用 RSS/Atom feed（如果可用），否则使用 HTML 解析
- 内容提取：使用 BeautifulSoup 解析 HTML，使用 `markdownify` 或 `html2text` 转换为 Markdown
- 幂等性：支持重复运行，已存在的文章不重复抓取（基于 URL hash）

## 架构设计

### 目录结构
```
get_blog_posts/
├── README.md
├── requirements.txt
├── config.py                    # 配置加载（使用 common/config_loader.py）
├── configs/
│   └── blogs.yaml               # 博客源配置
├── src/
│   ├── __init__.py
│   ├── main.py                  # CLI 入口
│   ├── models.py                # BlogPost 数据模型
│   ├── crawler.py               # 核心爬虫逻辑
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── rss_parser.py        # RSS/Atom feed 解析
│   │   ├── html_parser.py       # HTML 页面解析
│   │   └── markdown_converter.py # HTML 转 Markdown
│   └── storage/
│       ├── __init__.py
│       └── file_storage.py      # 文件存储管理
└── data/
    └── exports/                 # 导出目录
```

### 数据模型
```python
@dataclass
class BlogPost:
    source: str                  # 博客源名称（如 "langchain"）
    title: str
    url: str
    published_at: Optional[datetime]
    author: Optional[str]
    content: str                 # Markdown 格式的正文
    summary: Optional[str]      # 摘要（如果有）
    tags: List[str]
    fetched_at: datetime
    url_hash: str                # URL 的 SHA256 hash
```

### 配置格式（blogs.yaml）
```yaml
blogs:
  - name: langchain
    url: https://blog.langchain.com/
    type: html                   # html | rss
    rss_url: https://blog.langchain.com/feed/  # 可选
    selectors:
      list_item: article.post-item  # 列表页文章项选择器
      title: h2 a
      link: h2 a
      date: time.published
      author: .author
    pagination:
      type: next                 # next | param | page_links
      next_selector: .next-page
      max_pages: 10
    content_selectors:          # 详情页选择器
      title: h1.post-title
      content: .post-content
      author: .post-author
      date: time.published
    delay: 1.0                   # 请求延迟（秒）
    timeout: 30                  # 超时（秒）
    tags: [ai, langchain, agents]
```

### 爬取流程
1. 加载配置文件 `configs/blogs.yaml`
2. 对每个博客源：
   - 检查 robots.txt（如果存在）
   - 如果配置了 RSS URL，优先使用 RSS 解析
   - 否则使用 HTML 解析：
     a. 抓取列表页（支持翻页）
     b. 提取文章链接
     c. 抓取每篇文章详情页
     d. 提取标题、正文、作者、发布时间等
   - 将 HTML 内容转换为 Markdown
   - 保存到文件系统
3. 生成导出统计和 README

### 内容转换策略
- 使用 `html2text` 或 `markdownify` 库将 HTML 转换为 Markdown
- 清理多余的空白和格式
- 保留代码块、链接、图片等关键元素
- 处理相对链接，转换为绝对链接

## CLI 设计
- 命令：`uv run python -m get_blog_posts.src.main`
- 参数：
  - `--config PATH`（默认 `configs/blogs.yaml`）
  - `--output-dir PATH`（默认 `data/exports`）
  - `--source NAME`（可选，指定单个博客源）
  - `--max-pages N`（可选，覆盖配置中的 max_pages）
  - `--delay SECONDS`（可选，覆盖配置中的 delay）
  - `--overwrite`（默认否，是否覆盖已存在的文章）
  - `--log-level INFO|DEBUG`

## 错误处理与容错
- 网络错误：重试机制（最多 3 次），记录失败 URL
- 解析错误：跳过该文章，记录警告日志
- 配置错误：验证配置格式，提供清晰的错误信息
- robots.txt 禁止：跳过该博客源，记录警告
- 幂等性：基于 URL hash 判断是否已抓取，默认不覆盖

## Risks / Trade-offs
- 风险：不同博客网站结构差异大，需要为每个源定制选择器 → 通过配置文件灵活支持
- 风险：反爬虫机制可能限制抓取 → 遵守 robots.txt 和礼貌爬取规范，设置合理的延迟
- 取舍：不实现复杂的 JavaScript 渲染（仅抓取静态 HTML）→ 大多数博客支持 RSS 或静态 HTML
- 取舍：不实现增量更新机制 → 单次运行模式，通过 URL hash 避免重复抓取

## Migration Plan
新增独立工程，不涉及现有代码迁移。与现有工程保持松耦合，共享 `common/` 模块的配置和 LLM 客户端。

## Open Questions
- 是否需要支持需要登录的博客（如 Medium）？
- 是否需要实现文章内容的 LLM 摘要功能（可选）？
- 是否需要支持导出为 JSON/CSV 格式（类似 get_agent_news）？

