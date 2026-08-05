# Project Profile Contract

`project-profile.json` 是项目特有事实进入通用交付流程的唯一声明边界。核心状态机、验证器和完成门禁不得硬编码业务领域、技术栈、端口、数据目录、供应商或部署工具。

从 `assets/project-profile-template.json` 初始化，并在交付 preflight 运行：

```bash
python3 scripts/validate_project_profile.py <project-profile.json>
```

## 通用对象

- `target_components`：待验证组件及其身份要求和运行时探针；
- `protected_resources`：需要写门禁、备份和回滚的文件、数据库、队列或外部状态；
- `external_effects`：会影响工作区之外系统、人员、预算或真实数据的动作；
- `acceptance_journeys`：声明、目标组件和可执行旅程的映射；
- `verification_commands`：项目实际提供的 `fast`、`change`、`full` 检查；
- `rollback_actions`：受保护资源和变更的可执行恢复动作。

ID 和 `kind` 都是开放字符串；插件只验证引用完整性和安全不变量，不维护某个项目的枚举。

## 外部副作用

每项外部副作用只能使用以下策略之一：

- `forbidden`：当前交付不得执行；
- `sandboxed`：仅在隔离目标执行，并保留隔离身份和结果证据；
- `authorized`：已有明确授权，必须记录授权来源、限制和验证证据；
- `not_applicable`：旅程不会触发该类副作用。

具体 effect ID 可以表示付款、通知、第三方写入、设备动作、生成服务调用或任何其他项目行为。通用核心不解释其业务含义。

## 受保护资源

每个受保护资源必须声明定位方式、写门禁、备份动作和回滚动作。Profile 只授权控制流程，不等于授权执行真实写入；实际执行仍服从用户许可和项目自身安全规则。

Profile 发生变化时，候选冻结失效；控制器必须重新计算影响、重验证相关证据并重新签发完成收据。
