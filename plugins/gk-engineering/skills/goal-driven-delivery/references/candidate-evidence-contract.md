# 候选版本与测试证据合同

## 固定产物

每个 Program 维护以下机器可读产物：

- `baseline-verification.json`：改动前通过项、既有失败和目标身份；
- `test-impact-map.json`：变更文件/合同、风险、受影响场景和所需测试档位；
- `test-evidence-index.json`：每次执行的命令、结果、模型、耗时、token、候选版本和原始证据；
- `candidate-evidence.json`：同一候选版本的验收声明、执行场景、完整回归和独立 Terra 最终验收。

`candidate-evidence.json` 还维护两项通用控制面：

- `runtime_provenance`：实际被验证目标的启动、执行者/进程、build、目标探针和清理证明；
- `evidence_records`：每份证据的身份、候选版本、状态、原始路径以及替代/作废关系。

使用同目录 `assets/` 中的模板初始化。候选完成前运行：

```bash
python3 scripts/validate_candidate_evidence.py <candidate-evidence.json>
```

## 基线和影响分析

首次编辑前运行足以识别已有失败的最小基线，并记录 commit、build、入口、Flags、外部副作用策略和受保护资源/fixture 指纹。每次改动后更新影响图，不依据“改了几个文件”猜测试范围。

影响图至少回答：

- 哪些产品声明和执行场景可能失效；
- 是否改变共享运行时、状态生命周期、外部副作用边界或持久化；
- 当前应运行 `fast`、`change` 还是 `full`；
- 既有证据的哪些失效键发生变化。

## 证据索引和复用

一项通过证据只在以下条件同时满足时可复用：

- `candidate_commit`、build 和 exact target 一致；
- 所有声明的失效键未变化；
- 原始日志、截图或报告仍可读取；
- 外部副作用策略及授权满足该声明；
- 运行模型符合角色合同。
- 浏览器证据明确记录 Ego Lite `ego-browser` task-space、精确 URL、交互和关闭动作；其他浏览器入口只能作为诊断证据。

模型或 reviewer 变化本身不使证据失效。Reviewer 先对账索引，再只运行缺失或已失效的场景。

## 运行来源

运行来源回答“测试实际命中了什么”，不是“计划希望命中什么”。对需要运行时验收的 target，`runtime_provenance` 必须与候选 commit 一致，并按 target 的性质声明所需观察项。典型服务 target 包含：

- 启动前端口/资源预检；
- 启动命令及实际进程或执行者身份；
- 实际 build/commit 身份；
- health、API、CLI 或浏览器目标探针；
- 验收结束后的清理证明。

运行时不适用时必须写明 `not_applicable_reason`。端口被占用、复用旧进程、只读取配置或持久化字段、或无法关联 build 与执行者时，结果只能标为 diagnostic，不得支撑 `TARGET_VERIFIED`。

## 证据生命周期

`evidence_records` 的状态只允许为：`draft`、`candidate`、`accepted`、`invalidated`、`superseded`。

- 只有 `accepted` 且对当前候选有效的记录可支撑验收声明；同候选可直接绑定，跨候选必须包含 `revalidation`，记录目标候选、检查过的失效键、时间和原始证据；
- `invalidated` 必须记录原因和触发它的 artifact、环境或决策；
- `superseded` 必须指向替代证据；
- 代码、配置、消耗合同、运行来源或目标环境改变时，控制器必须重新判断既有证据，不能沿用旧结论；
- 失效证据保留用于诊断和审计，但不得被 Gate 或集成复用。

## 候选冻结与最终验收

只有在计划内实现完成、阶段真实用户旅程通过、Project Profile 中所有外部副作用已解析且无未解决失效项时，才能写入 `candidate_freeze.status: frozen`。冻结同时记录 `project_profile_sha256`；完整回归和构建绑定该 commit。候选或 Profile 变化后，冻结自动失效，必须重新判断影响，不能沿用旧候选的完成结论。

独立 Terra 最终验收消费原始证据并运行仍需人类交互判断的关键场景。其线程不得属于 `implementation_thread_ids`。最终 `TARGET_VERIFIED` 需要：

- 每个 `AC-*` 被至少一个已通过的同候选 `SC-*` 覆盖；
- 每个被引用的场景、完整回归和最终验收都绑定一份 `accepted` 证据记录；
- 需要运行时验收的 target 具有同候选且已验证的 `runtime_provenance`；
- 完整回归在同一候选通过；
- 无未解决失效；
- Terra 最终验收模型和线程独立性可验证。
