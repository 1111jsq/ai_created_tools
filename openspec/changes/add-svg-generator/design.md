## Context
用户需要一个可以根据任务描述生成 SVG 图片的工具。SVG 是矢量图形格式，适合网页、文档和报告中的图表插入。与现有的 PPT 生成器不同，SVG 生成器专注于生成独立的 SVG 文件，更灵活且易于集成。

## Goals / Non-Goals

### Goals
- 提供简洁的 CLI 接口，接受自然语言任务描述
- 使用 LLM 解析任务并生成结构化 SVG 数据
- 支持常见的图表类型（流程图、架构图、数据图表等）
- 生成符合 SVG 规范的 XML 文件
- 复用项目统一的配置和 LLM 客户端

### Non-Goals
- 不实现复杂的图形编辑器界面
- 不提供实时预览功能（首版）
- 不替代 PPT 生成器，两者服务于不同场景
- 不实现 SVG 动画（首版）

## Decisions

### Decision: 使用 LLM 生成 SVG 代码
**What**: 让 LLM 直接生成 SVG XML 代码，而不是先生成结构化数据再转换。

**Why**: 
- SVG 是文本格式，LLM 可以直接生成
- 减少中间转换层，简化实现
- 更灵活，可以生成任意复杂的 SVG 结构

**Alternatives considered**:
- 生成结构化数据后转换：需要维护转换逻辑，限制灵活性
- 使用 SVG 库（如 svgwrite）：需要定义数据模型，增加复杂度

### Decision: 复用 common/llm.py
**What**: 使用项目统一的 `LLMClient` 类，而不是创建新的客户端。

**Why**:
- 保持项目架构一致性
- 统一配置管理（从 .env 读取 LLM_API_KEY 等）
- 减少代码重复

### Decision: 独立的子工程结构
**What**: 创建 `svg_generator/` 目录，包含独立的 `src/`、`requirements.txt`、`README.md`。

**Why**:
- 遵循项目现有的模块化设计模式
- 便于独立维护和测试
- 可以独立运行，不依赖其他子工程

**Alternatives considered**:
- 集成到 PPT 生成器：但两者用途不同，SVG 更通用
- 放在 common 模块：但这是完整功能，不是共享工具

### Decision: 支持多种输入方式
**What**: CLI 接受自然语言字符串或文件路径。

**Why**:
- 提高易用性，支持交互式和批处理场景
- 与 PPT 生成器保持一致的用户体验

## Risks / Trade-offs

### Risk: LLM 生成的 SVG 可能不符合规范
**Mitigation**: 
- 在 prompt 中明确要求生成符合 SVG 1.1 规范的代码
- 添加基本的 XML 验证（可选）
- 提供示例 prompt 模板

### Risk: 复杂图表可能超出 LLM 能力
**Mitigation**:
- 首版专注于简单到中等复杂度的图表
- 在文档中说明支持的图表类型
- 未来可以扩展为分步骤生成（先结构后细节）

### Trade-off: 直接生成 SVG vs 结构化数据
- **直接生成**: 灵活但难以验证和调试
- **结构化数据**: 可控但限制灵活性
- **选择**: 首版选择直接生成，保持简单；未来可扩展为混合模式

## Migration Plan
不涉及迁移，这是全新功能。

## Open Questions
- SVG 样式定制程度（首版支持基础样式，未来可扩展）
- 是否需要支持从数据文件（CSV/JSON）生成图表（首版暂不支持）
- 错误处理策略：LLM 生成无效 SVG 时的降级方案

