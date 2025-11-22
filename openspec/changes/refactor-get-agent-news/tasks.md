## 1. 移除历史依赖与无用代码
- [ ] 1.1 删除 `get_agent_news/src/storage/typing_aliases.py` 并清理所有引用（预计无直接引用）
- [ ] 1.2 删除 `get_agent_news/src/schedule/weekly.py`（库内不再内置调度）
- [ ] 1.3 从 `get_agent_news/src/config.py` 中移除 `DEFAULT_DB_PATH` 与 `get_db_path`；保留 `get_sources_path`、`get_log_path`
- [ ] 1.4 删除 `get_agent_news/src/main.py` 中 `backup_database_data` 函数与所有 DB 备份调用
- [ ] 1.5 精简 `get_agent_news/src/tools/date_structure.py` 仅保留 `ensure_date_structure` 及必要辅助函数

## 2. 安全化 LLM 配置
- [ ] 2.1 将 `get_agent_news/src/config.py` 中 `get_deepseek_config` 的默认 API Key 置空，不再硬编码任何密钥
- [ ] 2.2 确认 `rank.py` 在 `DEEPSEEK_API_KEY` 缺失时严格走启发式分支，不发送任何网络请求

## 3. 一致化导出与风格
- [ ] 3.1 统一 `pipelines/markdown_export.py`、`pipelines/markdown_index.py` 与 `tools/slugify.py` 的缩进为空格（移除 Tab）
- [ ] 3.2 确认 Markdown 文件命名 `news-YYYY-MM-DD-<slug>-<hash8>.md` 生效，标题为空时回退为 `untitled`
- [ ] 3.3 保持 CSV/JSONL/排名导出不变，确保回归兼容

## 4. 文档与示例
- [ ] 4.1 在 `get_agent_news/README.md` 中说明：不再使用数据库；如需定时请使用系统调度器
- [ ] 4.2 提供示例命令（uv run）与最小运行参数说明

## 5. 验证与交付
- [ ] 5.1 本地自测：`uv run python -m src.main --once --source all --news-since-days 2 --export-markdown`
- [ ] 5.2 生成导出目录校验：存在 `news.jsonl/news.csv/markdown/analysis.json/TOP.md/index.md`
- [ ] 5.3 代码静态检查通过（格式/导入/未使用对象）
- [ ] 5.4 提交 PR 并过评审，合入后归档变更


