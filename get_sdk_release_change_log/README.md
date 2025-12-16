# GitHub 智能体框架 Release 爬虫与总结

## 功能
- 爬取指定 GitHub 仓库的 Releases 列表（含分页）
- 将每个 Release 的页面内容保存为 Markdown
- 调用 DeepSeek（OpenAI SDK）对每个页面进行智能总结

## 环境
- Python 3.11
- 使用 uv 管理虚拟环境（必须）

## 快速开始
```bash
# 使用 uv 创建并激活环境
cd get_sdk_release_change_log
uv venv
uv pip install -r requirements.txt

# 方式1：从配置文件批量处理多个仓库（推荐）
# 在 get_sdk_release_change_log 目录下运行
source .venv/Scripts/activate
uv run python -m src.main

# 方式2：处理单个仓库（向后兼容）
# 在 get_sdk_release_change_log 目录下运行
uv run python -m src.main --repo langchain-ai/langchain --max-pages 2
# 或从项目根目录运行
python run_sdk_crawler.py --repo langchain-ai/langchain --max-pages 2

# 方式3：使用 GitHub URL 格式
# 在 get_sdk_release_change_log 目录下运行
uv run python -m src.main --repo https://github.com/langchain-ai/langchain.git --max-pages 2
# 或从项目根目录运行
python run_sdk_crawler.py --repo https://github.com/langchain-ai/langchain.git --max-pages 2
```

## 配置

### 配置文件方式（批量处理）

创建 `repositories.yaml` 文件，配置要爬取的 GitHub 仓库：

```yaml
repositories:
  - url: https://github.com/langchain-ai/langchain.git
    name: LangChain
    enabled: true
    max_pages: 2
    start_page: 1
    enable_summary: true  # 可选，是否启用总结功能（默认从全局配置读取）

  - url: https://github.com/another-org/another-repo.git
    name: Another Repo
    enabled: true
    max_pages: 2
    enable_summary: false  # 示例：禁用该仓库的总结功能
```

支持的 URL 格式：
- `https://github.com/owner/repo.git`
- `https://github.com/owner/repo`
- `owner/repo`

### 环境变量配置
- 代理：根据网络环境可选设置 `HTTP_PROXY`、`HTTPS_PROXY`（不强制，默认不写入代理）
- GitHub Token：可选，通过参数 `--gh-token` 或环境变量 `GITHUB_TOKEN` 提供（提升限额）
- LLM API：可选，通过环境变量 `LLM_API_KEY` 提供；未提供时仅抓取 Markdown，跳过摘要
- 总结功能：通过环境变量 `ENABLE_SUMMARY` 控制是否启用总结功能（默认 `True`），也可在 `repositories.yaml` 中为每个仓库单独配置

## CLI 参数
- `--repo` 单个仓库名或 URL（可选），例如：`langchain-ai/langchain` 或 `https://github.com/langchain-ai/langchain.git`。如果未指定，则从配置文件读取
- `--config` 仓库配置文件路径（默认：`repositories.yaml`）
- `--max-pages` 抓取页数（默认 2，仅单仓库模式）
- `--start-page` 起始页（默认 1，仅单仓库模式）
- `--model` 大模型名称（默认 `deepseek-chat`，可设 `deepseek-reasoner`）
- `--gh-token` GitHub 访问令牌（默认从环境变量 `GITHUB_TOKEN` 读取）
- `--enable-summary` 是否启用总结功能（True/False，默认从配置文件读取）

## 输出
- Releases Markdown：`data/releases/<repo_slug>_<page>.md`
- 摘要 Markdown：`data/summaries/<repo_slug>_<page>_summary.md`（当提供 LLM 密钥时生成）

## 目录结构
```
src/
  crawler.py
  llm_client.py
  main.py
  utils.py
config.py
repositories.yaml  # 仓库配置文件
data/
  releases/
  summaries/
```

