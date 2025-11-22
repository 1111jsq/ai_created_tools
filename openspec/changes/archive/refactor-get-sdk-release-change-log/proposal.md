# Change: 重构 get_sdk_release_change_log，安全配置、可选 LLM、稳定输出与 CLI 恢复

## Why
当前实现存在硬编码密钥与代理、示例入口禁用了 CLI 参数并直接嵌入 GitHub Token，且 LLM 未配置时直接抛错，易导致安全与可用性问题；输出命名与行为亦缺少规范与幂等约束。

## What Changes
- 安全配置
  - 移除所有硬编码密钥（DeepSeek/OpenAI、GitHub Token）与强制代理设置，仅从环境变量读取；默认不启用 LLM。
  - DeepSeek 客户端在未配置密钥时不抛错，摘要流程退化为跳过但保留抓取产物。
- CLI 恢复与参数化
  - 恢复 `--repo/--max-pages/--start-page/--model/--gh-token` 等参数入口，移除示例中的内联 Token。
- 稳定与幂等输出
  - 产出目录固定为 `data/releases` 与 `data/summaries`，UTF-8 编码；
  - Markdown 命名遵循 `<repo_slug>_<page>.md`，总结命名 `<repo_slug>_<page>_summary.md`；
  - 已存在且非空文件默认不覆盖；提供可选覆盖开关（后续实现）。
- 网络鲁棒性
  - 保持限速/超时/重试策略；GitHub 限额时优先退避；GitHub Token 存在时附带认证头。
- 日志与可观测性
  - 仅打印最小必要日志，不暴露凭据。

## Impact
- Affected specs: `specs/sdk-release-changelog/spec.md`
- Affected code:
  - `get_sdk_release_change_log/config.py`
  - `get_sdk_release_change_log/src/main.py`
  - `get_sdk_release_change_log/src/llm_client.py`
  - `get_sdk_release_change_log/src/crawler.py`（输出与幂等约束说明）


