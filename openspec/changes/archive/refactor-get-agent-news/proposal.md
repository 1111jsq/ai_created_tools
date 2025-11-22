# Change: 重构 get_agent_news，移除无用代码与历史依赖，简化配置与导出

## Why
当前 `get_agent_news` 中仍残留数据库备份、可选调度器、未使用的类型别名与若干不再需要的工具函数，以及不安全的默认 LLM API Key 等历史代码与配置。这些内容增加了维护与认知成本，并带来潜在安全隐患与误用风险。

## What Changes
- 移除历史数据库相关逻辑：
  - 移除 `src/config.get_db_path` 与 `DEFAULT_DB_PATH`，以及主流程中的数据库备份函数与调用。
  - 移除 `src/main.py` 中 `backup_database_data` 与相关导入。
- 移除未使用模块/函数：
  - 删除 `src/storage/typing_aliases.py`。
  - 删除 `src/schedule/weekly.py`（库内不再内置调度，推荐外部调度器）。
  - 精简 `src/tools/date_structure.py`，仅保留 `ensure_date_structure` 与必要路径函数。
- 安全化配置：
  - 从 `src/config.get_deepseek_config` 移除硬编码的默认 API Key，默认置空；仅在设置环境变量时启用 LLM。
- 一致化与最小化导出：
  - Markdown 导出与索引构建统一使用空格缩进（去除混用 Tab），文件命名保持 `news-YYYY-MM-DD-<slug>-<hash8>.md`。
- 代码风格与日志：
  - 统一日志标签与关键路径的提示信息；维持现有 CLI 与行为不变。

## Impact
- Affected specs: `specs/agent-news/spec.md`
- Affected code:
  - `get_agent_news/src/main.py`
  - `get_agent_news/src/config.py`
  - `get_agent_news/src/storage/typing_aliases.py`（删除）
  - `get_agent_news/src/schedule/weekly.py`（删除）
  - `get_agent_news/src/tools/date_structure.py`（精简）
  - `get_agent_news/src/pipelines/markdown_*.py` 与 `src/tools/slugify.py`（缩进统一）
  - LLM 启用逻辑仅由 `DEEPSEEK_API_KEY` 控制，默认关闭


