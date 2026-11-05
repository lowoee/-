# 经验数据结构与设计理由

每条经验遵循仓库的JSON Schema。检索条件、可执行检查与出处分别存放，避免一句泛化原则承担所有作用。

|字段|内容|设计理由与实际使用|
|---|---|---|
|id|稳定经验ID|审查JSON引用、去重和修订追踪。保留FT的p编号及团队定位编号。|
|title|短标题|便于检查检索轨迹和人工阅读。|
|statement|独立可理解的规则|提供给Agent的核心判断依据。|
|status|active、reference_only、superseded、needs_review或rejected|明确旧规范、未核查定义和否决提案的生命周期，默认只检索active。|
|scope.organization|组织或any|把团队私有约定限制在明确适用组织。|
|scope.families|统计图、信息图或any|避免统计图被错误要求遵循手机信息图样式。|
|scope.media|手机、桌面、大屏或any|保存PC大屏例外，未知媒介不默认为手机。|
|scope.categories|时间、组成、数量等任务类别|程序按结构和用途过滤，减少无关上下文。|
|scope.conditions|自然语言适用条件|存放5倍、柱形、非零折线轴等条件。当前由Agent判断。|
|scope.exceptions|限制和例外|防止把经验扩展成来源未支持的普遍禁令。|
|check.question|检查问题|将原则转换为可询问的审查动作。|
|check.evidence_needed|所需材料|提醒必须同时核对图片、数据与规格。|
|check.pass_condition|通过条件|允许不适用或无问题，减少为了匹配规则而过度报错。|
|check.fail_condition|判错条件|要求存在可定位的具体违反证据。|
|check.action|修改方向|给出与经验对应的修订动作。|
|retrieval.keywords|语义标签和关键词|为检索说明和后续检索改进保留索引信息。当前主要用categories，不伪称已有向量检索。|
|retrieval.priority|0至100排序值|明确决议优先展示；不通过排序值静默删除其他适用条目。|
|validity.effective_from|生效日期或null|让人和Agent理解时效；FT不虚构未知发布日期。|
|validity.authority|公开资料、团队规范、明确决议、模板快照等|表达来源权威差异，代码快照只作现状证据。|
|relations.overrides|被该条覆盖的ID|保留新旧冲突的具体对象。|
|relations.exceptions_to|该条构成例外的ID|表达局部例外，避免把适用范围不同的规则整体废止。|
|relations.duplicates|语义重复的ID|为后续跨源归并保留显式关系。当前FT与团队同向规则保留各自出处。|
|evidence.source_id|来源清单中的ID|将经验与具体版本文件关联。|
|evidence.start_line/end_line|来源起止行|本地可直接核查，构建器自动定位。|
|evidence.quote|逐字原文片段|构建时验证确实存在，防止臆造引文。|
|evidence.interpretation|必要解释|区分来源说法与蒸馏者的解释。|
|provenance.method|转换或人工审阅方式|诚实记录哪一步有人工判断，哪些是确定性处理。|
|provenance.evaluation_dependent|是否依赖调试集答案|为导入条目提供检索保护，标记为 true 的记录会被排除。|
|provenance.converted_from|原skill卡相对路径|保留从原skill结构到经验条目的迁移轨迹。|

## 来源清单

`sources/manifest.json`记录每个来源的ID、相对路径、标题、类型、SHA-256、局限与是否属于评测材料。FT主来源另有固定提交、链接和授权范围说明。所有可核查文件均在sources目录，构建不需要连接网络。

## Agent使用方式

一次审查先分析图表用途、家族、媒介和类别，过滤经验状态与组织范围，再提供当前范围内的全部条目。

统计图按通用规则审查。手机信息图收到手机标题规则，PC 大屏收到大屏例外。状态筛选会排除 superseded 的旧断轴要求和 rejected 的删除标注提案。

模型判断后的每条问题必须引用已提供ID，程序再次验证该ID集合。图中具体问题的证据写在输出的evidence，经验来源写在库中evidence，两者承担不同职责。
