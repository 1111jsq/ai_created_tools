## ADDED Requirements

### Requirement: 统一日志系统
所有子项目必须使用 Python 标准 `logging` 模块进行日志输出，禁止使用 `print()` 进行日志记录。

#### Scenario: 日志输出使用标准模块
- **WHEN** 代码需要输出日志信息
- **THEN** 使用 `logging.getLogger()` 获取 logger 实例，并使用 `logger.info()`, `logger.warning()`, `logger.error()` 等方法
- **AND** 日志格式统一为：`%(asctime)s [%(levelname)s] %(name)s: %(message)s`

#### Scenario: 调试信息使用日志而非 print
- **WHEN** 需要输出调试信息
- **THEN** 使用 `logger.debug()` 而非 `print()`
- **AND** 调试日志可通过 `LOG_LEVEL=DEBUG` 环境变量控制

### Requirement: 依赖版本管理
所有子项目的依赖必须指定明确的版本号，相同依赖在不同子项目中使用相同版本。

#### Scenario: 依赖版本一致性
- **WHEN** 多个子项目使用相同的依赖包
- **THEN** 所有子项目的 `requirements.txt` 中该依赖的版本号必须一致
- **AND** 版本号使用 `>=` 约束，指定最低版本

#### Scenario: 依赖文件完整性
- **WHEN** 子项目有 `requirements.txt` 文件
- **THEN** 所有依赖项必须包含版本号约束
- **AND** 不允许使用未指定版本的依赖

### Requirement: 错误处理规范
关键操作必须包含适当的异常处理和错误日志记录。

#### Scenario: 配置加载错误处理
- **WHEN** 加载配置文件失败
- **THEN** 捕获异常并记录详细的错误日志
- **AND** 提供清晰的错误信息，包含文件路径和失败原因

#### Scenario: 网络请求错误处理
- **WHEN** 网络请求失败
- **THEN** 捕获异常并记录错误日志
- **AND** 包含请求 URL、状态码（如有）和错误详情

### Requirement: 代码清理
代码中不得包含调试用的 `print()` 语句，所有输出必须通过日志系统。

#### Scenario: 移除调试代码
- **WHEN** 代码中存在调试用的 `print()` 语句
- **THEN** 将其替换为适当的日志调用或完全移除
- **AND** 确保移除后不影响功能

### Requirement: 内存效率优化
代码应优先使用生成器和流式处理，避免不必要地将大量数据加载到内存。

#### Scenario: 生成器使用
- **WHEN** 函数返回大量数据项
- **THEN** 优先使用生成器（`yield`）而非返回列表
- **AND** 仅在必要时（如需要多次遍历）才转换为列表

#### Scenario: 流式处理
- **WHEN** 处理大量数据时
- **THEN** 使用迭代器模式，逐项处理而非一次性加载全部
- **AND** 避免在循环中多次调用 `list()` 转换生成器

### Requirement: LLM 客户端统一
所有 LLM API 调用必须使用 `common/llm.py` 提供的 `LLMClient`，禁止直接使用 `requests` 或其他方式调用 LLM API。

#### Scenario: 统一 LLM 调用
- **WHEN** 需要调用 LLM API
- **THEN** 使用 `common/llm.py` 的 `LLMClient` 类
- **AND** 禁止直接使用 `requests` 或其他 HTTP 客户端调用 LLM API

#### Scenario: 配置统一
- **WHEN** 初始化 LLM 客户端
- **THEN** 使用 `common/config_loader` 从环境变量读取配置
- **AND** 支持通过参数覆盖默认配置

### Requirement: 移除硬编码
代码中不得包含硬编码的配置值（如代理地址、API URL），所有配置必须从环境变量或配置文件读取。

#### Scenario: 代理配置
- **WHEN** 需要设置 HTTP/HTTPS 代理
- **THEN** 从环境变量 `HTTP_PROXY` 和 `HTTPS_PROXY` 读取
- **AND** 禁止在代码中硬编码代理地址

#### Scenario: API URL 配置
- **WHEN** 需要调用外部 API
- **THEN** 从环境变量或配置文件读取 API URL
- **AND** 禁止硬编码 API 端点地址

### Requirement: 流程逻辑正确性
代码流程必须逻辑正确，避免变量未定义、循环控制错误等问题。

#### Scenario: 变量初始化
- **WHEN** 变量可能在不同分支中使用
- **THEN** 在所有使用前确保变量已初始化
- **AND** 提供合理的默认值

#### Scenario: 循环控制
- **WHEN** 在循环中使用 `continue` 或 `break`
- **THEN** 确保控制流符合预期逻辑
- **AND** 避免跳过不应跳过的步骤

