---
name: yunzhuan-deploy-aliyun
description: 通过云效 Flow 公共构建集群的并行质量门禁，将 Video2 的不可变 Git SHA 安全部署到阿里云 ECS，并验证 PM2 在线进程的真实运行目录。用于用户明确要求“云转部署阿里云”、使用云效替代或绕过 GitHub Actions 发布、优化云效串行测试、排查 Codeup/Packages/公共执行器环境问题，或确认阿里云正在运行指定 Video2 版本时。
---

# 云转部署阿里云

以“ECS 上的 API 与 Web 在线进程均从本次冻结 SHA 的 Release 目录运行”为完成条件。云效流水线成功、Release 目录存在、`current` 软链正确或公网能打开，都不能单独证明部署完成。

## 固定目标与边界

- Video2 根目录：`/Users/gkjiale/aigc/video2`
- GitHub 仓库：`git@github.com:jialezhang/video2.git`
- Codeup 镜像：`https://jingzhun-cn-hangzhou.devops.aliyuncs.com/codeup/video2.git`
- 云效流水线：固定复用 Flow `1441793`，显示名可随候选 SHA 更新为 `video2-ci-<TARGET_SHA_SHORT>`；不得新建或复用缺少下述 `VMDeploy` Job 的旧流水线。
- 云效主机组：`video2-production`；`machineGroup` UUID 为 `video2prod`，控制台数字 ID 为 `26793`，唯一机器为 `i-bp11prwf96sm8jc0agfu`。
- ECS 根目录：`/opt/video2`
- ECS 服务用户：`ecs-user`；必须复用 `/home/ecs-user/.pm2`，不得以 `root` 启动 Video2 PM2 应用。
- 公网入口：`https://47.98.184.79/`
- 部署记录：`/Users/gkjiale/aigc/video2-local/部署记录/部署记录.md`，必须保留在 Git 仓库之外。
- 不同步、覆盖或重建 `data/`、`storage/`、`.env`、SQLite 数据或其他受保护状态。
- 不强推 `main`、`present` 或 Codeup 分支，不覆盖并发提交。
- 云效直达 ECS 是用户明确授权后的替代发布通道。不得把它描述成 GitHub Actions 或 `present` 部署；不得为制造一致性而擅自移动 `present`。

## 0. 先证明云效环境可用

完整读取 [云效环境预检](references/yunxiao-readiness.md)。启动七路矩阵前先完成以下检查：

1. 核对公共执行器与 ECS 的精确出口 IP 分属独立白名单组，组均已启用，应用范围仅包含“代码管理”和“制品仓库”；不要选择全部应用，也不要假设上一次 IP 永久不变。
2. 分别证明公共执行器能够读取精确 Codeup ref，并能够向 run-scoped Packages 路径上传和读取探针；探针验证后只删除该探针。
3. 云效公共 Alinux 3 环境使用平台的 `python38` 运行时，并断言 Node 22、Python 不低于 3.8、`make` 和 C/C++ 编译器可用。默认 Python 3.6 不能作为 `node-gyp` 回退环境。
4. 使用 npm 的 portable FFmpeg/FFprobe 包，不依赖公共执行器的交互式 `sudo` 或不稳定系统仓库。
5. 保存流水线后重新读取已持久化 YAML，核对源 ref、完整 `TARGET_SHA`、七路 DAG、`publish-verified` 依赖和运行时选择。页面标题或旧缓存名称不构成配置证据。
6. 同时断言持久化 YAML 含 `deploy_job`、`component: VMDeploy`、精确制品引用、`machineGroup: video2prod`、`executeUser: ecs-user`、显式 `/bin/bash` 包装、Release 根目录受保护状态检查和运行时验收命令，并确认 `video2-production` 的 Runner 为 `ok`、机器安装状态为 `Finished`。缺一项就停止；不得在普通部署中转用浏览器传包。

任何预检失败都先归类为基础设施故障并修复环境；不要启动完整测试矩阵来重复制造同一失败。

## 1. 冻结唯一候选

1. 读取目标仓库的 `AGENTS.md` 和部署脚本，检查仓库根目录、remote、当前分支与脏工作树。
2. 取得用户指定的完整 40 位 `TARGET_SHA`；未指定时，先按仓库发布规则形成一个已提交候选，再冻结 SHA。
3. 验证候选对象存在且属于预期 `main` 历史。冻结后不追逐继续前进的 `main`。
4. 将精确 SHA 推送到独立 Codeup 分支，例如 `ci-target-<TARGET_SHA_SHORT>`。使用 compare-and-swap 或精确 refspec；推送后用 `git ls-remote` 证明远端 ref 等于 `TARGET_SHA`。
5. 不把本地未提交改动、可变分支名或工作目录现状当作发布身份。

## 2. 建立并行云效门禁

配置或检查流水线前，完整读取 [并行门禁参考](references/parallel-gate.md)。

在同一验证 Stage 中创建七个独立 Job；同一 Stage 内不声明彼此 `needs`，让云效默认并行调度：

1. `quality`：typecheck、`git diff --check`、critical 生产依赖审计。
2. `test-1`：普通测试 shard 1/4。
3. `test-2`：普通测试 shard 2/4。
4. `test-3`：普通测试 shard 3/4。
5. `test-4`：普通测试 shard 4/4。
6. `test-media`：五组 FFmpeg/媒体测试和有界依赖预检。
7. `build-release`：生产构建并上传 run-scoped 预构建制品及 SHA-256。

遵守以下约束：

- 每个 Job 都从 Codeup 精确 ref checkout，并在第一条业务命令前断言 `git rev-parse HEAD == TARGET_SHA`。
- 每个 Job 使用 Node 22 和独立的 `npm ci`。公共集群 Job 不共享工作目录或 `node_modules`。
- 每个 Job 在 `npm ci` 前断言 Python 与原生编译工具链；媒体 Job 按参考文件安装 portable FFmpeg/FFprobe。
- 普通测试的四个 shard 与媒体测试必须覆盖完整测试集合；不得为了适配并发额度而合并遗漏、跳过或改成 `continueOnFail`。
- 公共集群实际最大并发数从“Flow → 资源用量”读取。额度为 3 时仍保留七个 Job，由平台排队补位；不得退回一个 90 分钟串行 Job。
- 为每个 Job 设置与实际耗时匹配的短超时；依赖下载、媒体安装等子步骤使用更短的有界重试。
- `build-release` 可以与质量 Job 并行生成 pending artifact，但该制品在全部门禁成功前不可信、不可部署。

## 3. 晋级唯一可信制品

1. 新增 `publish-verified` Job，并让它 `needs` 全部七个验证 Job。
2. 只有七个 Job 全部成功时，下载 `build-release` 的 pending artifact、校验：
   - 流水线源 SHA、制品 `.video2-build-commit` 与 `TARGET_SHA` 完全一致；
   - `dist/app/index.html` 存在；
   - SHA-256 与构建 Job 上传的校验文件一致；
   - 制品不包含 `.env`、`data/`、`storage/`、SQLite、Git 凭据或 SSH 密钥。
3. 将校验后的制品标记为 verified，并记录云效 run 链接、run ID、目标 SHA、checksum 和各 Job 结果。
4. 任一门禁失败时，禁止发布并只清理该 run 的 pending artifact。不要清理整个制品根目录。
5. 先区分基础设施失败与代码失败：clone 白名单、Packages 权限、Python/编译器和媒体二进制属于基础设施；typecheck、测试、构建和设计系统检查属于代码。不得通过改弱命令、跳过测试或放宽设计门禁把代码失败伪装成基础设施修复。
6. 不得对同一根因无修改地重复运行。每次基础设施重试必须先取得新的直接证据并修复该层故障；后续阶段暴露的不同根因可以继续修复。优先只重试失败 Job；区域 PAT API 不支持目标操作时才重跑完整矩阵，并记录额外核分。代码失败默认只允许一个修复后继：提交最小代码修复、冻结新的 SHA、推送新的精确 Codeup ref，并重新运行全部门禁。
7. 同一 SHA 的单个时序断言只在已有至少一次同命令成功证据、日志显示其余用例通过且失败与资源时序一致时，允许一次不改门禁的复核。复核仍失败就按代码失败处理；不得增加 sleep、放宽断言或使用 `continueOnFail`。

## 4. 部署到 ECS

部署前完整读取 [无浏览器可信制品传输](references/artifact-transfer.md) 和 [VMDeploy Job 契约](references/vmdeploy-job.md)。普通部署只有一条合法路径：

```text
publish-verified → VMDeploy → video2-production/video2prod → ecs-user 发布与验收
```

1. `deploy_job` 必须 `needs [publish_verified_job]`，由云效 `VMDeploy` 直接把本次 Packages 包装制品下发至 run-scoped `/tmp` 路径。固定使用 `machineGroup: video2prod` 和 `executeUser: ecs-user`。
2. 制品引用必须是 `$[stages.verify_stage.build_release_job.upload_pending.artifacts.video2-${TARGET_SHA}]`。云效配置校验未通过、引用不存在、主机组非 `ok`、机器忙或直接下发失败时，将本次发布标记为基础设施阻塞并停止。
3. `VMDeploy` 会用 `/bin/sh` 启动 `run`。若命令含 `pipefail`、`[[`、数组、`mapfile` 或进程替换，必须把整个脚本包在 `exec /bin/bash <<'VIDEO2_DEPLOY_BASH' ... VIDEO2_DEPLOY_BASH` 中；仅写 `set -Eeuo pipefail` 会在业务命令前失败。
4. 制品清单的敏感路径检查只匹配 Release 根目录的 `.env*`、`data/`、`storage/`、SQLite 和 SSH 私钥。不得用 `(^|/)data/` 或 `(^|/)storage/`，否则会误杀 `src/**/storage/` 和依赖内的 `data/`。
5. **普通部署禁止使用 Workbench、浏览器上传、浏览器下载后再上传、Cloud Assistant 或复制登录态作为自动 fallback。** 禁止在失败后静默改走这些路线并声称部署完成。
6. 只有用户在看到直接路径的具体阻塞证据后，明确授权“本次紧急恢复”时，才可单次使用独立应急通道。应急结果必须标成例外，不能修改本技能的默认路径，也不能作为自动化完成证据。
7. 失败关闭是默认行为：直接路径没有满足契约时，本次部署结果只能是 `blocked`，不能是浏览器 fallback 后的 `complete`。
8. 不得把浏览器 Cookie、Bearer Token 或 Packages 登录态复制进 ECS 命令。Packages 的认证内容 URL 在 ECS 上可能返回登录 HTML；任何尺寸异常、格式不符或 checksum 不匹配的下载都立即作废并删除。
9. 校验 checksum、压缩格式、`.video2-build-commit` 和 `dist/app/index.html` 后再解包。Packages 下载结果是外层包装包；要求其中恰好有一个 Release tar 与一个配套 checksum，不要把包装包直接当 Release。
10. 不要在 ECS 重新构建其他代码。确需 Codeup 临时读取能力时：
   - 创建只读、一次性 Deploy Key；
   - 只为 ECS 公网 IP 临时放行 Codeup；
   - 完成或失败后移除 Deploy Key、ECS 私钥/公钥、临时源码目录并关闭临时白名单。
11. 部署前检查运行中任务数；运行时不空闲则等待，不得强制切换。
12. 盘点 `/opt/video2`、目标 Release、共享 `.env`、业务数据库与日志目录的 owner/mode。不得修改受保护数据。
13. 始终以线上服务用户执行发布：

   ```bash
   sudo -u ecs-user -H env \
     RUNNER_TRACKING_ID= \
     VIDEO2_WORKFLOW_RUNTIME_DOMAIN_AGENT_VIDEO=mastra \
     VIDEO2_MEMORY_RUNTIME=mastra \
     bash /path/to/scripts/deploy-aliyun-release.sh \
       "$TARGET_SHA" "$STAGING_DIR" prebuilt
   ```

14. 将部署 stdout/stderr 保存到与 `TARGET_SHA` 绑定的日志，再向控制台输出短尾部摘要。部署脚本失败时必须自动恢复上一 Release；不要手工拼凑半成功状态。
15. 不以 `root` 调用 Release 内的 PM2。若发现 `/root/.pm2`，先证明其中没有 Video2 进程，再只清理该错误 PM2 实例的 Video2 状态。

## 5. 验证真实运行身份

部署脚本成功后，以 `ecs-user` 独立运行目标 Release 自带的验证脚本：

```bash
sudo -u ecs-user -H env \
  VIDEO2_WORKFLOW_RUNTIME_DOMAIN_AGENT_VIDEO=mastra \
  VIDEO2_MEMORY_RUNTIME=mastra \
  bash "/opt/video2/releases/$TARGET_SHA/scripts/verify-aliyun-runtime.sh" \
    "$TARGET_SHA"
```

必须取得以下全部证据：

- `/opt/video2/current` 解析到 `/opt/video2/releases/<TARGET_SHA>`。
- `video2-api` 与 `video2-web` 均为 `online`，且 PID 大于 0。
- 两个 PID 的 `/proc/<pid>/cwd` 都解析到目标 Release。
- 身份核验之后，内部 API、Web、Proxy 健康检查均为 HTTP 200。
- 最后访问公网首页；非维护模式必须为 200。受保护 API 返回 401 不代表服务故障。

PID 在健康检查过程中变化、cwd 不匹配、内部请求失败或公网异常都表示尚未完成。继续诊断或让自动回滚生效，不得只报告软链或目录状态。

## 6. 清理、记录与报告

1. 清理前解析并盘点每个精确临时目标。只删除本次 run 的临时密钥、源码、staging 和 pending artifact；保留 verified Release 与回滚所需的上一版本。
2. 再次确认一次性 Codeup Deploy Key 和临时白名单已移除。供公共集群读取 Codeup/Packages 以及供 VMDeploy 从 ECS 下载 Packages 的精确、已启用、最小应用范围白名单可以保留，但要在报告中说明。
3. 更新仓库外部署记录。记录时间、完整 SHA、相对上版变化、并行门禁墙钟时间、部署与验收耗时、失败/重试和剩余风险。
4. 检查 Video2 工作树，明确现有未提交修改不属于已冻结 SHA。
5. 最终报告提供：
   - 云效 run 链接与七个门禁结果；
   - 完整 `TARGET_SHA` 与制品 checksum；
   - 两个 PM2 PID 及目标 cwd；
   - 内部与公网 HTTP 状态；
   - 整体墙钟时间和最终成功链路时间；
   - 并行门禁墙钟时间与累计核分口径的区别；
   - `VMDeploy`、`video2prod` 与 ECS Runner 的实际结果；如直接路径阻塞，明确说明本次没有部署且没有转用浏览器；
   - `present` 是否未变化；
   - 临时权限清理结果与未处理风险。

缺少任一运行时证据时继续执行或明确报告阻塞，不要把“云效成功”“已上传制品”或“部署命令已发送”表述为线上已经运行目标版本。
