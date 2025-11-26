## MODIFIED Requirements

### Requirement: Markdown 深度分析报告（中文）
系统 SHALL 生成结构化 Markdown，包含：概览（数据量/活跃度）、论文、新闻、SDK 更新、综合洞察（趋势/主题/交叉影响）与附录（文件索引/路径）。当启用图片生成功能时，报告 SHALL 在合适位置包含生成的图片引用（SVG 或从 PPT 导出的图片），形成图文结合的展示效果。

#### Scenario: 成功导出报告
- **WHEN** 编排执行完成
- **THEN** 写入 `reports/<range>/weekly-intel-report.md`
- **AND** 文内各板块均以中文撰写，包含数据来源与时间范围标识

#### Scenario: 成功导出报告（含图片）
- **WHEN** 编排执行完成，且启用了图片生成功能（通过 `--enable-image-generation` 或配置）
- **THEN** 系统使用 LLM 分析报告内容，识别适合生成图片的部分
- **AND** 生成相应的图片文件（SVG 或从 PPT 导出）并保存到 `reports/<range>/assets/` 目录
- **AND** 在 Markdown 报告的合适位置插入图片引用（使用相对路径，如 `![描述](./assets/image_1.svg)`）
- **AND** 报告包含图文结合的展示效果

## ADDED Requirements

### Requirement: LLM 驱动的图片生成判断
系统 SHALL 使用大模型分析报告内容，识别哪些部分适合生成图片（如趋势图表、架构图、数据可视化等），并返回结构化的判断结果（包含图片类型、描述、建议位置等）。

#### Scenario: LLM 判断适合生成图片的内容
- **WHEN** 启用图片生成功能，且报告数据准备完成
- **THEN** 系统调用 LLM 分析报告内容（论文、新闻、SDK 更新等数据）
- **AND** LLM 返回 JSON 格式的判断结果，包含：
  - `image_type`: 图片类型（如 "trend_chart", "pie_chart", "architecture_diagram" 等）
  - `description`: 图片生成的任务描述（自然语言）
  - `suggested_position`: 建议插入位置（如 "after_overview", "in_insights" 等）
  - `priority`: 优先级（1-5，数字越大优先级越高）
- **AND** 系统根据优先级筛选，最多生成 5 张图片

#### Scenario: LLM 判断失败时的降级处理
- **WHEN** LLM 判断调用失败（API 错误、超时等）或返回无效结果
- **THEN** 系统记录警告日志
- **AND** 报告正常生成，但不包含自动生成的图片
- **AND** 不中断报告生成流程

### Requirement: SVG 图片生成与集成
系统 SHALL 使用 `svg_generator` 模块根据 LLM 判断结果生成 SVG 图片，并将图片保存到报告的 `assets/` 目录，在 Markdown 中插入图片引用。

#### Scenario: 生成 SVG 图片
- **WHEN** LLM 判断结果为需要生成 SVG 图片（如流程图、架构图、数据图表）
- **THEN** 系统调用 `svg_generator` 模块，传入 LLM 生成的图片描述
- **AND** SVG 生成器返回有效的 SVG XML 代码
- **AND** 系统将 SVG 代码保存到 `reports/<range>/assets/` 目录，文件名为 `image_<index>.svg`（index 从 1 开始）
- **AND** 在 Markdown 报告的建议位置插入图片引用：`![图片描述](./assets/image_<index>.svg)`

#### Scenario: SVG 生成失败时的处理
- **WHEN** SVG 生成失败（LLM 调用失败、生成的代码无效等）
- **THEN** 系统记录错误日志，但不中断报告生成
- **AND** 报告中不包含该图片的引用
- **AND** 其他图片生成和报告生成继续正常进行

### Requirement: 图片生成配置与开关
系统 SHALL 提供配置选项控制图片生成功能的启用/禁用，支持通过命令行参数或环境变量配置。

#### Scenario: 通过命令行启用图片生成
- **WHEN** 用户执行 `python -m report.main --enable-image-generation`
- **THEN** 系统启用图片生成功能
- **AND** 如果 `LLM_API_KEY` 未配置，记录警告但不中断报告生成

#### Scenario: 图片生成默认禁用
- **WHEN** 用户未指定 `--enable-image-generation` 参数
- **THEN** 图片生成功能默认禁用
- **AND** 报告正常生成，仅包含文本和 Mermaid 图表

#### Scenario: 限制图片生成数量
- **WHEN** LLM 判断结果包含多张图片建议
- **THEN** 系统按优先级排序，最多生成 5 张图片
- **AND** 记录日志说明实际生成的图片数量

### Requirement: 报告目录结构与图片存储
报告输出目录 SHALL 包含 `assets/` 子目录用于存储生成的图片文件，保持目录结构清晰且便于管理。

#### Scenario: 创建 assets 目录
- **WHEN** 启用图片生成功能
- **THEN** 系统在报告输出目录下创建 `assets/` 子目录（如果不存在）
- **AND** 生成的图片文件保存在该目录中

#### Scenario: 图片文件命名
- **WHEN** 生成多张图片
- **THEN** 图片文件使用递增的索引命名：`image_1.svg`, `image_2.svg`, ...
- **AND** 文件名在报告中对应的图片引用中保持一致

### Requirement: 向后兼容性
图片生成功能 SHALL 作为可选功能，不影响现有报告生成流程的稳定性和功能。

#### Scenario: 禁用图片生成时的行为
- **WHEN** 图片生成功能禁用（默认状态）
- **THEN** 报告生成行为与现有实现完全一致
- **AND** 不创建 `assets/` 目录（除非用户明确需要）
- **AND** 不进行任何 LLM 调用（用于图片判断）

#### Scenario: 图片生成失败时的降级
- **WHEN** 图片生成过程中出现任何错误
- **THEN** 系统记录错误日志
- **AND** 报告仍正常生成，包含已成功生成的图片
- **AND** 报告结构完整，不因图片生成失败而缺失内容

