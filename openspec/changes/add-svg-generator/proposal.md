# Change: 添加 SVG 图片生成器子工程

## Why
当前项目已有 PPT 生成器，但缺少直接生成 SVG 图片的能力。SVG 格式更适合网页嵌入、文档插入和矢量图形需求。用户需要一个独立的子工程，可以根据任务描述调用大模型生成 SVG 图片，满足不同场景的可视化需求。

## What Changes
- 新增 `svg_generator/` 子工程，独立于现有 PPT 生成器
- 提供 CLI 入口，接受任务描述（自然语言或文件路径）
- 使用 LLM 解析任务描述，提取图片需求（类型、内容、样式等）
- 生成符合规范的 SVG 文件，支持多种图表类型（流程图、架构图、数据可视化等）
- 复用项目统一的 `common/llm.py` LLM 客户端和配置管理
- 输出到指定目录，支持自定义文件名和样式
- 非破坏性：不影响现有子工程

## Impact
- Affected specs: `specs/svg-generator/spec.md`（新增能力）
- Affected code: 新增 `svg_generator/` 目录及其内部实现；不修改现有子工程代码
- 新增依赖：可能需要 SVG 生成库（如 `svgwrite` 或直接生成 SVG XML）

