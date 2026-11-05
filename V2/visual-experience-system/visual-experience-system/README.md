# 可视化经验蒸馏与审查系统

本仓库把已蒸馏的FT Visual Vocabulary能力卡和团队文档转换为可追溯经验库，再按图表场景提供给一个读取PNG的审查Agent。默认使用本机Codex CLI的登录凭据，通过独立临时配置执行。

当前交付包含构建和审查代码、完整经验库、来源快照、Schema、字段设计说明，以及本次12张图的审查JSON。按用户后续要求，本次只交自己的这一组结果。五组基线对比尚未执行。

## 环境与安装

需要Python 3.10及以上、jsonschema，以及已经登录的Codex CLI。进入仓库根目录执行以下命令。

```powershell
python -m pip install -e .
python -m vizexp build
python -m vizexp validate
```

此仓库按源码或editable方式使用，来源和Schema从仓库路径读取。没有配置将资料打入独立wheel。

## 构建经验库

```powershell
python -m vizexp build --sources sources --output knowledge/experiences.json
```

构建流程如下。

1. 读取来源清单，检查每个来源文件的SHA-256。
2. 从FT能力卡的规则表提取稳定ID、中文规则、类别和限制，回到固定提交README定位原文。
3. 合并人工审阅的团队规范与决议转换种子，计算出处行号并核查逐字引文。
4. 校验Schema、ID唯一性、来源关系和经验间引用，排除没有出处或来源已改变的构建。
5. 原子写入JSON。构建失败时保留此前完整经验库。

现有库共94条，其中83条active、5条superseded、2条reference_only、3条needs_review、1条rejected。64条FT规则与1条技能契约参与有效经验，另有18条有效团队规则。

`sources/curated.json`是人工审阅后的转换记录。`tools/prepare_sources.py`保存这些记录的生成逻辑，并能重建来源哈希清单。新增或修改来源时，应先人工核对规则含义、适用范围与冲突，再修改转换种子或生成逻辑并重建。该入口对当前来源做可重复转换，尚未实现对任意新书或任意网页的自动模型抽取。

## 运行审查

审查一个图表目录或包含多个图表子目录的目录。

```powershell
python -m vizexp review "D:\path\to\charts" --output results/new-review.json
```

目录使用下列文件名。

```text
chart-directory/
  chart.png
  brief.md
  data.csv
  spec.vl.json 或 source.html
```

程序把PNG作为图像输入，同时提供用途、完整CSV和图形源码。`reference.md`及其他参考答案不会被读取。HTML与图形源码只作为文本材料，不执行脚本。输出中每条issue都必须引用本次检索到的有效经验ID。缺少经验依据或精度有疑问的可见现象写入`observations`，避免编造来源。

```json
{
  "chart_id": "example",
  "issues": [
    {
      "description": "具体问题",
      "experience_ids": ["p45"],
      "severity": "high",
      "location": "纵轴",
      "suggestion": "按规则修正",
      "evidence": ["图片中轴起点与规格中的数值范围"]
    }
  ],
  "observations": []
}
```

批量输出另有`planned_count`、`completed_count`和`errors`。单图失败会记录错误，继续处理其余图，进程以2退出并标记incomplete。每张图的检索轨迹、提示、模型事件与实际回答保存在输出文件同名的`_traces`目录。

可选参数如下。

```powershell
# 只查看检索结果，不调用模型
python -m vizexp retrieve "D:\path\to\charts" --output results/retrieval.json

# 生成模型任务包，不把任务准备误报为实际审查
python -m vizexp review "D:\path\to\charts" --output results/prepared.json --prepare-only

# 显式指定组织、CLI或模型
python -m vizexp review "D:\path\to\chart" --organization team-finance --codex "C:\path\codex.exe" --model YOUR_MODEL --output results/review.json
```

`organization=auto`只在HTML信息图且其上级存在团队资料包，或brief声明`团队规范：team-finance`时启用团队规则。其他目录可显式指定组织。手机、桌面和大屏从brief识别，未知媒介不会自动套用手机专属规则。

审查使用临时CODEX_HOME和每图独立临时工作目录。同一批次临时复制一次当前auth.json以复用用户登录，批次结束后删除。它不载入全局已安装技能或用户配置，避免未记录经验混入。自定义模型提供方配置尚未迁移，仅支持当前标准Codex登录或OPENAI_API_KEY路径。可通过`--model`指定可用模型。真实PNG会提交给当前模型服务，请在获准使用这些图片的环境中运行。

## 经验Schema与Agent用法

完整定义在`schemas/experience.schema.json`，字段逐项理由在`docs/SCHEMA.md`。每条经验必须带来源ID、起止行、逐字引文与必要的解释。来源清单含相对路径、文件哈希、FT固定提交和公开链接。

检索先排除过时、被否决、待核查和依赖调试集答案的记录，再按组织、图表家族、媒介和任务类别过滤。有效范围内的规则全部提供给Agent，当前没有任意top-k截断。自然语言条件和例外由Agent结合PNG与数据判断，程序尚未将其全部编译为可计算谓词。

三项needs_review记录的名称和状态另作为来源边界提示提供，不能作为有效执行经验引用。缺少源码而无法确定图表家族时，不默认启用团队信息图要求。

目前结构信号检索属于启发式。它根据Vega-Lite标记、字段类型、用途文本和HTML语义选择类别，未训练图像分类器。复杂或陌生布局可能漏检，检索轨迹用于检查哪些经验被提供、哪些被排除。

## 来源选择和冲突处理

FT提供图形任务分类和可追溯的选型边界。团队资料补足模型无法从通用训练知道的组织约定，包含手机小标题、间距、金额精度、单位、颜色、来源行与涨跌习惯。

团队规则的处理基于明确声明和适用范围。v2修改项覆盖v1，未修改项继承；明确决议可撤销旧条款；PC大屏例外保留媒介条件。旧模板是实现快照，代码里的常量不会自动覆盖后续决议。被否决提案和个人审美偏好不晋升为规范。

例如非零折线轴的旧断轴要求为superseded，保留出处和被覆盖关系。手机标题规则与PC大屏例外分开表达，避免只按日期把手机要求整体废止。原文中的5倍阈值属于该团队，不扩展为所有图表的通用规则。

未采用新书全文或额外网络抓取。FT来源存在仓库MIT与子目录保留版权声明的范围问题，公开发布材料前须核对授权。当前按本地交付保留来源声明，未代用户发布到GitHub。

## 本次结果与验证

`results/chart-review-ft-vocabulary.json`逐字节保留用户指定的原结果，覆盖12图，共19项确认问题、1项待核查，chart-02、chart-05、chart-20没有确认问题。

这份历史结果来自此前结合图片、数据、源码、参考意见和团队材料开展的人工与Agent联合审查。它包含从调试集整理的补充观察，属于开发阶段的结果。五条 `audit-*` 记录已从经验库和构建来源删除。历史结果内的引用由随附的 `experience_catalog` 解释。

验证命令如下。

```powershell
python -m unittest discover -s tests -v
```

回归检查覆盖可重复构建、全部引文定位、手机与大屏例外、统计图不套团队约定、过时及答案衍生经验排除，以及未见目录名和reference.md指令隔离。实际命令验证见`docs/VALIDATION.md`。

## 已知局限

- 五组基线对比按用户当前范围暂未运行，没有相对基线的提升结论。
- FT的p24、p35、p38操作定义仍待核查，归档保留，不进入有效检索。
- 缺少独立配色和多线识别来源时，新Agent可记录待核查观察，不能冒充FT规则。
- 模型语义判断存在随机性，Schema和引用校验能约束结构及ID，不能代替逐条审查结论核实。
- 文本大小限制4MiB，未实现超大数据采样或分块。PNG大小由CLI与模型限制。
- 目录和提示隔离减少知识污染，未实现OS级独立安全沙箱；Codex模型子进程使用read-only权限。
