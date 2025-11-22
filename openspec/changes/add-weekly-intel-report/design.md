## Context
本变更跨 `get_paper`、`get_agent_news`、`get_sdk_release_change_log` 三个子工程的导出产物进行只读聚合，生成中文 Markdown 深度分析报告。各子工程已具备按区间导出与统计能力，编排器无需重复抓取。

## Goals / Non-Goals
- Goals
  - 统一时间区间的只读聚合
  - 一键生成中文深度报告与 Mermaid 可视化
  - LLM 可选，缺失时模板化降级
- Non-Goals
  - 不改动子工程导出格式与代码路径
  - 不引入内置调度器（外部 CI/计划任务负责）

## Decisions
- 目录约定：输出至 `reports/<YYYYMMDD-YYYYMMDD>/weekly-intel-report.md`，图表快照（若实现）至 `reports/<range>/assets/`
- 时间解析：`--start/--end` 或 `--last-days N`，缺省为最近 7 天
- 读取策略：优先读取区间匹配的导出目录；读取失败/缺失时以占位提示降级
- LLM 策略：`DEEPSEEK_API_KEY` 存在即启用深度分析；否则走模板化摘要
- Mermaid 约束：图内文本不含括号类符号，避免渲染异常；首选柱状/饼图/简单流程图
- 幂等策略：默认不覆盖已存在且非空的目标文件；提供 `--overwrite` 以便显式覆盖

## Risks / Trade-offs
- 风险：某一数据源缺失导致洞察偏差 → 降级提示并在“综合洞察”中披露数据缺失
- 风险：Mermaid 渲染差异 → 提供纯文本统计作为兜底
- 取舍：不内置调度，降低耦合，交给外部系统触发

## Migration Plan
新增 CLI 与聚合逻辑，不涉及数据迁移；与子工程保持松耦合。

## Open Questions
- 综合评分/权重算法是否需要可配置策略？
- 图表类型是否需要导出 PNG 快照（需要额外依赖）？


