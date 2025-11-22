# ai_created_tools
一些有用的工具

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
