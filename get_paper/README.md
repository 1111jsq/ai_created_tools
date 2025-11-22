# AI Agent Papers ETL

最小月度/区间 ETL：抓取（arXiv、OpenReview）、解析/规范化、去重、质量筛选、分类与摘要、下载 PDF、导出 JSON/CSV/MD，并结合 LLM 分析与排名。

## 快速开始

1) 安装依赖
```bash
pip install -r requirements.txt
```

可选：推荐使用 uv 管理虚拟环境（更快、更干净）
```bash
pip install uv
uv venv
source .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

2) 运行（按区间）
```bash
# Windows CMD 示例（可在源码中已默认设置时间窗口）
set OPENREVIEW_ENABLED=1
set OPENREVIEW_VENUE_ID=ICLR.cc/2025/Conference
set OPENREVIEW_STATUS=accepted
python -m src.monthly_run
```

也可通过 CLI 参数指定时间窗口：
```bash
# 指定按月
python -m src.monthly_run --month 2025-11

# 指定起止日期
python -m src.monthly_run --start 2025-11-01 --end 2025-11-16
```

产物输出在 `get_paper/data/`（已统一，无论从哪里运行均输出到该处）：
- `raw/` 原始抓取（含 `openreview/` 与 `arxiv/`）
- `exports/` JSON/CSV/Markdown、排名与统计

## 综述抓取（2020+，按年存放）
新增独立入口，用于自 2020 年起抓取与「LLM/Agent」相关的综述类文章（`survey`/`review`），结果按年写入 `src/data/raw/arxiv_surveys/<year>/arxiv-<year>-surveys.json`：

```bash
# 默认从 2020 年抓到当前年
python -m src.run_arxiv_surveys

# 自定义起止年份与输出目录
python -m src.run_arxiv_surveys --start-year 2021 --end-year 2024 --output-base src/data/raw/arxiv_surveys
```

## OpenReview（API v2）说明
- 推荐使用官方客户端（`openreview-py`，已在 `requirements.txt` 中列出）
- 必需：`OPENREVIEW_ENABLED=1` 与 `OPENREVIEW_VENUE_ID`（如 `ICLR.cc/2025/Conference`）
- 仅发表/接收稿：`OPENREVIEW_STATUS=accepted`（别名：`published`/`final`）
- 未提供 `OPENREVIEW_VENUE_ID` 时，程序会在日志中列出近期候选，便于选择

## LLM 配置（与 PPT 一致）
- 环境变量：
  - `LLM_API_KEY`：大模型 API Key（如 DeepSeek）
  - `LLM_BASE_URL`：可选，兼容自定义网关/DeepSeek 网关
  - `LLM_MODEL`：默认 `deepseek-chat`
  - `LLM_TIMEOUT`：可选，请求超时（秒）
- 未设置 `LLM_API_KEY` 时，大模型分析将自动跳过，其他流程仍正常产出。

## 其他
- 若需要修改时间窗口，可编辑 `src/monthly_run.py` 或通过 CLI 参数传入


