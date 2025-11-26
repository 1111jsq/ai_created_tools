## ADDED Requirements

### Requirement: CLI 入口与输入解析
系统 SHALL 提供命令行接口，接受自然语言任务描述或文件路径作为输入，并解析为 SVG 生成请求。

#### Scenario: 自然语言输入
- **WHEN** 用户执行 `python -m svg_generator.main "创建一个简单的流程图，包含开始、处理、结束三个节点"`
- **THEN** 系统解析任务描述
- **AND** 调用 LLM 生成对应的 SVG 代码

#### Scenario: 文件路径输入
- **WHEN** 用户执行 `python -m svg_generator.main task.txt`
- **THEN** 系统读取文件内容作为任务描述
- **AND** 解析并生成 SVG

---

### Requirement: LLM 驱动的 SVG 生成
系统 SHALL 使用 LLM 解析任务描述并生成符合 SVG 1.1 规范的 XML 代码。当存在 `LLM_API_KEY` 时启用 LLM；不存在时 SHALL 返回明确的错误提示。

#### Scenario: 成功生成 SVG
- **WHEN** 提供有效的 `LLM_API_KEY` 和任务描述
- **THEN** LLM 生成符合 SVG 规范的 XML 代码
- **AND** 代码包含必要的 SVG 元素（如 `<svg>` 标签、命名空间等）

#### Scenario: 无 API Key 时的错误处理
- **WHEN** 未提供 `LLM_API_KEY`
- **THEN** 系统返回明确的错误信息，提示需要配置 API Key
- **AND** 不生成 SVG 文件

---

### Requirement: SVG 文件输出
系统 SHALL 将生成的 SVG 代码写入文件，支持自定义输出路径和文件名。默认输出到 `svg_generator/data/output/` 目录。

#### Scenario: 默认输出
- **WHEN** 用户未指定输出路径
- **THEN** SVG 文件保存到 `svg_generator/data/output/svg_output.svg`
- **AND** 文件名包含时间戳以避免覆盖

#### Scenario: 自定义输出路径
- **WHEN** 用户指定 `--output custom/path/diagram.svg`
- **THEN** SVG 文件保存到指定路径
- **AND** 自动创建不存在的目录

---

### Requirement: 配置管理集成
系统 SHALL 复用项目统一的配置管理，从项目根目录的 `.env` 文件读取 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 等配置，使用 `common/config_loader.py` 和 `common/llm.py`。

#### Scenario: 从 .env 读取配置
- **WHEN** `.env` 文件中配置了 `LLM_API_KEY=sk-xxx`
- **THEN** 系统自动读取并使用该配置
- **AND** 无需在命令行中重复指定

---

### Requirement: 基础 SVG 验证（可选但推荐）
系统 SHOULD 对生成的 SVG 代码进行基本的 XML 格式验证，确保文件可以被标准 SVG 渲染器解析。

#### Scenario: 验证有效 SVG
- **WHEN** LLM 生成有效的 SVG XML
- **THEN** 验证通过，文件正常保存

#### Scenario: 验证无效 SVG
- **WHEN** LLM 生成不符合规范的代码
- **THEN** 系统记录警告日志
- **AND** 仍尝试保存文件（允许用户手动修复）

---

### Requirement: 支持的图表类型
系统 SHALL 支持生成常见类型的 SVG 图表，包括但不限于：流程图、架构图、简单的数据可视化图表（柱状图、饼图等）。

#### Scenario: 生成流程图
- **WHEN** 任务描述包含"流程图"关键词
- **THEN** LLM 生成包含节点和连线的流程图 SVG

#### Scenario: 生成架构图
- **WHEN** 任务描述包含"架构"或"系统结构"关键词
- **THEN** LLM 生成展示组件关系的架构图 SVG

