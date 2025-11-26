# Project Context

## Purpose

本项目是一个 AI 工具集合，用于自动化收集、分析和报告 AI Agent 与大模型领域的最新动态。主要功能包括：

- **论文爬虫** (`get_paper`): 从 arXiv 抓取 AI/Agent 相关论文，进行质量筛选、分类、摘要和排名
- **新闻爬虫** (`get_agent_news`): 从 AIbase 等来源抓取 AI Agent 相关资讯，支持去重和智能排序
- **SDK Release 爬虫** (`get_sdk_release_change_log`): 爬取 GitHub 上智能体框架的 Releases，生成摘要
- **报告生成器** (`report`): 聚合上述三个数据源，生成每周/区间的深度分析报告（中文 Markdown + Mermaid 图表）
- **PPT 生成器** (`PPT`): 从自然语言描述生成带图表的 PowerPoint 演示文稿

所有工具共享统一的配置管理（`.env`）和 LLM 客户端（`common/llm.py`）。

## Tech Stack

- **Python 3.11+**: 主要编程语言
- **uv**: 虚拟环境管理和依赖安装工具（推荐使用）
- **OpenAI SDK**: LLM API 客户端（兼容 DeepSeek 等）
- **httpx**: HTTP 客户端（用于爬虫）
- **feedparser**: RSS/Atom 解析（arXiv）
- **python-dotenv**: 环境变量管理
- **python-pptx**: PowerPoint 文件生成
- **pydantic**: 数据验证和模型定义
- **OpenSpec**: 规范驱动的开发流程管理

## Project Conventions

### Code Style

- **类型提示**: 所有函数必须使用类型提示，使用 `from __future__ import annotations` 启用延迟评估
- **命名约定**:
  - 函数和变量：`snake_case`
  - 类：`PascalCase`
  - 常量：`UPPER_SNAKE_CASE`
  - 私有函数：以 `_` 开头
- **文档字符串**: 使用中文编写文档和注释（用户要求）
- **导入顺序**: 标准库 → 第三方库 → 本地模块
- **代码格式**: 遵循 PEP 8，使用 4 空格缩进

### Architecture Patterns

- **模块化设计**: 每个工具（`get_paper`, `get_agent_news` 等）独立运行，共享 `common` 模块
- **管道式处理**: 数据流遵循 `fetch → parse → normalize → classify → export` 模式
- **统一配置管理**: 所有配置通过 `common/config_loader.py` 从项目根目录的 `.env` 文件读取
- **统一 LLM 客户端**: 所有 LLM 调用通过 `common/llm.py` 的 `LLMClient` 类
- **数据持久化**: 使用文件系统存储（JSON、CSV、Markdown），不依赖数据库
- **幂等性**: 工具支持重复运行，已存在的数据可选择性覆盖
- **内存优化**: 优先使用生成器和流式处理，避免不必要地将大量数据加载到内存

### Testing Strategy

- 目前项目未建立完整的测试框架
- 建议未来添加：
  - 单元测试：使用 `pytest` 测试核心逻辑
  - 集成测试：测试完整的数据流管道
  - 数据验证：使用 `pydantic` 模型进行数据校验

### Logging Best Practices

- **统一使用 `logging` 模块**：禁止使用 `print()` 进行日志输出
- **日志格式**：统一使用 `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- **日志级别**：
  - `DEBUG`: 详细的调试信息
  - `INFO`: 一般信息（默认级别）
  - `WARNING`: 警告信息
  - `ERROR`: 错误信息
  - `CRITICAL`: 严重错误
- **日志配置**：在模块入口处配置 `logging.basicConfig()`，支持文件和控制台输出
- **异常日志**：使用 `logger.exception()` 记录异常，自动包含堆栈跟踪

### Error Handling Best Practices

- **关键操作必须包含异常处理**：网络请求、文件操作、配置加载等
- **错误日志格式**：包含足够的上下文信息（URL、文件路径、参数等）
- **异常传播**：根据场景决定是捕获并记录，还是重新抛出
- **用户友好的错误信息**：提供清晰的错误提示和解决建议

### Git Workflow

- **提交规范**: 使用语义化提交信息（`feat:`, `fix:`, `refactor:` 等）
- **提交频率**: 不要每次修改就提交，要求提交后再提交（批量提交）
- **分支策略**: 主要使用 `main` 分支，功能开发可创建特性分支
- **提交命令示例**: `git add . && git commit -m "feat: 添加 Arxiv 论文分析器及相关配置" && git push`

## Domain Context

### AI Agent 与 LLM 领域

- **论文来源**: 主要关注 arXiv 上的 `cs.AI`、`cs.LG`、`cs.MA` 类别
- **机构关注**: 优先关注顶级机构（Google、DeepMind、OpenAI、Meta、Stanford、MIT 等）和知名高校
- **新闻来源**: AIbase 日报和资讯，聚焦 AI Agent、工具使用、多模态等主题
- **SDK 框架**: 关注主流智能体框架（LangChain、AutoGPT、AgentGPT 等）的 GitHub Releases
- **报告语言**: 所有报告和文档使用中文

### 数据流程

1. **抓取阶段**: 从外部 API/网站获取原始数据
2. **解析阶段**: 将原始数据转换为结构化格式
3. **规范化阶段**: 统一数据模型（如 `Paper` 模型）
4. **质量筛选**: 基于机构、引用、关键词等筛选高质量内容
5. **分类与摘要**: 使用规则或 LLM 进行分类和摘要生成
6. **导出阶段**: 生成 JSON、CSV、Markdown 等格式的输出

## Important Constraints

### 合规与礼貌抓取

- **遵守 robots.txt**: 自动检测并遵守目标网站的 robots.txt 规则
- **请求延迟**: 默认延迟 1.0 秒，避免对目标服务器造成压力
- **超时设置**: 默认超时 30 秒，支持重试机制
- **User-Agent**: 设置合理的 User-Agent 标识
- **速率限制**: 实施主机级速率限制，避免被封禁

### 技术约束

- **Mermaid 图表**: 图表内文本不能包含小括号、中括号、大括号等特殊符号，避免渲染异常
- **文件编码**: 统一使用 UTF-8 编码
- **路径约定**: 所有路径配置相对于项目根目录
- **环境变量优先级**: 环境变量优先于 `.env` 文件（`load_dotenv(override=False)`）

### 数据约束

- **敏感信息**: `.env` 文件包含 API 密钥等敏感信息，不得提交到版本控制
- **数据格式**: 输出数据使用 JSON、CSV、Markdown 等标准格式
- **幂等性**: 工具应支持重复运行而不产生副作用

## External Dependencies

### API 服务

- **arXiv API**: 论文元数据和 RSS 源
- **GitHub API**: Releases 信息和仓库元数据（可选 Token 提升限额）
- **LLM API**: DeepSeek、OpenAI 等兼容 OpenAI API 格式的服务
  - 必需配置：`LLM_API_KEY`
  - 可选配置：`LLM_BASE_URL`、`LLM_MODEL`、`LLM_TIMEOUT`
  - 未提供 API Key 时，相关功能自动跳过，其他流程正常执行

### 网站爬取

- **AIbase**: AI 资讯网站（遵守 robots.txt 和站点条款）
- **OpenReview**: 已移除（不再使用）

### 配置依赖

- **`.env` 文件**: 项目根目录的统一配置文件
- **`repositories.yaml`**: SDK 爬虫的仓库列表配置（可选）
- **`sources.yaml`**: 新闻爬虫的数据源配置（可选）

### 工具依赖

- **uv**: 推荐用于虚拟环境管理（更快、更干净）
- **Git**: 版本控制
- **Python 3.11+**: 运行环境
