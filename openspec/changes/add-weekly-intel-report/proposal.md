# Change: 每周/区间 智能体深度分析报告（整合论文/新闻/SDK 更新）

## Why
当前三个子工程分别输出论文、行业新闻、SDK 版本更新，缺少统一的跨域洞察与可视化汇总。手动拼接成本高、不可重复，无法形成一键可分享的中文深度报告。

## What Changes
- 新增一个只读式编排器（Orchestrator）与 CLI，默认统计最近 7 天；支持 `--start YYYY-MM-DD --end YYYY-MM-DD` 与 `--last-days N`
- 聚合 `get_paper`、`get_agent_news`、`get_sdk_release_change_log` 现有导出产物，计算基础统计与交叉洞察
- 生成结构化的 Markdown 报告（中文），包含：概览、论文、新闻、SDK 更新、综合洞察与附录
- 生成可复制的 Mermaid 图表代码块（柱状/饼图等），遵循“图内文本不含括号类符号”的约束
- LLM 分析可选：存在 `DEEPSEEK_API_KEY` 时启用深度分析；缺失时降级为模板化总结
- 稳定输出目录：`reports/<YYYYMMDD-YYYYMMDD>/weekly-intel-report.md` 与 `reports/<range>/assets/`（图表快照可选）
- 非破坏性：不修改子工程的行为与接口，仅消费其导出文件

## Impact
- Affected specs: `specs/weekly-intel-report/spec.md`
- Affected code (后续实现)：新增 `report/` 或顶层 `src/report_*.py` 编排入口、适配读取三个子工程导出的文件夹结构；不会改动现有子工程


