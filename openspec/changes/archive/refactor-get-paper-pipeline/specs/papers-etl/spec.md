## ADDED Requirements

### Requirement: ETL 按月/区间运行的 CLI
系统 SHALL 提供 `python -m src.monthly_run` 入口，支持：
- 方式一：`--month YYYY-MM`
- 方式二：`--start YYYY-MM-DD --end YYYY-MM-DD`
并将产物输出到 `src/data/` 目录结构下（raw、normalized、exports 等保持现有约定）。

#### Scenario: 区间运行成功
- **WHEN** 用户执行 `python -m src.monthly_run --start 2025-11-01 --end 2025-11-16`
- **THEN** 在 `src/data/raw/20251101-20251116/` 下写入原始抓取，在 `src/data/exports/20251101-20251116/` 下写入 JSON/CSV/MD 与统计

#### Scenario: 按月运行成功
- **WHEN** 用户执行 `python -m src.monthly_run --month 2025-11`
- **THEN** 产物以 `2025-11` 作为标签写入对应目录

---

### Requirement: 配置与密钥管理
系统 MUST NOT 硬编码任何密钥；DeepSeek API Key SHALL 从环境变量 `DEEPSEEK_API_KEY` 读取；HTTP/HTTPS 代理 SHALL 仅通过环境变量配置（若需要）。
当未设置 `DEEPSEEK_API_KEY` 时，系统 SHALL 安全跳过 LLM 分析并给出告警日志。

#### Scenario: 未设置密钥
- **WHEN** 环境中没有 `DEEPSEEK_API_KEY`
- **THEN** 跳过 LLM 分析且继续导出其它产物

---

### Requirement: OpenReview v2 优先与回退
系统 SHALL 优先使用 OpenReview v2 客户端（需要 `OPENREVIEW_VENUE_ID`），若未命中或失败，SHALL 回退至 v1 抓取。

#### Scenario: v2 成功
- **WHEN** 设置 `OPENREVIEW_ENABLED=1` 且提供 `OPENREVIEW_VENUE_ID`
- **THEN** 使用 v2 抓取并写入 `raw/openreview/`

#### Scenario: v2 无结果回退 v1
- **WHEN** v2 返回空或失败
- **THEN** 回退 v1 抓取并写入 `raw/openreview/`

---

### Requirement: PDF 下载稳健性
系统 SHALL 为每篇带 `pdfUrl` 的论文尝试下载，采用重试与临时文件策略，并在 `raw/pdfs/manifest.json` 中持久化 `paperId -> 本地路径` 映射。

#### Scenario: 小文件与内容类型
- **WHEN** 下载成功但文件小于 1KB
- **THEN** 视为异常并重试/告警

---

### Requirement: 导出与统计报告
系统 SHALL 导出：
- 列表：JSON、CSV、Markdown
- 统计：基础统计 `*-stats.json` 与中文统计 `*-stats-cn.md`
- 排名：`*-top10.json` 与 `*-ranked-(all|rest).json`
- 综合报告：`*-comprehensive-report.md`

#### Scenario: 成功导出
- **WHEN** 管道执行完成
- **THEN** 在 `exports/<label>/` 下存在上述文件


