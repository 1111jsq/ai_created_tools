## ADDED Requirements

### Requirement: 区间化编排 CLI（默认 7 天）
系统 SHALL 提供编排入口以分析固定时间段，默认最近 7 天；支持 `--start YYYY-MM-DD --end YYYY-MM-DD` 与 `--last-days N` 的互斥参数组合，并输出到约定目录。

#### Scenario: 默认最近 7 天
- **WHEN** 用户未提供任何时间参数
- **THEN** 计算 `today-6 .. today` 的区间作为标签（共 7 天）
- **AND** 输出到 `reports/<YYYYMMDD-YYYYMMDD>/weekly-intel-report.md`

#### Scenario: 明确的起止日期
- **WHEN** 用户传入 `--start 2025-11-01 --end 2025-11-07`
- **THEN** 使用 `20251101-20251107` 作为输出标签目录
- **AND** 同步用于读取三个子工程的导出目录

---

### Requirement: 多源只读聚合与缺失容忍
系统 MUST 仅从既有产物读取数据（不调用原始抓取流程），并在任一数据源缺失时提供降级占位提示，报告仍可生成。

#### Scenario: 三源齐全
- **WHEN** 论文、新闻、SDK 更新都存在对应区间的导出
- **THEN** 报告包含三个板块与综合洞察

#### Scenario: 单源缺失
- **WHEN** 某一数据源目录不存在或为空
- **THEN** 对应板块显示“数据缺失”说明
- **AND** 其它板块与总体报告正常生成

---

### Requirement: Markdown 深度分析报告（中文）
系统 SHALL 生成结构化 Markdown，包含：概览（数据量/活跃度）、论文、新闻、SDK 更新、综合洞察（趋势/主题/交叉影响）与附录（文件索引/路径）。

#### Scenario: 成功导出报告
- **WHEN** 编排执行完成
- **THEN** 写入 `reports/<range>/weekly-intel-report.md`
- **AND** 文内各板块均以中文撰写，包含数据来源与时间范围标识

---

### Requirement: LLM 可选与安全降级
当存在 `DEEPSEEK_API_KEY` 时，系统 SHALL 使用 LLM 生成“综合洞察/重点解读/建议”；当不存在密钥时，SHALL 降级为模板化摘要，不中止流程。

#### Scenario: 有密钥启用 LLM
- **WHEN** 环境中提供 `DEEPSEEK_API_KEY`
- **THEN** 生成 LLM 驱动的深度分析段落，并在日志中标注“LLM 分析已启用”

#### Scenario: 无密钥模板化
- **WHEN** 未提供 `DEEPSEEK_API_KEY`
- **THEN** 使用规则/模板生成基础总结
- **AND** 报告正文中不出现 API Key 或内部错误信息

---

### Requirement: Mermaid 图表与无括号文本约束
系统 SHALL 在报告中内嵌 Mermaid 图表代码块（柱状/饼图/流程图），用于可视化数量分布、来源占比与管道流向；图内文本不得包含括号类符号（小/中/大括号）。

#### Scenario: 渠道占比饼图
- **WHEN** 生成“论文/新闻/SDK 更新占比”图
- **THEN** 以 Mermaid 饼图表示三类占比
- **AND** 图例文本不含括号类符号

#### Scenario: 流程图展示编排流
- **WHEN** 展示“编排从读取到导出的步骤”
- **THEN** 以 Mermaid 流程图表示主要步骤
- **AND** 每个节点文本不含括号类符号

---

### Requirement: 稳定的目录结构与命名
输出目录 SHALL 稳定：`reports/<YYYYMMDD-YYYYMMDD>/weekly-intel-report.md`；可选的图表快照文件写入 `reports/<range>/assets/`；重复执行 SHALL 幂等（已有非空文件默认不覆盖，或使用 `--overwrite` 显式允许覆盖）。

#### Scenario: 幂等写入
- **WHEN** 同一时间范围重复执行
- **THEN** 若目标 Markdown 已存在且非空，默认不覆盖
- **AND** 传入 `--overwrite` 时允许覆盖


