# 设计：get_sdk_release_change_log 大重构

## 背景与问题
现状具备基础可用性，但存在如下关键问题：
- 安全：存在硬编码密钥与代理示例，风险高；凭据与代理应仅由环境变量提供。
- 可用性：LLM 未配置即抛错，抓取与摘要强耦合；示例入口绕过 CLI 参数且内联 GitHub Token。
- 一致性：输出命名与幂等缺乏严格约束；日志可能冗长且潜在泄密。
- 可靠性：对 GitHub 限额与网络故障的降级策略需要明确；缺少断点续跑与页面级幂等。
- 可维护性：模块边界模糊，测试与替换（如 LLM 提供方）成本较高。

## 目标与非目标
### 目标
- 安全默认：不硬编码任何密钥或代理；无 LLM 时完整抓取流程仍可运行。
- 产品化 CLI：参数化入口，覆盖仓库、分页、起始页、模型、Token 等。
- 稳定输出：统一 UTF-8；`data/releases` 与 `data/summaries` 固定目录；命名规范与幂等。
- 可靠网络：限速、超时、重试、退避；命中限额时稳健退避；报错清晰。
- 可观察：最小化但清晰的日志；敏感信息打码；基本运行指标。
- 易扩展：总结模块抽象成接口；支持 DeepSeek(OpenAI 兼容) 或禁用。
- 可测试：HTTP 层可 mock；文件输出可金样校验；流水线 E2E 可录制。
- 运行方式：推荐使用 uv 管理虚拟环境与依赖。

### 非目标
- 不引入数据库存储，维持文件系统输出。
- 不实现多仓库聚合与跨项目报告（可在后续扩展）。
- 不在本次变更中加入复杂并发抓取（默认串行，保留接口与配置以便扩展）。

## 架构概览
流水线分层：
1) CLI 层：参数解析、环境变量回退、输入校验、打印关键输出路径。
2) Crawler 层：分页抓取 Releases → 生成页面级 Markdown。
3) Summarizer 层：可选的分段摘要与总览汇总；无密钥则整个摘要阶段跳过。
4) Storage 层：路径与命名规范、UTF-8 编码、存在且非空不覆盖（幂等）；后续预留 `--force`。
5) Infra 层：HTTP Session、认证头、超时、重试、退避、速率控制；日志与指标。

依赖方向：CLI → Crawler → Storage；CLI → Summarizer → Storage；Infra 被 Crawler 与 Summarizer 复用。

## 模块设计
### 1. 配置模块 `config`
- 仅从环境变量读取密钥与代理：`DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY`、`GITHUB_TOKEN`、`HTTP(S)_PROXY`。
- 默认不设置或覆盖代理变量；保留用户环境值。
- 可配置项：请求超时、重试次数、请求间隔、每页数量、最大页数、LLM 模型、分段策略等。

### 2. HTTP 与 GitHub 访问 `src/crawler.py`
- 使用 `requests.Session`，设置标准 UA；若提供 Token 则附带认证头。
- `_request(url, params)` 内部重试：
  - 对 `403` 且包含 `rate limit` 触发指数退避。
  - 其他临时错误按次数指数退避重试，最终抛出最后异常。
- `fetch_releases_page(page)`：返回 `List[ReleaseItem]`，字段覆盖 id、tag、name、body、html_url、published_at。
- `save_page_markdown(page, items)`：
  - 路径：`data/releases/<repo_slug>_<page>.md`
  - UTF-8 写入；若文件存在且非空则直接返回（幂等）。

### 3. 摘要抽象与实现 `src/llm_client.py`
- 接口形态：
  - `available() -> bool`：是否可用（检测密钥）。
  - `summarize(text, system_prompt) -> str`：单段摘要。
  - `summarize_long(content) -> list[str]`：分段摘要（按 “## ” 版本段聚合）。
  - `summarize_aggregate(chunks) -> str`：汇总。
- DeepSeek(OpenAI 兼容) 实现：
  - 从环境变量读取 API Key 与 Base URL。
  - 超时、重试、RateLimit 处理；温度与 tokens 受配置控制。
- 调用侧逻辑：若 `available() == False`，则跳过摘要阶段，保留抓取文件与日志提示。

### 4. CLI 入口 `src/main.py`
- 参数：`--repo` 必填，`--max-pages`、`--start-page`、`--model`、`--gh-token` 可选；`--gh-token` 默认为 `GITHUB_TOKEN` 环境变量。
- 运行流程：
  - 校验目录与参数 → 分页抓取 → 写入页面 Markdown → 若 LLM 可用则摘要并写入 `_summary.md`。
- 输出路径：
  - Releases：`data/releases/<repo_slug>_<page>.md`
  - Summaries：`data/summaries/<repo_slug>_<page>_summary.md`
- 日志：打印页级结果路径；不打印凭据；错误输出包含上下文但隐去敏感字段。

### 5. 存储与命名规范
- 目录固定：`data/releases`、`data/summaries`；UTF-8。
- 文件命名稳定：`<repo_slug>_<page>.md` 与 `<repo_slug>_<page>_summary.md`。
- 幂等写入：存在且非空不覆盖；后续支持 `--force`（暂不实现）。

### 6. 可靠性与限额处理
- `403 rate limit`：指数退避，打印提示；最终失败时抛出明确异常。
- `timeout/retry`：在 `_request` 内统一处理；重试次数与延迟可配。
- 速率控制：请求间固定延迟，默认 1s，可配。
- 断点续跑：基于“存在且非空即跳过”的幂等策略实现页面级复跑。

### 7. 日志与基本指标
- 日志等级：INFO 为主，ERROR 在失败时；DEBUG 预留。
- 打码规则：Token、Key 只显示前后各3位，中间以 `***` 替代。
- 指标：页数、成功数、失败数、重试次数、总时长；以简洁文本输出。

### 8. 数据模型
```text
ReleaseItem
- id: int
- tag_name: str
- name: str
- body: str
- html_url: str
- published_at: str  # ISO8601 入, 输出人类可读
```

可选：`SummaryResult`（若未来需要结构化导出）
```text
SummaryResult
- page: int
- chunks: list[str]
- final_summary: str
```

## 关键用例与时序
1) 无 LLM 密钥：
   - 抓取 → 写入页面 Markdown → 打印“跳过摘要” → 退出码 0。
2) 有 LLM 密钥：
   - 抓取 → 写入页面 Markdown → 分段摘要 → 汇总 → 写入 `_summary.md` → 退出码 0。
3) 命中限额：
   - 抓取某页时 403 且包含 rate limit → 退避重试 → 成功则继续，失败则报错并退出码非 0。

## 测试策略
- 单元测试：
  - Crawler `_request` 的退避分支与错误分支（mock `requests.Session.get`）。
  - `fetch_releases_page` 的解析健壮性（无字段、空列表）。
  - Storage 幂等：存在且非空文件时不覆盖。
  - Summarizer 分段切分与可用性检测 `available()`。
- 集成测试：
  - CLI E2E：无密钥与有密钥两条路径；校验输出文件存在且内容基本格式正确。
  - 金样：示例仓库的第一页 Markdown 与摘要进行“包含关键段落”的断言（避免完全相等导致脆弱）。
- 可选：VCR 录制 HTTP 交互以稳定回放。

## 迁移计划
- 移除硬编码代理与密钥；更新 README 说明通过环境变量提供。
- 恢复并推广 CLI 参数；删除 main 中的内联 Token 示例。
- 对现有数据目录无破坏性变更；若已有相同命名文件则不覆盖。
- 发布后在 `openspec` 中归档该变更；后续可追加 `--force` 与并发抓取的增强提案。

## 风险与缓解
- GitHub 变更 API 限额策略：通过重试与速率控制缓解；必要时降低并发与页数。
- 长页面摘要超出上下文：按“版本段”聚合分段，减少单请求体积；必要时调整 `versions_per_chunk`。
- 代理环境差异：不强制设置代理，完全依赖用户环境；在 README 列出常见代理配置示例。

## 打开问题
- 是否需要为每条 Release 生成独立 Markdown（当前为页级），或同时输出两种粒度？
- 是否需要结构化 JSON 导出摘要结果，支持后续下游处理？
- 是否需要引入简单的并行抓取开关（限额友好的范围内，如2-3并发）？


