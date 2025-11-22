## 1. 安全与配置
- [ ] 1.1 从 `get_sdk_release_change_log/config.py` 移除硬编码密钥（DeepSeek/OpenAI）与强制代理设置；仅读取环境变量
- [ ] 1.2 在 README 中明确代理、密钥的环境变量配置方式；不提供默认内网代理
- [ ] 1.3 `src/llm_client.py`：当缺失密钥时不抛错，提供 `available()`/或由调用方安全跳过摘要

## 2. CLI 恢复与参数化
- [ ] 2.1 恢复 `src/main.py` 的 argparse 参数：`--repo --max-pages --start-page --model --gh-token`
- [ ] 2.2 移除示例中的内联 GitHub Token；默认从环境变量读取或通过参数传入
- [ ] 2.3 打印最小必要日志与结果路径，避免泄露敏感信息

## 3. 稳定与幂等输出
- [ ] 3.1 统一输出到 `data/releases` 与 `data/summaries`，UTF-8 编码
- [ ] 3.2 文件命名：`<repo_slug>_<page>.md` 与 `<repo_slug>_<page>_summary.md`
- [ ] 3.3 已存在且非空文件默认不覆盖（预留 `--force` 开关，后续实现）

## 4. 网络鲁棒性
- [ ] 4.1 保持请求重试、超时、延迟策略；命中 GitHub 限额时指数退避
- [ ] 4.2 当提供 `--gh-token` 或 `GITHUB_TOKEN` 时，附带认证头；否则匿名调用

## 5. 文档与验证
- [ ] 5.1 更新 `get_sdk_release_change_log/README.md`：使用 uv 的最小示例、CLI 参数说明、安全注意事项
- [ ] 5.2 本地验证：`uv run python -m src.main --repo langchain-ai/langchain --max-pages 1`
- [ ] 5.3 验证无 LLM 密钥时流程可用，且仅跳过摘要；有密钥时生成 `_summary.md`
- [ ] 5.4 通过严格校验：`openspec validate refactor-get-sdk-release-change-log --strict`

## 6. 交付
- [ ] 6.1 提交变更并推送
- [ ] 6.2 待评审通过后执行实现，实施完成后归档该变更


