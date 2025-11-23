# 每周/区间 智能体深度分析报告（编排 CLI）使用手册

本工具将三个子工程的既有产出按固定时间段（默认 7 天）进行只读聚合，生成中文 Markdown 深度报告，并内嵌 Mermaid 图表（遵循“图内文本不含括号类符号”的渲染约束）。

## 一、前置条件

- 已安装 Python 与 `uv`（建议使用 `uv` 运行）
- 三个子工程至少有其一已产出数据（否则报告仍会生成，但会标注“数据缺失”）：
  - 论文（get_paper）：`get_paper/data/exports/<YYYYMMDD-YYYYMMDD>/`
    - 示例：`<label>-stats.json`、`<label>-ranked-all.json`、`<label>-comprehensive-report.md`
  - 新闻（get_agent_news）：`get_agent_news/data/exports/<YYYYMMDD_HHMMSS>/`
    - 示例：`news.jsonl`、`news.csv`、`markdown/`
  - SDK Releases（get_sdk_release_change_log）：
    - Releases：`get_sdk_release_change_log/data/releases/<repo_slug>_<page>.md`
    - 摘要（可选）：`get_sdk_release_change_log/data/summaries/<repo_slug>_<page>_summary.md`

## 二、快速开始

默认会先执行三子工程生成数据，再聚合最近 7 天（含当天），输出到 `reports/<执行时间前缀>-<YYYYMMDD-YYYYMMDD>/weekly-intel-report.md`：

```bash
uv run python -m report.main
```

指定时间区间：

```bash
uv run python -m report.main --start 2025-11-01 --end 2025-11-07
```

仅汇总指定 SDK 仓库，且允许覆盖已存在报告：

```bash
uv run python -m report.main --repos langchain-ai/langchain,openai/openai-python --overwrite
```

仅聚合（不执行三子工程）：

```bash
uv run python -m report.main --no-run-sources
```

启用 LLM 深度洞察（可选）：

```bash
# Windows: set LLM_API_KEY=your_key
# PowerShell: $Env:LLM_API_KEY="your_key"
export LLM_API_KEY=your_key
uv run python -m report.main
```

启用图片生成功能（可选）：

```bash
# 需要配置 LLM_API_KEY
export LLM_API_KEY=your_key
uv run python -m report.main --enable-image-generation
```

图片生成功能会使用大模型分析报告内容，自动识别适合生成图片的部分（如趋势图表、架构图、数据可视化等），并使用 `svg_generator` 模块生成 SVG 图片嵌入到报告中。

## 三、命令行参数

- `--start YYYY-MM-DD` 与 `--end YYYY-MM-DD`：区间起止日期（与 `--last-days` 互斥）
- `--last-days N`：最近 N 天，默认 7（仅当未提供 `--start/--end` 时生效）
- `--paper-root PATH`：论文数据根目录，默认 `get_paper/data`
- `--news-root PATH`：新闻导出根目录，默认 `get_agent_news/data/exports`
- `--sdk-root PATH`：SDK 数据根目录，默认 `get_sdk_release_change_log/data`
- `--repos LIST`：逗号分隔仓库列表（`org/repo`），用于筛选 SDK 页面
- `--output-root PATH`：输出根目录，默认 `reports`
- `--overwrite`：目标报告已存在且非空时允许覆盖
- `--log-level LEVEL`：日志级别，默认 `INFO`
- `--no-run-sources`：仅聚合既有产出（默认会先执行子工程）
- `--name-by-exec-time`：即使不执行子工程，也按执行时间前缀命名输出目录
- `--enable-image-generation`：启用图片生成功能（需要配置 `LLM_API_KEY`），自动生成 SVG 图片并嵌入报告

## 四、输出与目录约定

- 报告：`reports/<执行时间前缀>-<YYYYMMDD-YYYYMMDD>/weekly-intel-report.md`（默认运行模式带前缀；仅聚合可用 `--name-by-exec-time`）
- Mermaid 图表：内嵌于 Markdown（不输出图片快照）
- 图片文件（启用 `--enable-image-generation` 时）：`reports/<range>/assets/image_<index>.svg`，自动嵌入到 Markdown 报告中的合适位置
- 幂等：若报告已存在且非空，默认不覆盖；`--overwrite` 可强制覆盖

## 五、渲染与格式约束

- Mermaid 图内文字不包含小括号/中括号/大括号，避免渲染异常
- 报告语言为中文
- LLM 可用（存在 `LLM_API_KEY`）时生成更深入洞察；失败自动回退模板化总结
- 图片生成功能（`--enable-image-generation`）：
  - 使用大模型分析报告内容，自动识别适合生成图片的部分
  - 最多生成 5 张图片（按优先级排序）
  - 图片类型包括：趋势图表、饼图、架构图、柱状图等
  - 图片保存在 `assets/` 子目录，使用相对路径嵌入 Markdown
  - 图片生成失败不影响报告正常生成（降级处理）

## 六、常见问题

- Q: 某个数据源没有产出会怎样？  
  A: 报告会保留该板块并标注“数据缺失”，整体仍会生成。

- Q: SDK 时间如何过滤？  
  A: 解析 `data/releases/*.md` 内的 `- **Published At**:` 字段按区间过滤。

- Q: 论文条目为何不全？  
  A: 优先读取 `<label>-ranked-all.json`；若只有统计文件，则只展示数量与趋势。

- Q: 图片生成功能如何使用？  
  A: 使用 `--enable-image-generation` 参数启用。需要配置 `LLM_API_KEY`。系统会自动分析报告内容，识别适合生成图片的部分，并使用 `svg_generator` 模块生成 SVG 图片。最多生成 5 张图片，按优先级排序。图片生成失败不影响报告正常生成。

- Q: 生成的图片保存在哪里？  
  A: 图片保存在报告目录的 `assets/` 子目录中，文件名为 `image_1.svg`, `image_2.svg` 等。在 Markdown 中使用相对路径引用。

## 七、子工程产出示例命令

```bash
# 论文（区间）
uv run python -m get_paper.src.monthly_run --start 2025-11-01 --end 2025-11-07

# 新闻（单次运行会产生一个新的 run 目录）
uv run python -m get_agent_news.src.main --once --source all --news-since-days 7 --export-markdown

# SDK Releases（抓取 + 可选摘要）
uv run python -m get_sdk_release_change_log.src.main --repo langchain-ai/langchain --max-pages 2
```


