# 博客爬虫工程

从 AI 相关公司/产品的官方博客抓取文章并保存为 Markdown 格式。

## 功能特性

- 支持 RSS/Atom feed 和 HTML 页面两种抓取模式
- **支持单 URL 抓取**：无需配置即可抓取任意网页
- 自动将 HTML 内容转换为 Markdown 格式
- 按日期和来源组织文件结构
- 支持多博客源配置（YAML 配置文件）
- 遵守 robots.txt 和礼貌爬取规范
- URL hash 去重，支持幂等运行
- 支持翻页（next、param、page_links 三种模式）
- 智能内容提取：自动识别标题、正文、日期、作者等信息

## 安装

```bash
# 使用 uv 安装依赖
cd get_blog_posts
uv pip install -r requirements.txt
```

## 配置

编辑 `configs/blogs.yaml` 文件，添加要抓取的博客源：

```yaml
blogs:
  - name: langchain
    url: https://blog.langchain.com/
    type: html
    rss_url: https://blog.langchain.com/feed/  # 可选
    selectors:
      list_item: article
      title: h2 a
      link: h2 a
      date: time
    pagination:
      type: next
      next_selector: a[rel="next"]
      max_pages: 10
    content_selectors:
      title: h1
      content: article
      author: .author
      date: time
    delay: 1.0
    timeout: 30
    tags: [ai, langchain, agents]
```

### 配置说明

- **name**: 博客源名称（用于目录组织）
- **url**: 博客首页 URL
- **type**: 爬取类型（`html` 或 `rss`）
- **rss_url**: RSS feed URL（可选，如果配置了会优先使用）
- **selectors**: HTML 列表页选择器配置
  - `list_item`: 文章项选择器
  - `title`: 标题选择器
  - `link`: 链接选择器
  - `date`: 日期选择器（可选）
  - `author`: 作者选择器（可选）
- **pagination**: 翻页配置
  - `type`: 翻页类型（`next`、`param`、`page_links`）
  - `next_selector`: 下一页链接选择器（type=next 时使用）
  - `param_name`: 查询参数名（type=param 时使用，默认 "page"）
  - `start`: 起始页码（type=param 时使用，默认 1）
  - `step`: 步长（type=param 时使用，默认 1）
  - `max_pages`: 最大页数
- **content_selectors**: 详情页内容选择器
  - `title`: 标题选择器
  - `content`: 正文内容选择器
  - `author`: 作者选择器（可选）
  - `date`: 日期选择器（可选）
- **delay**: 请求延迟（秒，默认 1.0）
- **timeout**: 请求超时（秒，默认 30）
- **tags**: 标签列表

## 使用方法

### 基本使用

```bash
# 从项目根目录运行
uv run python -m get_blog_posts.src.main

# 或从 get_blog_posts 目录运行
cd get_blog_posts
python -m src.main
```

### 命令行参数

#### 配置文件模式参数

- `--config PATH`: 配置文件路径（默认: `configs/blogs.yaml`）
- `--output-dir PATH`: 输出目录（默认: `data/exports`）
- `--source NAME`: 指定单个博客源名称
- `--max-pages N`: 覆盖配置中的 max_pages
- `--delay SECONDS`: 覆盖配置中的 delay（秒）
- `--overwrite`: 覆盖已存在的文章
- `--log-level LEVEL`: 日志级别（DEBUG、INFO、WARNING、ERROR，默认 INFO）

#### 单 URL 抓取参数

- `--url URL`: 抓取单个 URL（直接指定要抓取的网页 URL）
- `--url-source NAME`: 指定来源名称（默认从 URL 提取域名）
- `--url-tags TAG1 TAG2 ...`: 指定标签列表（默认从 URL 提取域名）

### 示例

#### 配置文件模式

```bash
# 抓取所有配置的博客源
uv run python -m get_blog_posts.src.main

# 只抓取 LangChain 博客
uv run python -m get_blog_posts.src.main --source langchain

# 覆盖已存在的文章
uv run python -m get_blog_posts.src.main --overwrite

# 设置最大页数为 5
uv run python -m get_blog_posts.src.main --max-pages 5

# 设置请求延迟为 2 秒
uv run python -m get_blog_posts.src.main --delay 2.0
```

#### 单 URL 抓取模式

```bash
# 抓取单个 URL（自动提取域名作为来源和标签）
uv run python -m get_blog_posts.src.main --url "https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills"

# 指定来源名称
uv run python -m get_blog_posts.src.main --url "https://example.com/article" --url-source "example"

# 指定标签
uv run python -m get_blog_posts.src.main --url "https://example.com/article" --url-tags ai engineering agents

# 覆盖已存在的文章
uv run python -m get_blog_posts.src.main --url "https://example.com/article" --overwrite
```

## 输出格式

文章保存在 `data/exports/<timestamp>/markdown/<source>/<YYYY>/<MM>/<DD>/<slug>.md` 目录下。

每个 Markdown 文件包含：
- 文章标题
- 元数据（来源、URL、发布时间、作者、标签、抓取时间）
- 摘要（如果有）
- 正文内容（Markdown 格式）

## 注意事项

1. **礼貌爬取**: 程序会自动检查 robots.txt 并遵守规则，默认请求延迟为 1 秒
2. **幂等性**: 默认不会重复抓取已存在的文章（基于 URL hash），使用 `--overwrite` 可覆盖
3. **错误处理**: 单个博客源失败不会影响其他源的抓取
4. **网络要求**: 需要能够访问目标博客网站
5. **JavaScript 渲染**: 当前版本仅支持静态 HTML 页面，不支持 JavaScript 动态加载的内容（如 OpenAI 的新闻页面）
6. **分页限制**: 某些网站（如 Anthropic）使用 JavaScript 加载更多内容，只能抓取首页显示的文章
7. **文件组织**: 不同来源的文章会自动保存在不同的文件夹中（`markdown/<source>/<YYYY>/<MM>/<DD>/`）

## 故障排除

### 抓取失败

- 检查网络连接
- 检查目标网站是否可访问
- 检查选择器是否正确（可能需要根据网站结构调整）
- 查看日志文件 `logs/app.log`

### 内容为空

- 检查 `content_selectors` 配置是否正确
- 某些网站可能需要 JavaScript 渲染，本工具仅支持静态 HTML

### 翻页失败

- 检查 `pagination` 配置是否正确
- 尝试不同的翻页类型（next、param、page_links）

