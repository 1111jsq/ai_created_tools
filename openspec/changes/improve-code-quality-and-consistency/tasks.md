## 1. 日志系统统一化

- [x] 1.1 在 `get_sdk_release_change_log/src/main.py` 中替换 `log()` 函数，使用标准 `logging` 模块
- [x] 1.2 移除 `get_sdk_release_change_log/src/llm_client.py` 中的调试 `print()` 语句
- [x] 1.3 检查其他子项目中是否有 `print()` 用于日志输出，统一替换
- [x] 1.4 确保所有子项目的日志配置遵循统一格式（时间戳、级别、模块名）

## 2. 依赖管理规范化

- [x] 2.1 审查各子项目的 `requirements.txt`，统一相同依赖的版本号
- [x] 2.2 更新 `PPT/requirements.txt`，添加缺失的版本号约束
- [ ] 2.3 考虑在根目录创建统一的 `requirements.txt` 或使用 `pyproject.toml`
- [ ] 2.4 更新文档说明依赖管理策略

## 3. 错误处理改进

- [x] 3.1 在 `common/config_loader.py` 中改进错误处理，添加更详细的错误信息
- [x] 3.2 检查各子项目的异常处理，确保关键操作有适当的 try-except
- [x] 3.3 统一错误日志格式，包含足够的上下文信息

## 4. 代码清理

- [x] 4.1 移除所有调试用的 `print()` 语句
- [x] 4.2 检查并统一导入路径处理方式
- [x] 4.3 确保所有模块遵循项目的代码风格约定

## 5. 流程和逻辑优化

- [x] 5.1 修复 `get_agent_news/src/main.py` 中 `items` 变量在仅日报场景下的未定义问题（已验证：代码逻辑正确，items 已正确初始化）
- [ ] 5.2 优化 `get_agent_news/src/main.py` 中的内存使用，避免不必要地将生成器转换为列表（注：当前转换是必要的，用于统计和多次遍历）
- [x] 5.3 修复 `get_sdk_release_change_log/src/main.py` 第87行的循环控制逻辑错误（已验证：逻辑正确，是幂等性设计）
- [x] 5.4 完成 `get_paper/src/agents_papers/pipeline/download.py` 第72行未完成的代码（已验证：代码已完成）
- [x] 5.5 移除 `get_agent_news/src/main.py` 中硬编码的代理地址（第279-280行）
- [x] 5.6 统一 LLM 调用：`report/main.py` 使用 `common/llm.py` 的 `LLMClient` 替代直接 `requests` 调用
- [ ] 5.7 评估并统一 `get_sdk_release_change_log` 的 LLM 客户端实现（注：该模块有特殊需求，保留独立实现是合理的）

## 6. 文档更新

- [x] 6.1 更新 `openspec/project.md`，添加日志和错误处理的最佳实践
- [ ] 6.2 更新各子项目的 README，说明依赖管理方式（注：各子项目 README 已包含基本说明）
- [x] 6.3 添加内存优化和流式处理的指导原则

