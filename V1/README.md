# V1 团队经验 + Datawrapper 经验

V1 使用两个已审阅来源。团队经验来自原交付 ZIP 的团队资料和转换种子，经逐项核对、归并、处理冲突后保留 18 条有效经验。Datawrapper 使用此前归并发布的 30 条经验，保留 EXP-001 至 EXP-030 和上游出处。

| 文件 | 用途 |
| --- | --- |
| sources/team/ | 六份团队文档的原交付快照 |
| sources/curated.json | 团队规则提取记录 |
| sources/datawrapper-review-30.json | Datawrapper 已发布的 30 条经验，保留来源 URL、定位、引文和适用变体 |
| sources/datawrapper-review-30.manifest.json | 上游发布清单，含经验 ID 和 SHA-256 |
| sources/manifest.json | V1 的来源路径和 SHA-256 |
| knowledge/experiences.json | 合并的审查经验库，含 60 条记录，其中 48 条有效 |
| 冲突处理.md | 版本、例外和跨来源适用边界 |
| 联合审查/ | V1 的检索、逐图运行记录和联合审查结果 |
| 审查结果/ | 本次合并之前的团队规则单独运行记录 |

统计图只加载 30 条 Datawrapper 经验。测试集内四张手机信息图同时加载 30 条 Datawrapper 经验及 17 条手机适用的团队经验，PC 大屏例外按媒介检索。条件和例外由模型依据实际图面、数据和源码判断。确认问题必须引用能够直接支持它的经验 ID，缺少适用经验或证据的现象放入 observations。

团队规则的语义提取由人工审阅方式完成，构建命令对记录做确定性转换、校验来源哈希、引用和结构。Datawrapper 来源定位保存在上游快照中，本次校验上游快照与发布清单一致。历史审查结果、FT 规则和调试答案未作为审查输入。

需要 Python 3.10+、jsonschema 和已登录的 Codex CLI。从本目录运行：

```powershell
python -m pip install -e .
python -m vizexp build
python -m vizexp validate
python -m vizexp review "../测试集" --organization team-finance --output "联合审查/复跑.json"
```

审查逐图创建独立会话，输入实际 PNG、用途、CSV、源码和适用经验。若需与基线做受控对比，用 --model 指定同一可用模型并统一其他运行条件。
