> Archived October 9 planning. On October 14 the team selected U.S. state unemployment forecasting. See the current README and docs/plans/2026-10-14-bls-pipeline.md. Earlier candidate/status statements below describe that earlier date.

# outlier 的三个数据选题候选

2026-10-09 核查。**下面都是候选，没有一个已被小组选定。**实际 API 查询与字段检查摘要见 [source-checks.json](source-checks.json)。API 访问通过仅证明当前可获取这些字段；完整清洗、采集脚本和预测效果尚未验证。

## 候选比较

| 方向 | 建议研究问题 / target | 采集方式 | 范围与主要代价 | 初步判断 |
|---|---|---|---|---|
| Chicago 餐饮卫生检查 | 在例行检查前预测该次检查是否 Fail；binary classification | 官方 Socrata API，按日期、facility type、inspection type 查询并分页 | 一城市、餐厅、2023–2025；要处理重复店铺、历史记录、检查后的信息泄漏 | **首推：目标直接、范围可控、有官方既有工作** |
| NYC 311 处理时间 | 在请求创建时预测是否会在 7 天内被行政结案；binary classification | 官方 Socrata API，按日期、borough、agency/problem 查询并分页 | 先选一类服务/一个机构；未结案记录、结案口径和机构差异更复杂 | 社会数据问题较丰富，但清洗和标签定义成本更高 |
| Providence 次日最高温 | 以 t 日结束时及以前的数据预测 t+1 日最高温；regression | Open-Meteo Historical Weather API，按时间区间和变量获取 | 建议一城市、2015–2025；time-series split、lagged features、季节性 baseline | 技术入口最简单，数据来源与真实预测时可用性要谨慎说明 |

以上年份、7 天阈值和范围是建议，不是课程要求。

## A. Chicago：餐厅卫生检查是否不合格

**一句话问题：** Can information available before a routine restaurant inspection help predict whether that inspection will fail?

- 原始发布者：City of Chicago / Chicago Department of Public Health。
- [官方数据页面](https://data.cityofchicago.org/Health-Human-Services/Food-Inspections/4ijn-s7e5)
- [API 文档入口](https://dev.socrata.com/foundry/data.cityofchicago.org/4ijn-s7e5)
- API endpoint：`https://data.cityofchicago.org/resource/4ijn-s7e5.json`
- 一行：一次检查；`inspection_id` 是记录标识，`license_` 可作为历史店铺关联的候选 key，需要检查 0/缺失/复用等情况。
- 建议范围：`facility_type = 'Restaurant'`、`inspection_type = 'Canvass'`，2023-01-01 至 2025-12-31。仅把 `Pass`、`Pass w/ Conditions`、`Fail` 放入第一版标签定义；`Pass w/ Conditions` 与 Fail 不同，二分类中归入“未 Fail”，不能将其表述为完全无问题。
- **实际核查：**在上述范围中，API 返回 Pass 9,355、Fail 4,193、Pass w/ Conditions 3,452，共 **17,000** 次有评价结果的检查，Fail 比例 **24.66%**。另外有 Out of Business 2,766、No Entry 96、Not Ready 2、Business Not Located 2；这些不能不加说明地作为 Pass。查询时的数量可能随后更正。
- 候选 features：地点信息、日历变量，以及严格早于本次检查的历史结果、距上次检查的时间、历史失败比例。`risk` 等静态字段能否代表检查前已知状态需要核实，不能因为在表中出现就认定可用于预测。
- 禁止直接放入 X：**本次 `results`、本次 `violations`**；它们可以作为标签/解释材料，不能作为检查前预测的 features。

**建议三张 EDA 图：**结果类别及比例；有/无历史失败记录的 Fail 比例并标注样本量；按季度/区域的 Fail 比例（同时展示分母，避免小样本误读）。

**潜在用途：**为例行检查优先级提供研究性参考。只有被检查的店铺产生 outcome，因此预测结果不能直接推广到所有未检查店铺，不能声称已证明政策效果。

**方法风险：**官方 metadata 提醒可能存在重复报告，并注明 2018-07-01 检查流程变化；第一版采用 2023–2025，仍要检查重复记录与当期制度。相同店铺会多次出现，历史 features 只使用更早记录；采用时间划分以匹配后续检查预测。只保留完成评价的检查会限定适用人群，需要在报告中说明。

**既有研究起点：**[City of Chicago 官方预测与评估项目](https://github.com/Chicago/food-inspections-evaluation)。它预测 critical violations，与本候选的整体 Fail 标签并不完全相同；可作为动机和相关研究，不能直接拿它的效果当作我们的结果，也不要复用其成品训练数据作为自己的采集工作。

## B. NYC 311：请求是否在 7 天内结案

**一句话问题：** At request creation, can intake information predict administrative closure within seven days for a specified service category?

- [官方数据页面](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9)
- [官方更新说明](https://www.nyc.gov/opendata/news/all-news/311-Service-Requests-Updates)
- API endpoint：`https://data.cityofnewyork.us/resource/erm2-nwe9.json`
- 一行：一次 service request；`unique_key` 是 ID。
- 建议先选一个 borough 和一类服务/一个机构，再根据 target 分布选范围，避免直接下载全市多年千万级数据。
- 初步 label：`closed_date - created_date <= 7 days`；但必须固定 snapshot、给每条请求至少完整 7 天的观察窗口，并验证“缺少 closed_date”的含义。不能直接删除所有未结案请求，也不能把最近还没观察满 7 天的请求标为失败。
- 候选 features：请求创建时的 problem/detail、地点、提交渠道、日历变量；agency 若可能在后续被重新分配，需要核实初始状态。
- 从 X 排除：`closed_date`、最终 `status`、`resolution_description`、`resolution_action_updated_date` 等事后处理结果。

**实际访问核查：**成功读取 2025 年 1 月 Brooklyn 按创建时间排序的前 200 条记录，查到上述关键字段。此小样本不是随机抽样，不据此声称全体请求都已结案或没有日期错误。

**建议三张图：**关闭耗时分布/7 天结案比例；某一类服务按地点的结案比例与样本量；提交月份或渠道与结案比例。

**解释限制：**行政 closure 不等于居民问题被真正解决。响应时间差异还可能来自工作量、机构标准、诉求复杂度和居民投诉倾向；不能从这些关联推断政府歧视或因果效果。

**当前 schema 提醒：**网页标签已将 Complaint Type 改为 Problem、Descriptor 改为 Problem Detail，官方说明 API 后端字段名保持 `complaint_type` 和 `descriptor`；当前主表覆盖 2020 至今，2010–2019 在另一个表。

**文献起点：**[NYC 311 数据整理与质量研究](https://arxiv.org/abs/2502.08649)，以及具体 agency/service 的官方处理规则。需要自行阅读全文，确认它能支持哪些陈述。

## C. Providence：次日最高温预测

**一句话问题：** Can lagged daily weather and calendar information predict the next day's maximum temperature better than persistence and seasonal baselines?

- [官方 Historical Weather API 文档](https://open-meteo.com/en/docs/historical-weather-api)
- API endpoint：`https://archive-api.open-meteo.com/v1/archive`
- 按 Providence 坐标（示例 41.824, -71.413）、日期区间和 daily variables 调用 API；统一 `America/New_York`，固定 model 参数，如 ERA5。
- 一行：一个本地日；target 是次日 `temperature_2m_max`。
- 候选 features：已结束的历史日最高/最低温、降水、风速等 lagged values，day-of-year；不使用次日 realized weather 作为输入。
- 首版建议 2015–2025 单城市，约数千日；不扩展多城市或复杂 deep learning。

**实际访问核查：**API 成功返回 2025-01-01 至 2025-01-07 的 7 日记录，包含最高温、最低温、降水量和最大风速，单位分别为 °C、mm 和 km/h。

**建议三张图：**温度的年度/季节变化；今日与次日温度关系；不同季节的波动/target 分布。

**主要风险：**此 API 的历史数据属于 reanalysis，而不是单个地面站的原始观测或实时预测；真实部署时同样版本的数据不一定及时可得。最稳妥的表述是 retrospective next-day prediction exercise，并用仅使用过去的时间划分与 persistence baseline。不能因为一个随机 split 分数高就认为具备实际天气预报能力。

**初步推荐：**若没有明确兴趣，先让小组比较 A 和 B；A 更容易形成可控的 supervised ML 问题，B 的社会数据解释空间较大。C 是技术备选，但需要更仔细地处理历史数据与真实预测情景的差别。
