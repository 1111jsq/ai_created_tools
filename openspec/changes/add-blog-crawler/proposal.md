# Change: 新增博客爬虫工程

## Why
当前项目已有论文、新闻、SDK Release 爬虫，但缺少对 AI 相关公司/产品官方博客的专门爬取工具。博客文章通常包含产品更新、技术深度解析、案例研究等重要信息，是了解行业动态的重要来源。需要创建一个独立的博客爬虫工程，支持从多个博客网站（如 LangChain、OpenAI 等）抓取文章并保存为 Markdown 格式。

## What Changes
- 新增 `get_blog_posts` 工程，独立于现有爬虫工具
- 支持从博客网站抓取文章列表和详情内容
- 支持多种博客平台（WordPress、Ghost、自定义博客等）
- 将抓取的文章保存为 Markdown 格式，按日期和来源组织
- 支持配置多个博客源（通过 YAML 配置文件）
- 遵循项目统一的配置管理和 LLM 客户端模式
- 遵守 robots.txt 和礼貌爬取规范（延迟、超时、User-Agent）

## Impact
- Affected specs: `specs/blog-crawler/spec.md`（新增）
- Affected code: 新增 `get_blog_posts/` 目录及其子模块
- 不影响现有工程：与 `get_paper`、`get_agent_news`、`get_sdk_release_change_log` 独立运行

