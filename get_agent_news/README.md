# get_agent_news

每周自动获取 AI Agent / 大模型相关资讯，支持 AIbase 日报与资讯抓取，输出 Markdown 与目录页。

## 运行环境

- Python 3.11（仅使用 uv 管理环境）

```bash
uv sync
```

## 快速开始

```bash
# 同时抓取日报与资讯，生成 Markdown 与目录页
uv run python -m src.main --once --source all --news-since-days 7 --export-markdown --stop-on-duplicate-daily
```

更多示例见：`specs/001-aibase-md-export/quickstart.md`

## 重要说明

- 本项目不再依赖或备份任何数据库文件，所有产出为文件系统导出（CSV、JSONL、Markdown 与目录页）。
- 不再内置定时任务调度，请使用系统级调度器或 CI 定时触发上述命令。
- 若需启用 LLM 排序，请提供环境变量 `DEEPSEEK_API_KEY`；未提供时将自动使用启发式排序。

## 内容目录结构

```text
content/
├─ daily/                 # 日报（一个日期一个 Markdown 文件）
│  ├─ YYYY-MM-DD.md
│  └─ ...
├─ news/                  # 资讯（按日期分目录）
│  ├─ YYYY-MM-DD/
│  │  ├─ <slug>-<hash8>.md
│  │  └─ ...
│  └─ ...
└─ index.md               # 目录页（包含本次新增摘要与全量索引）
```

## 合规与礼貌抓取

- 自定义 User-Agent、超时、重试与主机级速率限制；
- 遵守 robots.txt 与站点条款，被禁止的路径将记录日志并跳过。


