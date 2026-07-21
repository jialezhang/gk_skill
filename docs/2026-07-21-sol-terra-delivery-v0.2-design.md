# Sol Terra Delivery 0.2 设计说明

## 背景

0.1.0 能约束 PRD、计划审批、单 Goal 交付和 exact-target 验收，但缺少六个会显著放大长任务成本的控制：计划前范围估算、超大 Goal 拆分、逐 turn 实际模型核验、Luna 验收、Agent 数量上限，以及阶段提交/多 worktree 集成。

0.2 的目标不是增加更多审查层，而是让任务更早变小、执行模型更便宜、错误路由更早失败，并让每个阶段都形成可恢复的 Git 事实。

## 决策

### 计划前先评估范围

批准 PRD 后先生成 `scope-assessment.yaml`。P80 表示 80% 的相似交付应能在该墙钟时间内结束，它来自真实代码范围、工作包、依赖/冲突、环境与集成成本，而不是根据 PRD 字数猜测。

- P80 ≤ 5 小时：通常一个 Goal。
- 5 < P80 ≤ 8 小时：一个 Goal，但要有阶段 checkpoint。
- P80 > 8 小时：建议拆分并询问用户。
- P80 > 10 小时：强烈建议拆分。
- 用户 240 秒未回复时，仅 Goal 包装默认保持单 Goal；这不构成 PRD 或计划批准。

### 模型路由必须有运行时证据

每次创建 task 和每个 follow-up turn 都必须显式传入模型，并从 runtime turn metadata 读取实际模型，写入 `model-routing.jsonl`。

| 工作 | 默认模型 |
| --- | --- |
| PRD、范围、计划、产品/计划/架构/高风险安全冲突 | Sol |
| 实现、调试、返工、集成 | Terra |
| focused test、build、checklist、浏览器 E2E、常规最终验收 | Luna |

`requested_model != observed_model` 或缺少实际 metadata 时返回 `MODEL_ROUTE_MISMATCH`，该 turn 产物不能作为交付证据。正式执行前必须完成 Sol、Terra、Luna 首 turn 与 follow-up turn Canary。

### 控制并行与上下文成本

Agent 预算按整个 Program 累计，而不是按 Goal 重置：正常目标 8、软上限 12、硬上限 20，最大嵌套深度 1，同时运行的 Goal session 不超过 3。优先复用 Terra 实现者和 Luna verifier，不允许 verifier-of-verifier 或递归编排。

### 用 Git checkpoint 形成真实进度

每个可独立运行的 vertical slice 或阶段完成后，必须按顺序执行 focused checks、diff/受保护数据检查、仅提交归属文件、push、记录远端 SHA、进度汇报。最终验收只接受 clean commit，dirty worktree 证据仅用于诊断。

### 多 Goal 以独立 session/worktree 实现

拆分后的每个 Goal 有可见 session、独立 worktree/branch、端口或浏览器 context、状态和 checkpoint。Program controller 只管理跨 Goal 依赖、冲突图和总 Agent 预算。所有 Goal 完成后，由 Terra 在 integration worktree 按依赖顺序合并，Luna 在 clean integration commit 上执行完整验收。

## 验证

0.2 增加了可重复的策略测试：

- P80 超过 8 小时却未建议拆分会失败；
- 超时决策必须为 `single_goal` + `timeout_default_single` + 240 秒；
- 实际模型与请求模型不一致会失败；
- Sol 用于 routine verification 会失败；
- Canary 缺少 Sol/Terra/Luna 任一模型会失败；
- 第 21 个 Agent 会失败；
- completed checkpoint 缺少 commit/push/report 会失败；
- 任一 Goal 未 push、未验证或路由无效时，Program 集成会失败。

## 剩余风险

- P80 早期仍是区间判断，需要用实际项目的预计/实际时间持续校准。
- Runtime 是否暴露稳定的 per-turn model metadata 必须由安装后的 live Canary 证明；静态测试不能替代 live Canary。
- 不同项目的服务内存、端口和 E2E 环境成本不同，最多 3 个并行 Goal 是上限，不是必须并行 3 个。
