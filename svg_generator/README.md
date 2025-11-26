# SVG 生成器

根据任务描述调用大模型生成 SVG 图片的工具。

## 功能特性

- 🎨 **自然语言输入**：使用自然语言描述，自动生成 SVG 图片
- 🤖 **LLM 驱动**：使用大模型理解任务并生成符合规范的 SVG 代码
- 📊 **多种图表类型**：支持流程图、架构图、数据可视化图表等
- ✅ **自动验证**：生成后自动验证 SVG 格式，确保可正常渲染
- 🔧 **灵活配置**：支持从 `.env` 文件或命令行参数配置 LLM API

## 安装

```bash
cd svg_generator
# 使用 uv 或 pip 安装依赖
uv pip install -r requirements.txt
# 或
pip install -r requirements.txt
```

## 配置

在项目根目录的 `.env` 文件中配置 LLM API：

```ini
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com  # 可选，默认使用 DeepSeek
LLM_MODEL=deepseek-chat  # 可选，默认使用 deepseek-chat
```

## 使用方法

### 基本用法

```bash
# 使用自然语言描述生成 SVG
python -m src.main "创建一个简单的流程图，包含开始、处理、结束三个节点"

# 从文件读取任务描述
python -m src.main task.txt

# 指定输出路径
python -m src.main "画一个系统架构图" --output diagrams/architecture.svg
```

### 命令行参数

- `input`: 任务描述（自然语言文本或文件路径，必需）
- `--output`, `-o`: 输出 SVG 文件路径（可选，默认: `data/output/svg_output_<timestamp>.svg`）
- `--api-key`: LLM API Key（可选，会从 .env 文件读取）
- `--base-url`: LLM API Base URL（可选，会从 .env 文件读取）
- `--model`: LLM 模型名称（可选，会从 .env 文件读取）
- `--temperature`: LLM 温度参数（默认: 0.3）

### 使用 uv 运行

```bash
# 从项目根目录运行
uv run python -m src.main "创建一个流程图"
```

## 示例

### 生成流程图

```bash
python -m src.main "创建一个流程图，展示用户登录流程：开始 -> 输入用户名密码 -> 验证 -> 登录成功 -> 结束"
```

### 生成架构图

```bash
python -m src.main "画一个微服务架构图，包含前端、API 网关、用户服务、订单服务、数据库"
```

### 生成数据图表

```bash
python -m src.main "创建一个柱状图，展示 Q1: 100, Q2: 150, Q3: 120, Q4: 180 的销售数据"
```

## 输出

生成的 SVG 文件默认保存在 `svg_generator/data/output/` 目录，文件名包含时间戳以避免覆盖。

SVG 文件可以直接：
- 在浏览器中打开查看
- 嵌入到 HTML 文档中
- 插入到 Markdown 文档中
- 导入到设计工具（如 Figma、Inkscape）中编辑

## 技术实现

- **LLM 集成**：使用 `common/llm.py` 统一 LLM 客户端
- **配置管理**：复用项目统一的配置加载机制
- **SVG 验证**：自动验证生成的 SVG 是否符合 XML 规范
- **错误处理**：完善的错误提示和日志记录

## 注意事项

1. **API Key 必需**：使用前必须配置 `LLM_API_KEY`
2. **LLM 输出质量**：生成的 SVG 质量取决于 LLM 模型的能力，复杂图表可能需要多次尝试
3. **SVG 验证**：如果验证失败，文件仍会保存，但可能无法正常渲染，需要手动修复
4. **代码块提取**：如果 LLM 返回包含 markdown 代码块标记，系统会自动提取其中的 SVG 代码

## 故障排除

### 错误：未提供 LLM_API_KEY

确保在项目根目录的 `.env` 文件中配置了 `LLM_API_KEY`，或在命令行中使用 `--api-key` 参数。

### 生成的 SVG 无法渲染

1. 检查 SVG 文件内容，确保包含有效的 `<svg>` 标签
2. 尝试在浏览器中打开，查看控制台错误信息
3. 可以手动编辑 SVG 文件进行修复

### LLM 返回的内容不是 SVG

系统会自动尝试从返回内容中提取 SVG 代码。如果仍然失败，可以：
1. 调整 prompt，明确要求只输出 SVG 代码
2. 降低 temperature 参数以获得更稳定的输出
3. 尝试更具体的任务描述

