## ADDED Requirements

### Requirement: 博客文章爬取
系统 SHALL 能够从配置的博客网站抓取文章列表和详情内容。

#### Scenario: 从 RSS feed 抓取文章
- **WHEN** 博客源配置了 RSS URL
- **THEN** 系统使用 RSS/Atom feed 解析器抓取文章列表
- **AND** 提取每篇文章的标题、链接、发布时间、摘要等信息
- **AND** 抓取每篇文章的详情页内容（如果 RSS 中未包含完整正文）

#### Scenario: 从 HTML 页面抓取文章
- **WHEN** 博客源未配置 RSS URL 或 RSS 解析失败
- **THEN** 系统使用 HTML 解析器抓取列表页
- **AND** 根据配置的选择器提取文章链接
- **AND** 支持翻页功能（next、param、page_links 三种模式）
- **AND** 抓取每篇文章的详情页并提取标题、正文、作者、发布时间等信息

#### Scenario: 遵守礼貌爬取规范
- **WHEN** 开始抓取博客源
- **THEN** 系统检查目标网站的 robots.txt（如果存在）
- **AND** 遵守 robots.txt 中的规则
- **AND** 在请求之间添加配置的延迟时间（默认 1.0 秒）
- **AND** 设置合理的 User-Agent 和超时时间（默认 30 秒）

### Requirement: 内容格式转换
系统 SHALL 将抓取的 HTML 内容转换为 Markdown 格式。

#### Scenario: HTML 转 Markdown
- **WHEN** 抓取到文章的 HTML 内容
- **THEN** 系统使用 HTML 转 Markdown 转换器处理内容
- **AND** 保留代码块、链接、图片、列表等关键格式
- **AND** 清理多余的空白和格式
- **AND** 将相对链接转换为绝对链接

### Requirement: 文件存储管理
系统 SHALL 将抓取的文章保存为 Markdown 文件，并按日期和来源组织目录结构。

#### Scenario: 按日期和来源组织文件
- **WHEN** 保存文章到文件系统
- **THEN** 文件路径格式为 `data/exports/<timestamp>/markdown/<source>/<YYYY>/<MM>/<DD>/<slug>.md`
- **AND** 文件名使用文章的 slug（从标题或 URL 生成）
- **AND** 文件内容包含文章元数据（标题、作者、发布时间、来源、标签等）和正文

#### Scenario: 幂等性支持
- **WHEN** 重复运行爬虫
- **THEN** 系统基于 URL hash 判断文章是否已抓取
- **AND** 已存在的文章默认不重复抓取（除非指定 `--overwrite`）
- **AND** 避免重复的网络请求和文件写入

### Requirement: 多源配置管理
系统 SHALL 支持通过 YAML 配置文件管理多个博客源。

#### Scenario: 加载博客源配置
- **WHEN** 启动爬虫
- **THEN** 系统从 `configs/blogs.yaml` 加载博客源配置
- **AND** 支持配置博客 URL、类型（RSS/HTML）、选择器、翻页规则、延迟等参数
- **AND** 支持通过 `--source` 参数指定单个博客源
- **AND** 验证配置格式，提供清晰的错误信息

#### Scenario: 配置驱动的爬取
- **WHEN** 配置了多个博客源
- **THEN** 系统依次处理每个博客源
- **AND** 根据配置的类型（RSS/HTML）选择相应的解析器
- **AND** 根据配置的选择器提取文章信息
- **AND** 根据配置的翻页规则处理多页内容

### Requirement: 错误处理与容错
系统 SHALL 优雅处理各种错误情况，确保部分失败不影响整体运行。

#### Scenario: 网络错误处理
- **WHEN** 网络请求失败
- **THEN** 系统实现重试机制（最多 3 次）
- **AND** 记录失败的 URL 和错误信息
- **AND** 继续处理其他文章或博客源

#### Scenario: 解析错误处理
- **WHEN** HTML 解析或内容提取失败
- **THEN** 系统跳过该文章并记录警告日志
- **AND** 继续处理其他文章
- **AND** 在最终统计中报告失败数量

#### Scenario: robots.txt 禁止处理
- **WHEN** robots.txt 禁止访问目标路径
- **THEN** 系统跳过该博客源并记录警告
- **AND** 继续处理其他博客源

### Requirement: CLI 接口
系统 SHALL 提供命令行接口，支持灵活的配置和运行选项。

#### Scenario: 基本运行
- **WHEN** 运行 `uv run python -m get_blog_posts.src.main`
- **THEN** 系统使用默认配置抓取所有博客源
- **AND** 将结果保存到默认输出目录

#### Scenario: 指定博客源
- **WHEN** 使用 `--source langchain` 参数
- **THEN** 系统仅抓取指定的博客源
- **AND** 忽略其他博客源配置

#### Scenario: 覆盖已存在文件
- **WHEN** 使用 `--overwrite` 参数
- **THEN** 系统覆盖已存在的文章文件
- **AND** 重新抓取和保存内容

