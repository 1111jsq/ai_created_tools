## ADDED Requirements
### Requirement: Deterministic Markdown Export Formatting
Markdown 导出必须使用空格缩进且产出稳定的文件命名。

#### Scenario: Export a news item to Markdown
- WHEN 系统导出单条资讯为 Markdown
- THEN 使用空格缩进，不得混用 Tab
- AND 文件名遵循 `news-YYYY-MM-DD-<slug>-<hash8>.md`
- AND 若标题为空则使用 `untitled`
- AND `published_at` 若存在则以 ISO 格式输出

## MODIFIED Requirements
### Requirement: Ranking Strategy (LLM-optional with safe fallback)
系统在存在 `DEEPSEEK_API_KEY` 时启用 LLM 批量打分，否则回退到启发式打分；两种策略的排序都必须可用。

#### Scenario: With DEEPSEEK_API_KEY
- WHEN 环境变量中提供 `DEEPSEEK_API_KEY`
- THEN 使用 LLM 批量打分，并将请求/响应写入本次运行导出目录
- AND 若 LLM 失败则对失败批次回退到启发式

#### Scenario: Without DEEPSEEK_API_KEY
- WHEN 未提供 `DEEPSEEK_API_KEY`
- THEN 全量使用启发式打分
- AND 不产生任何 LLM 网络请求

## REMOVED Requirements
### Requirement: Legacy SQLite Database and Backup
**Reason**: 已完全采用文件系统导出（CSV/JSONL/Markdown/Index），数据库备份无实际用途且增加复杂度  
**Migration**: 无需迁移，删除备份相关函数与调用

#### Scenario: Run CLI flow
- WHEN 执行主流程
- THEN 不再访问或备份 SQLite 文件
- AND 不再读取数据库路径配置

### Requirement: Built-in Job Scheduling
**Reason**: 运行计划应由外部调度器（如系统计划任务、CI）负责，库内不再内置定时循环  
**Migration**: 删除 `schedule/weekly.py`，在文档中提供外部调度示例

#### Scenario: Library usage
- WHEN 用户需要周期性执行
- THEN 使用系统级调度器触发 CLI，而非库内调度模块

### Requirement: Default LLM API Key in code
**Reason**: 安全合规风险；默认 Key 必须为空  
**Migration**: 通过环境变量显式提供，默认不启用 LLM

#### Scenario: Missing API key
- WHEN 未设置 `DEEPSEEK_API_KEY`
- THEN LLM 客户端 `available()` 返回 False，排序逻辑走启发式


