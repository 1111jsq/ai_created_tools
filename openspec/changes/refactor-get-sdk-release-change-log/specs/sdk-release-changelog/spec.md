## ADDED Requirements
### Requirement: CLI 参数化入口（安全、可重复）
系统 SHALL 通过 CLI 提供参数化入口，允许用户配置仓库与分页范围，并且不得在代码中内联凭据。

#### Scenario: 基本运行
- **WHEN** 执行 `python -m src.main --repo langchain-ai/langchain --max-pages 2`
- **THEN** 抓取前 2 页 Releases
- **AND** 将页面 Markdown 写入 `data/releases/langchain-ai_langchain_1.md`、`..._2.md`

#### Scenario: 起始页偏移
- **WHEN** 传入 `--start-page 3 --max-pages 2`
- **THEN** 抓取第 3、4 页
- **AND** 文件名为 `..._3.md` 与 `..._4.md`

#### Scenario: GitHub Token 可选
- **WHEN** 通过 `--gh-token` 或 `GITHUB_TOKEN` 提供访问令牌
- **THEN** 请求携带认证头
- **AND** 在未提供时不报错，仅可能遇到限额退避

### Requirement: 安全配置（无硬编码密钥/代理）
系统 MUST 不在代码中硬编码任何 API Key 或企业代理；代理与密钥均从环境变量读取；缺失时提供安全降级。

#### Scenario: 缺失 DeepSeek/OpenAI 密钥
- **WHEN** 未设置 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY`
- **THEN** 摘要流程被跳过且不抛出异常
- **AND** Releases Markdown 仍被正常写入

#### Scenario: 代理设置
- **WHEN** 未设置 HTTP(S) 代理环境变量
- **THEN** 系统不得强制写入代理
- **AND** 如已设置，则复用用户环境值

### Requirement: 稳定与幂等输出
系统 SHALL 使用 UTF-8 编码；输出目录固定；默认幂等（存在且非空文件不覆盖）。

#### Scenario: 页面级 Markdown 输出
- **WHEN** 保存第 N 页
- **THEN** 写入 `data/releases/<repo_slug>_<N>.md`
- **AND** 若文件已存在且非空，默认不覆盖

#### Scenario: 页面级摘要输出
- **WHEN** 生成第 N 页摘要
- **THEN** 写入 `data/summaries/<repo_slug>_<N>_summary.md`
- **AND** 若文件已存在且非空，默认不覆盖

### Requirement: 网络鲁棒性（限速、超时、重试）
系统 SHALL 应对 GitHub 限额与临时错误：指数退避重试、请求超时受控、相邻请求间延迟可配置。

#### Scenario: 命中 GitHub 限额
- **WHEN** 返回 403 且响应包含 rate limit
- **THEN** 按尝试次数递增退避后重试
- **AND** 最终失败时给出清晰错误

### Requirement: 日志最小化与不泄露凭据
系统 MUST 避免在日志中打印 Token/密钥等敏感信息，仅打印必要流程日志与目标文件路径。

## REMOVED Requirements
### Requirement: 硬编码密钥与强制代理
**Reason**: 存在重大安全与可移植性风险  
**Migration**: 从环境变量读取；默认不启用 LLM；示例不再写死代理与密钥

#### Scenario: 代码安全审计
- **WHEN** 检查 `config.py` 与 `main.py`
- **THEN** 不存在硬编码 Token/Key/内网代理的字面值

### Requirement: 运行时因缺失 LLM 密钥而中止
**Reason**: 可用性差；抓取与摘要应解耦  
**Migration**: 无密钥时跳过摘要但不影响抓取与保存

#### Scenario: 无 LLM 时运行
- **WHEN** 未配置 LLM 密钥
- **THEN** 整体流程完成抓取与 Markdown 保存
- **AND** 日志提示“跳过摘要”


