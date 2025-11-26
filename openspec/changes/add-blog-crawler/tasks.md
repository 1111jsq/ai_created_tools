## 1. Implementation
- [x] 1.1 创建工程目录结构：`get_blog_posts/` 及其子目录
- [x] 1.2 创建 `BlogPost` 数据模型（`src/models.py`）
- [x] 1.3 实现 RSS/Atom feed 解析器（`src/parsers/rss_parser.py`）
- [x] 1.4 实现 HTML 列表页和详情页解析器（`src/parsers/html_parser.py`）
- [x] 1.5 实现 HTML 转 Markdown 转换器（`src/parsers/markdown_converter.py`）
- [x] 1.6 实现核心爬虫逻辑（`src/crawler.py`），支持 RSS 和 HTML 两种模式
- [x] 1.7 实现文件存储管理（`src/storage/file_storage.py`），按日期和来源组织目录
- [x] 1.8 实现 CLI 入口（`src/main.py`），支持命令行参数
- [x] 1.9 创建配置文件模板（`configs/blogs.yaml`），包含 LangChain 等示例配置
- [x] 1.10 实现 robots.txt 检查功能（遵守礼貌爬取规范）
- [x] 1.11 实现 URL hash 去重机制（幂等性支持）
- [x] 1.12 创建 `requirements.txt`，添加必要依赖（httpx、beautifulsoup4、html2text/markdownify、feedparser、pyyaml）
- [x] 1.13 创建 `config.py`，使用 `common/config_loader.py` 加载配置

## 2. Validation
- [ ] 2.1 测试 RSS feed 解析（使用 LangChain 博客的 RSS feed）
- [ ] 2.2 测试 HTML 列表页解析和翻页功能
- [ ] 2.3 测试详情页内容提取和 Markdown 转换
- [ ] 2.4 测试文件存储和目录组织（按日期和来源）
- [ ] 2.5 测试 URL hash 去重（重复运行不重复抓取）
- [ ] 2.6 测试 robots.txt 检查功能
- [ ] 2.7 测试错误处理（网络错误、解析错误、配置错误）
- [ ] 2.8 验证生成的 Markdown 文件格式正确、内容完整

## 3. Documentation
- [x] 3.1 创建 `get_blog_posts/README.md`，包含使用说明、配置示例、命令行参数说明
- [x] 3.2 在根 `README.md` 中添加 `get_blog_posts` 工程说明
- [x] 3.3 在 `configs/blogs.yaml` 中添加注释，说明各配置项含义

