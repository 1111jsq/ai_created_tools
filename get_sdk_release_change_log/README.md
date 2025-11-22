# GitHub 智能体框架 Release 爬虫与总结

## 功能
- 爬取指定 GitHub 仓库的 Releases 列表（含分页）
- 将每个 Release 的页面内容保存为 Markdown
- 调用 DeepSeek（OpenAI SDK）对每个页面进行智能总结

## 环境
- Python 3.10
- 使用 uv 管理虚拟环境（必须）

## 快速开始
```bash
# 使用 uv 创建并激活环境
uv venv
uv pip install -r requirements.txt

# 运行
uv run python -m src.main --repo openai/openai-python --max-pages 2
```

## 配置
- 代理：根据网络环境可选设置 `HTTP_PROXY`、`HTTPS_PROXY`（不强制，默认不写入代理）
- GitHub Token：可选，通过参数 `--gh-token` 或环境变量 `GITHUB_TOKEN` 提供（提升限额）
- DeepSeek API：可选，通过环境变量 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY` 提供；未提供时仅抓取 Markdown，跳过摘要

## CLI 参数
- `--repo` 仓库名（必填），例如：`langchain-ai/langchain`
- `--max-pages` 抓取页数（默认 2）
- `--start-page` 起始页（默认 1）
- `--model` 大模型名称（默认 `deepseek-chat`，可设 `deepseek-reasoner`）
- `--gh-token` GitHub 访问令牌（默认从环境变量 `GITHUB_TOKEN` 读取）

## 输出
- Releases Markdown：`data/releases/<repo_slug>_<page>.md`
- 摘要 Markdown：`data/summaries/<repo_slug>_<page>_summary.md`（当提供 LLM 密钥时生成）

## 目录结构
```
src/
  crawler.py
  llm_client.py
  main.py
config.py
data/
  releases/
  summaries/
```

