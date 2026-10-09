# outlier 工作大纲：从选题到 midterm report

日期：2026-10-09。队名：outlier。主题、研究问题、成员分工与 TA mentor 尚未确认。

## 本阶段目标

在 **2026-10-25 下午 5 点**前，把自行编程采集的数据、data dictionary、至少三张 explanatory figures、清晰的 supervised ML 问题与潜在用途，整理成不超过 1500 words 的团队报告，并提交到 Gradescope。期末阶段再完成模型比较、cross-validation、选择与解释。

本文件中的内部日期、建议样本量、分工和文献数量都是工作建议；课程硬性要求以官方 rubric 为准。

## 1. 先确定问题，再扩大采集

选题必须能用一句话说清楚：

> 对于【每行代表的单位】，在【预测时间点】，利用【当时可以获得的 features】，预测【target】，让【用户】可以【采取什么行动】。

先比较 [三个数据候选](../dataset-options.md)。我的初步推荐是芝加哥餐厅例行卫生检查；API 已通过小样本访问检查，有明确 outcome 和官方既有研究。推荐不等于小组已选定。

一个候选应通过以下检查再成为正式主题：

- 能通过真正的 API 查询、分页或其他代码采集获得数据，并保存可重复的采集过程。
- 一行的含义、target 的定义和预测时间点明确；target 可以观测或合理构造。
- 有若干预测时可得的 features，不能让结果、后续处理或未来信息进入 X。
- 小样本检查 ID 重复、字段缺失、类别数量、target 分布、日期与单位。
- 有可以引用的既有工作，能解释模型的用途与限制。
- 范围能在两周内完成。先做一个城市、一类任务、一个 target；第二个数据源作为后续可选扩展。

API 可访问不证明整个数据集干净，也不证明老师一定接受你们的具体采集工作。把采集方案与 target 定义带给 mentor TA，确认范围和合规方式。

## 2. 时间安排和完成标准

| 内部时间 | 工作 | 本阶段完成标准 |
|---|---|---|
| 10/09–10/11 | 比较候选，确定 topic、unit、target、预测时间点；确认成员账号和分工 | 一段团队自己写的研究问题；一个主数据源；一个备选；实际 API 小样本 |
| 10/12–10/15 | 编写正式采集与整理代码，保存原始快照和查询记录 | 分页采集可重跑；记录来源、时间、参数、行数；原始与处理后数据分开；初版 data dictionary |
| 10/16–10/18 | 数据质量检查和 EDA | 检查去重、缺失、target 分布；探索多张图，选择至少三张能讲清信息的图 |
| 10/19–10/21 | 阅读既有研究，团队自己写 report draft | 正文五个指定部分都有内容；引用来源完整；图表都有 caption；target 和 impact 一致 |
| 10/22–10/23 | 交叉检查和复现 | 另一名成员按 README 重跑；public repo、成员、文件路径、字数和图表检查通过 |
| 10/24 | 预留修复与提交缓冲 | 最终 PDF、提交成员信息和 repo 链接准备好；核对 Gradescope 实际提交状态 |
| **10/25，5 pm 前** | 正式提交 | Gradescope 显示成功提交，确认全体队员包含在团队提交中；无 late-day/grace period |

内部日期可以调整，但不能把修复缓冲挤到课程截止后。

## 3. 数据集怎么找

1. 从问题出发，先找数据的原始发布机构，而不是先找 Kaggle 成品表。
2. 搜索“主题 + official API / open data / data dictionary”。优先政府开放数据门户、官方 API 和有结构说明的数据源。
3. 打开 dataset metadata 和 API 文档：确认 access、字段定义、时间覆盖、更新方式、分页、rate limits、许可与归属。
4. 建议先查数百至约 1000 条进行可行性检查；这不是课程规定的样本量。时间顺序取出的前几百行不能当代表性随机样本。
5. 写下 field → meaning → type → unit/categories → target/feature/ID → prediction-time availability。
6. 检查目标类别是否足够、字段是否在预测之后才生成、同一实体是否有多次记录。
7. 选定后再采集正式数据，固定时间范围、过滤规则和快照。仅把现成 CSV 的下载包装为脚本，不足以证明满足“coding effort”；要说明实际采集过程。

## 4. 分工建议

| 工作包 | 负责人待定 | 应交给其他成员的内容 |
|---|---|---|
| 数据采集与 provenance | A | API 查询/分页代码、原始数据、采集参数和快照时间 |
| 清洗与 data dictionary | B | 清洗规则、ID/缺失/target 检查、所有列的定义 |
| EDA 与可视化 | C | 探索图、三张主图、caption 和可复现代码 |
| 文献、报告统筹与复现检查 | D；三人组由 A/B/C 分担 | 文献笔记、结构和字数检查、最终提交核对 |

角色不意味着一个人独自写完整报告。所有人需要理解 target、数据来源、清洗规则和图表；每个工作包由另一人检查。默认团队同分，课程提供可选贡献表；持续记录实际贡献。

## 5. GitHub 中需要逐步补齐的内容

- 成员账号：加入 collaborators。README 写队名、成员、项目问题和 TA mentor。
- `src/`：按采集 → 整理 → EDA → 后期 modeling 的顺序放代码/notebooks。
- `data/`：原始/处理后数据和 data dictionary；数据太大时写准确下载/采集方法。
- `figures/`：报告使用的图及其他探索图。
- `results/`：期末阶段的预测、模型和比较结果。
- `report/`：最终 midterm PDF 和 final presentation slides。
- 环境：现已放入课程环境 YAML；真正运行时记录实际 Python/package versions 和运行顺序。
- 文档：来源、查询参数、过滤/排除规则、日期范围、采集时间。当前只有 API 可行性检查，不能标记“分析已完成”。

## 6. 三张图应该回答什么

选题确定后再定具体图；下面是可用框架：

1. **Target 的分布**：问题是否有足够变化，类别是否不平衡？
2. **一个预测时可得 feature 与 target 的关系**：哪个群体或类别的 outcome 不同？加分母/样本量，不能只展示总数量。
3. **时间变化或另一个重要 feature**：是否存在季节性、变化趋势或需要控制的背景差异？

图上的 headline 必须由实际数据支持。EDA 中的关联不能写成因果效应。

## 7. Midterm 提交前核对

- [ ] 报告开头有 title、全体姓名、affiliation、public GitHub 链接。
- [ ] 按 Introduction、Data、Exploratory Data Analysis、Problem description and potential impact、References 的顺序。
- [ ] 至少三张 explanatory visualizations，坐标、caption、headline 完整。
- [ ] 正文和 captions 总字数 ≤1500；references/appendix 排除；正文不放代码。
- [ ] 数据采集方法满足 rubric；所有列有 documentation。
- [ ] Target、任务类型、预测时间点、使用者和模型用途明确。
- [ ] 预测时拿不到的 features 已排除；ID 不作为普通数值 predictor。
- [ ] 参考文献、数据来源和既有工作被引用；关键内容没有仅放在 appendix。
- [ ] Repo public，成员 collaborators、目录、LICENSE、README 和环境信息完整。
- [ ] 另一名成员完成复现检查；PDF 已放入 `report/`。
- [ ] Gradescope 提交状态和团队名单已核对。

## 8. Midterm 之后

准备 train/validation/test 划分与 cross-validation，训练课程覆盖的模型、选择最佳模型并做 interpretability。具体模型数量、展示时长等等待 final presentation rubric，不将猜测写成课程要求。

按时间或同一实体重复出现的数据，划分方式需要匹配未来使用情景，不能默认随机拆行。先做简单 baseline，再比较较复杂模型；test 不用于反复挑模型。

## 依据

- [Fall 2026 官方 midterm rubric](https://docs.google.com/document/d/1kC3cgE-CPUVmveWHdKAqlbnaq2XMNKjzY9ifF6M97ps/edit)
- [Canvas syllabus](https://canvas.brown.edu/courses/1103554)
- [EdStem 分组锁定公告](https://edstem.org/us/courses/104806/discussion/8358533)
