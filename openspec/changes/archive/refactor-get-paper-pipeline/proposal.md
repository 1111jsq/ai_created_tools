# Change: 重构 get_paper 管道与配置（安全、CLI 与可维护性）

## Why
当前 `get_paper` 代码存在硬编码密钥与代理、参数通过源码内写死、不够清晰的运行入口等问题，给使用安全性、可维护性与可移植性带来风险。需要一次小步重构以提升安全、易用与稳健。

## What Changes
- 移除硬编码的 DeepSeek API Key 与默认企业代理，统一改为通过环境变量读取（未设置则安全跳过相关能力）
- 为 `src/monthly_run.py` 增加标准 CLI 参数（`--month` 或 `--start/--end`），去除源码内写死的日期窗口
- 保持 OpenReview v2 为优先，失败时回退 v1（已有能力，纳入规范要求）
- 保持现有导出（JSON/CSV/MD、统计、Top/Ranked、综合报告），并对 PDF 下载的稳健性与清单持久化提出明确要求
- 文档更新：补充 uv 虚拟环境用法与 CLI 示例

不涉及破坏性接口调整，保留现有目录与产物结构。

## Impact
- Affected specs: `papers-etl`
- Affected code:
  - `get_paper/src/agents_papers/config.py`
  - `get_paper/src/monthly_run.py`
  - `get_paper/README.md`
  - 相关说明：`agents_papers/sources/*`, `agents_papers/pipeline/*`, `agents_papers/analysis/*`（行为保持一致）


