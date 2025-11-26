# ai_created_tools
一些有用的工具

## 配置说明

本项目使用统一的 `.env` 文件管理所有子工程的配置信息。

**首次使用前，请先配置环境变量：**

```bash
# 1. 复制配置模板
cp .env.example .env

# 2. 编辑 .env 文件，填写你的 API 密钥等配置
# 特别是：LLM_API_KEY、GITHUB_TOKEN 等
```

详细配置说明请参考：[CONFIG.md](CONFIG.md)

## 报告编排 CLI（每周/区间智能体深度报告）

将论文（get_paper）、新闻（get_agent_news）、SDK Releases（get_sdk_release_change_log）的既有产出在固定时间段内聚合为中文 Markdown 报告（含 Mermaid 图表，LLM 可选）。

- 使用手册：`report/README.md`
- 快速开始（最近 7 天）：
  ```bash
  uv run python -m report.main
  ```
- 指定区间：
  ```bash
  uv run python -m report.main --start 2025-11-01 --end 2025-11-07
  ```
- 仅汇总指定仓库并覆盖报告：
  ```bash
  uv run python -m report.main --repos langchain-ai/langchain,openai/openai-python --overwrite
  ```

## 博客爬虫

从 AI 相关公司/产品的官方博客抓取文章并保存为 Markdown 格式。

- 使用手册：`get_blog_posts/README.md`
- 快速开始：
  ```bash
  uv run python -m get_blog_posts.src.main
  ```
- 指定博客源：
  ```bash
  uv run python -m get_blog_posts.src.main --source langchain
  ```
- 覆盖已存在文章：
  ```bash
  uv run python -m get_blog_posts.src.main --overwrite
  ```

## SVG 图片生成器

根据任务描述调用大模型生成 SVG 图片的工具。

- 使用手册：`svg_generator/README.md`
- 快速开始：
  ```bash
  uv run python -m svg_generator.main "创建一个简单的流程图，包含开始、处理、结束三个节点"
  ```
- 指定输出路径：
  ```bash
  uv run python -m svg_generator.main "画一个架构图" --output diagrams/architecture.svg
  ```
