# 基于 Spec Kit 的多模型自治交付系统

## 1. 想构建的系统

目标不是再做一个普通的 planning skill，也不是复制 Spec Kit，而是构建一套：

> 从需求讨论开始，经过 PRD 和实施计划两次人工确认，再由多模型、多角色 Agent 自主执行到最终真实验收的软件交付系统。

它要解决当前手动工作流的结构性缺陷：

```text
过去：
Sol 制定计划
→ Terra 接管实施
→ Terra 遇到计划级问题后仍由 Terra 自己判断和修补
→ 强模型在最需要介入的时候不在工作流中

目标：
Sol 负责产品、架构、计划和计划修订
→ Terra 负责实施、调度和运行状态
→ 专业 Agent 负责前端、后端、数据、测试和集成
→ 计划级问题自动升级 Sol
→ 产品级问题才升级用户
→ 循环到真实完成
```

## 2. 三层决策权

| 问题级别 | 负责人 | 典型情况 |
| --- | --- | --- |
| 实现级 | Terra / 专业 Executor | 文件位置、helper 复用、测试修复、局部重构 |
| 计划级 | Sol | SDK 假设失败、公共接口变化、新状态 owner、架构前提失效 |
| 产品级 | 用户 | 用户流程变化、P0 降级、安全边界变化、费用或范围扩大 |

核心规则：

```text
实现问题 → Terra
计划问题 → Sol
产品问题 → 用户
```

## 3. 端到端流程

```text
用户提出需求
→ Sol 进行 Grill / Product Discovery
→ Sol 生成 Agent-ready PRD
→ 用户批准 PRD
→ Sol 生成完整实施计划、Tasks 和 Delegation Map
→ Sol 执行 spec / plan / tasks 一致性分析
→ 用户批准实施计划
→ Terra Delivery Controller 创建唯一顶层 Goal
→ Terra 调度前端、后端、数据、测试等专业 Agent
→ 独立测试与验证 Agent 收集证据
→ 局部问题由 Terra 返工
→ 计划问题交给 Sol 修订受影响计划
→ 产品问题请求用户决策
→ Sol 执行 Gate Review
→ 对照 PRD 执行真实目标验收
→ 全部通过后 Goal Complete
```

用户只需要在两个正常节点正式批准：

1. 产品合同，也就是 PRD；
2. 实施基线，也就是 Plan 和 Tasks。

Goal 启动后，不再为普通、可逆的技术问题反复询问用户。

## 4. Spec Kit 的定位

Spec Kit 负责保存稳定、版本化、可审查的交付事实：

```text
constitution
→ assess / clarify
→ specify
→ plan
→ tasks
→ analyze
→ implement
→ converge
```

在本系统中，Spec Kit 负责：

- 项目原则；
- 产品规范；
- 技术计划；
- 稳定任务 DAG；
- 验收映射；
- 用户审批 Gate；
- 实现缺口收敛；
- 持久化文档和版本。

Spec Kit 不负责：

- 当前 Codex App 任务的 Goal；
- native subagent 生命周期；
- 运行时任务调度；
- executor retry；
- Agent 邮箱和协作状态；
- 最终运行状态所有权。

## 5. Codex Controller 的定位

Codex Delivery Controller 是唯一运行时状态机，负责：

- 顶层 Goal；
- 当前任务状态；
- 依赖判断；
- Agent 路由；
- 并发和写入范围冲突；
- task attempt；
- retry 和返工；
- escalation；
- 验证证据收集；
- 最终完成判断。

只能有一个运行时控制器。不要让 Spec Kit Workflow 和 Terra Controller 同时管理 implement、retry、blocked、converge 和 completion，否则会形成双控制面。

## 6. 推荐的 Agent 角色

角色定义与具体模型解耦：

```text
Product Discovery Agent
Product Specification Agent
Architecture Planner
Plan Reviewer
Delivery Controller
Frontend Executor
Backend Executor
Data Executor
Integration Executor
Test Executor
Browser QA
Product Acceptance Reviewer
```

默认模型映射可以是：

```text
Product Discovery Agent     → Sol xhigh
Product Specification Agent → Sol xhigh
Architecture Planner        → Sol xhigh
Plan Reviewer               → Sol xhigh
Product Acceptance Reviewer → Sol xhigh

Delivery Controller         → Terra high
Frontend Executor           → Terra high
Backend Executor            → Terra high
Data / Integration Executor → Terra high
Test Executor               → Terra high 或 medium
```

模型映射属于 Codex 配置，不进入 PRD。未来模型升级时，只修改角色映射。

## 7. Constitution

使用 Spec Kit Constitution 保存项目级长期规则：

- 测试标准；
- 数据安全；
- 权限要求；
- 架构禁止事项；
- Definition of Done；
- Agent 行为边界；
- 谁可以改变产品范围；
- 谁可以修改实施计划；
- 验收证据要求。

这些项目通用规则不应在每份 PRD 中重复。

## 8. Product Discovery

可以基于 Spec Kit 的 `assess` 和 `clarify`，增加一个更完整的 Grill 工作流。

Discovery 负责确定：

- 用户是谁；
- 当前问题；
- 期望结果；
- 核心用户旅程；
- must-have；
- non-goals；
- 产品取舍；
- 成功意图；
- 仍需用户决定的问题；
- 可以交给技术规划解决的未知项。

Discovery 不做具体技术设计。

## 9. Agent-ready PRD Preset

不要同时维护内容重复的 `prd.md` 和 `spec.md`。将 Spec Kit 的 `spec.md` 定制为 Agent-ready PRD。

PRD Preset 覆盖或组合：

```text
spec-template.md
speckit.specify
speckit.clarify
```

PRD 建议包含：

```markdown
## Status and Approval
## Product Outcome
## Users and Core Journeys
## Product Invariants
## Requirements and Priority
## Non-goals
## Human Decision Boundary
## Implementation Freedom
## Acceptance Inventory
## Product Assumptions
## Change Control
## Completion Definition
```

需求元数据建议包含：

| 字段 | 用途 |
| --- | --- |
| ID | 稳定追踪 |
| Priority | 完成阻断等级 |
| Domain | 前端、后端、数据、安全等能力域 |
| Risk | 调度和审查强度 |
| Acceptance level | Core、Safety Critical、Quality、Optional |

PRD 中不要写：

- Sol/Terra 模型名；
- reasoning effort；
- Fast Mode；
- Agent 配置；
- Skill 名称；
- 文件路径；
- Task 分配；
- 测试命令。

## 10. Planning Preset

Planning Preset 定制：

```text
plan-template.md
tasks-template.md
speckit.plan
speckit.tasks
speckit.analyze
```

`plan.md` 应覆盖完整项目，而不是只规划第一个里程碑：

- 所有主要里程碑；
- 所有主要任务；
- 任务依赖；
- 架构合同；
- 责任迁移；
- 数据所有权；
- 安全和幂等边界；
- 验收；
- Gate；
- 回滚；
- Legacy 退出；
- 假设账本；
- 计划修订条件。

但不同决策必须标注不同确定性：

| 等级 | 执行含义 |
| --- | --- |
| MUST | 产品、安全、权限、数据等硬约束 |
| BASELINE | Sol 批准的总体技术方向 |
| VERIFY_FIRST | 必须先验证的 SDK 或运行假设 |
| RECOMMENDED | 推荐实现，允许等价局部调整 |
| DEFERRED | 到指定 Gate 后按预定规则决定 |
| FORBIDDEN | 明确不得实施 |

精细度原则：

> 有证据的决策尽可能写细；继续细化必须依赖尚未获得的运行证据时停止。

## 11. Tasks 和 Delegation Map

每个 Task 需要同时支持实施和自动调度：

```yaml
task_id: T004
outcome: Headless Runtime 成为 Thread 状态 owner

depends_on:
  - T002
  - T003

preferred_role: frontend_executor

required_skills:
  - react-best-practices
  - test-driven-development

write_scope:
  - src/app/runtime/**
  - tests/runtime/**

acceptance:
  - 同一个 Thread 只有一个状态 owner
  - 刷新后恢复相同状态

escalation_conditions:
  - 必须保留双 Runtime
  - 公共事件合同需要改变
  - 需要新增持久化状态层

parallel_safe: false
```

Sol 在规划阶段提供默认 Delegation Map。Terra 可以根据实际依赖、写入冲突和 Agent 可用性做局部调度调整，但不能借调度改变产品和架构基线。

## 12. 两次审批 Workflow

Spec Kit Workflow 负责前置阶段：

```text
Sol Discovery
→ Sol Specify
→ PRD Approval Gate
→ Sol Plan
→ Sol Tasks
→ Sol Analyze
→ Plan Approval Gate
→ 启动一次 Terra Delivery Controller
```

进入 Delivery 后，Workflow 不再与 Terra 共同管理任务执行循环。

## 13. Terra Delivery Loop

Terra Controller 执行：

```text
读取批准的 spec / plan / tasks
→ 创建一个顶层 Goal
→ 找出依赖已经满足的 Task
→ 检查 write_scope 冲突
→ 创建专业 Agent
→ 收集结构化 handoff
→ 运行独立验证
→ 分类结果
   ├─ 局部问题：返给原 Executor
   ├─ 跨模块合同问题：Integration Agent
   ├─ 计划级问题：Sol
   └─ 产品级问题：用户
→ 更新 delivery-state
→ 进入下一 Task 或 Gate
→ 最终真实验收
```

只建立一个顶层 Delivery Goal。子 Agent 是 task attempt，不创建独立持久化 Goal。

## 14. 统一 Handoff

专业 Agent 返回：

```yaml
task_id: T004
status: completed

changes:
  - path: src/app/runtime/example.ts
    summary: 接管 Thread 状态投影

tests:
  passed:
    - runtime contract tests
  failed: []

deviations:
  - type: local
    planned: 新建 pending reducer
    actual: 复用已有 pending state
    reason: 等价且更小

plan_conflicts: []
remaining_risks: []
recommended_next:
  - run integration verification
```

有效结果状态：

```text
completed
needs_rework
blocked
plan_conflict
```

## 15. Escalation Protocol

计划冲突必须生成结构化证据：

```yaml
escalation_id: ESC-003
task_id: T004
failed_assumption: A-07

observed_evidence:
  - SDK connect 不恢复持久化状态
  - 旧 Socket 同时拥有附件 transport

impact:
  - 无法按原计划实现单 Runtime owner
  - T004 和 T009 受影响

reversible_changes:
  - 实验 Adapter 位于关闭的 feature flag 后

options_considered:
  - 拆出附件 transport
  - 保留旧 Socket 的非状态职责

requires:
  - sol_plan_revision
```

处理流程：

```text
Terra 暂停受影响任务
→ Sol 读取计划、diff、测试和 escalation
→ Sol 只修订受影响部分
→ 创建新的 plan/tasks revision
→ 受影响的旧 task attempts 失效
→ Terra 按新 revision 继续
```

只有修订改变产品范围、用户流程或验收语义时才询问用户。

## 16. 持久化状态

建议产物：

```text
spec.md
产品权威

plan.md
架构和实施基线

tasks.md
稳定 Task ID、依赖、验收和角色建议

delivery-state.yaml
唯一运行状态

decision-log.md
关键发现和计划修订

escalations/
计划冲突证据

verification.md
独立验证证据
```

`tasks.md` 不承担实时运行状态。实时状态只由 Controller 管理。

```yaml
artifact_revision:
  spec: 1.0
  plan: 1.2
  tasks: 1.3

goal:
  status: executing

tasks:
  T001:
    status: completed
    attempt: 1
    executor: backend_executor
    verification: passed

  T002:
    status: plan_conflict
    escalation: ESC-003

gates:
  G1:
    status: pending
```

执行中的 artifact revision 不可静默变化。计划修订时必须明确受影响任务。

## 17. Converge

Spec Kit `converge` 负责：

```text
读取 spec / plan / tasks
→ 检查当前实现缺口
→ 将缺口 append 到 tasks.md
→ 再由 implement 或 Controller 执行
```

它不负责：

- 修改 PRD；
- 修改 Plan；
- 修改产品代码；
- 重新解释产品范围；
- 调度 Agent；
- 处理架构前提失效。

因此：

```text
实现缺口 → converge
计划前提错误 → Sol plan revision
产品合同变化 → 用户
```

## 18. Spec Kit Workflow 与 Codex 的边界

Spec Kit Workflow 支持逐 step `model`，Codex integration 会执行：

```text
codex exec <prompt> --model <model> --json
```

这意味着 Workflow 中的每个 AI step 是新的 Codex CLI 进程，并不是当前 Codex App 任务里的 native subagent，也不会自动继承当前任务的 Goal。

Spec Kit Workflow 当前也没有逐 step `reasoning_effort` 的一等字段。

因此推荐：

```text
Spec Kit Workflow
负责前置规范阶段、产物和两次审批

Codex product-to-delivery Skill
负责当前任务中的 Goal、native subagents 和执行闭环
```

## 19. 需要开发的组件

```text
sol-terra-spec-delivery/
├── presets/
│   ├── agent-ready-prd/
│   │   ├── preset.yml
│   │   ├── templates/spec-template.md
│   │   └── commands/speckit.specify.md
│   │
│   └── governed-planning/
│       ├── preset.yml
│       ├── templates/plan-template.md
│       ├── templates/tasks-template.md
│       └── commands/
│
├── extensions/
│   └── delivery-governance/
│       ├── extension.yml
│       └── commands/
│           ├── escalate.md
│           ├── revise-plan.md
│           ├── review-gate.md
│           └── accept.md
│
├── workflows/
│   └── product-to-approved-plan.yml
│
├── codex/
│   ├── agents/
│   └── skills/
│       ├── product-to-delivery/
│       └── goal-driven-delivery/
│
└── bundle/
    └── bundle.yml
```

职责：

- Preset：修改 Spec Kit 原有模板和命令；
- Extension：新增升级、验收、状态或外部集成能力；
- Workflow：阶段顺序和审批；
- Codex Skill：Goal 和子 Agent 控制；
- Bundle：组合与分发，不承载运行逻辑。

## 20. 建设顺序

### MVP 1：规范产物

- Agent-ready PRD Preset；
- Planning/Tasks Preset；
- Approval 状态；
- Task Delegation 元数据。

### MVP 2：单 Controller 执行

- Terra Delivery Controller；
- 一个顶层 Goal；
- frontend/backend/test 三类 Agent；
- delivery-state；
- 统一 handoff；
- 局部返工循环。

### MVP 3：Terra 到 Sol 升级

- escalation packet；
- plan revision；
- artifact revision；
- 受影响任务 invalidation；
- Gate Review。

### MVP 4：收敛与真实验收

- converge；
- 独立验证矩阵；
- 浏览器和真实 Provider 验收；
- 最终 PRD 对账；
- rollback 和 Legacy 对账。

### MVP 5：打包分发

- Spec Kit Bundle；
- catalog；
- 版本管理；
- 项目模板；
- Agent 配置安装器。

## 21. 关键风险

1. Spec Kit Workflow 与 Terra 同时做运行调度，形成双状态机；
2. Sol 同时制定需求、实现和生成证据，形成自审偏差；
3. 运行中静默修改 Plan，导致不同 Agent 使用不同 revision；
4. 子 Agent 直接向用户提问，使产品决策碎片化；
5. `tasks.md` 和 Goal 同时承担运行状态；
6. 所有任务都强制完整 PRD 流程，产生固定流程税；
7. 把角色绑定具体模型名，导致模型升级时修改整个体系。

建议根据风险选择流程深度：

```text
小 Bug / 局部修改
→ 直接执行 + 验证

标准功能
→ Spec + Plan + Tasks + Delivery

高风险迁移
→ 完整 PRD 审批 + Plan 审批 + Gate + 真实验收
```

## 22. 最终定位

> 一个以 Spec Kit 保存产品和计划事实、以 Codex Terra Controller 负责唯一运行状态、以 Sol 负责高价值决策和计划升级的多模型自治软件交付系统。

Spec Kit 回答：

```text
要做什么
批准过什么
计划是什么
还有哪些实现缺口
```

Codex Controller 回答：

```text
现在执行哪个任务
由哪个 Agent 执行
哪些任务可以并行
失败后返工还是升级
何时能够宣布完成
```

三方权威：

```text
Sol：产品语义和计划权威
Terra：执行和运行状态权威
用户：最终产品取舍权威
```

## 23. 参考资料

- [Spec Kit](https://github.com/github/spec-kit)
- [Spec Kit Workflows](https://github.github.io/spec-kit/reference/workflows.html)
- [Spec Kit Presets](https://github.github.io/spec-kit/reference/presets.html)
- [Spec Kit Extensions](https://github.github.io/spec-kit/reference/extensions.html)
- [Spec Kit Codex Integration](https://github.com/github/spec-kit/blob/main/src/specify_cli/integrations/codex/__init__.py)
- [Spec Kit Converge](https://github.com/github/spec-kit/blob/main/templates/commands/converge.md)
