## 1. Implementation
- [x] 1.1 创建 `svg_generator/` 目录结构（`src/`、`data/`、`README.md`、`requirements.txt`）
- [x] 1.2 实现 CLI 入口 `src/main.py`，支持自然语言输入和文件路径输入
- [x] 1.3 实现 `src/llm_service.py`，使用 `common/llm.py` 调用 LLM 生成 SVG 代码
- [x] 1.4 实现 `src/svg_validator.py`，提供基本的 SVG XML 验证（可选但推荐）
- [x] 1.5 实现 SVG 文件写入功能，支持自定义输出路径和文件名
- [x] 1.6 添加配置支持，从 `.env` 读取 `LLM_API_KEY` 等配置
- [x] 1.7 编写 `README.md`，包含使用说明和示例

## 2. Validation
- [ ] 2.1 测试简单流程图生成（如：开始 -> 处理 -> 结束）
- [ ] 2.2 测试架构图生成（如：展示系统组件关系）
- [ ] 2.3 测试数据图表生成（如：简单的柱状图或饼图）
- [ ] 2.4 验证生成的 SVG 文件可以在浏览器中正常渲染
- [ ] 2.5 测试无 LLM_API_KEY 时的错误处理
- [ ] 2.6 测试文件路径输入和自然语言输入两种方式

## 3. Documentation
- [x] 3.1 在 `svg_generator/README.md` 中编写完整的使用文档
- [x] 3.2 在根目录 `README.md` 中添加 SVG 生成器的简要说明
- [x] 3.3 添加示例 SVG 输出到文档中

