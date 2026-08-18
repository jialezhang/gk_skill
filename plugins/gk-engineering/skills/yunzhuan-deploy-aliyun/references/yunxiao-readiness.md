# 云效环境预检

## 目录

1. Codeup 与 Packages 权限
2. 公共执行器工具链
3. 流水线持久化检查
4. 本地 OpenAPI 凭据
5. 失败分类与停止条件

## 1. Codeup 与 Packages 权限

在完整矩阵前先证明 clone 和制品读写能力：

- Codeup IP 白名单的应用范围只选择“代码管理”和“制品仓库”，不要选择全部应用。
- 已观察到的公共执行器出口 IP 为 `116.62.173.28` 和 `47.96.173.226`。它们是当前基线，不是永久承诺；新日志出现不同出口 IP 时，只在证据充分后追加该精确 IP。
- `VMDeploy` 的 Packages 下载发生在 ECS，不是公共执行器。为 ECS 建立独立且已启用的 IP 组；当前固定出口为 `47.98.184.79`，应用范围同样只选“代码管理”和“制品仓库”。日志出现 `NO_PERMISSION_IP_INSECURITY` 时，以响应中的 client IP 为证据更新该组。
- 使用精确 `ci-target-<TARGET_SHA_SHORT>` ref 做 clone 探针，并断言完整 SHA。
- 使用 run-scoped 名称做 Packages 上传与读取探针；验证完成后只删除该探针，不清空仓库。
- clone 的 `403`、IP 白名单拒绝或 Packages 的权限错误都属于基础设施失败，不消耗代码修复后继。

不要扩大到所有阿里云应用。公共构建访问与 ECS 下载访问是两类权限，必须使用独立 IP 组并分别审计；精确固定出口可以长期保留，临时 NAT/EIP 或宽 CIDR 必须在部署后移除。

## 2. 公共执行器工具链

公共 Alinux 3 Job 使用以下约束：

```bash
set -Eeuo pipefail

test "$(node --version | sed -E 's/^v([0-9]+).*/\1/')" = "22"
python3 - <<'PY'
import sys
assert sys.version_info >= (3, 8), sys.version
PY
command -v make >/dev/null
command -v gcc >/dev/null
command -v g++ >/dev/null
```

- 在云效运行时配置中选择 `python38`，不要依赖镜像默认 Python 3.6。`better-sqlite3` 的预构建包下载失败时会回退到 `node-gyp`，旧 Python 会在此处产生误导性代码失败。
- 只启用安装 Python 3.8 与最小编译工具所需的软件源；不要为了修一个 Job 无界扩充系统仓库。
- 媒体 Job 使用 `@ffmpeg-installer/linux-x64@4.1.0` 与 `@ffprobe-installer/linux-x64@5.2.0`，安装到 Job 独占临时目录并导出实际二进制路径。不要依赖需要交互密码的 `sudo`。
- 原生依赖与媒体安装都设置短超时和有限重试；重试后仍是同一网络或镜像错误时停止矩阵。

## 3. 流水线持久化检查

云效 UI 保存后重新读取实际 YAML，并核对：

1. 源分支是精确 `ci-target-<TARGET_SHA_SHORT>`。
2. `TARGET_SHA` 是完整 40 位 SHA。
3. 七个验证 Job 位于同一 Stage，彼此没有串行 `needs`。
4. `publish-verified` 依赖全部七个 Job。
5. Node 22、`python38`、portable FFmpeg/FFprobe 和 run-scoped Packages 名称都已持久化。

页面标题可能仍显示旧流水线名。以保存后的 YAML、运行实例源 SHA 和 Job 日志为准，不以标题缓存为准。

## 4. 本地 OpenAPI 凭据

- Codeup 使用本机已登记的 SSH key 推送精确 ref；不要通过浏览器上传源码或制品。
- Flow PAT 保存到 macOS Keychain，例如 account `root`、service `video2-yunxiao-token`；只在子进程环境中读取，不打印 token。
- 浏览器外部署需要：流水线读写、流水线运行实例读写、流水线运行任务读写、主机部署读写、主机组只读。PAT 过期时间必须写入部署记录。
- 区域 PAT API 支持触发/读取 run、读取 Job 日志、读取发布单与机器日志；旧版 `RetryPipelineJobRun` 是 AK 签名 API，不能假设 PAT 路由可用。优先调用实际可用的目标重试 API；不可用时记录原因，再决定是否重跑完整矩阵。
- 固定区域基址为 `https://jingzhun-cn-hangzhou.devops.aliyuncs.com/oapi/v1/flow`。触发 run 的 `params` 是单层 JSON 字符串，不要二次 `tojson`。

## 5. 失败分类与停止条件

| 现象 | 分类 | 处理 |
| --- | --- | --- |
| clone 白名单、Packages 权限、Python/编译器、媒体二进制失败 | 基础设施 | 修复有直接证据的根因；不得原样重跑，同一根因最多一次重试 |
| typecheck、单测、构建、Tailwind/设计系统检查失败 | 代码 | 不放宽门禁；提交最小修复后继并冻结新 SHA |
| 同一 SHA、同一命令曾成功，单个时序断言孤立失败 | 待判定波动 | 核对完整日志；允许一次不改门禁的复核，再失败则按代码处理 |
| tar 报告读取到自身或 checksum 漂移 | 制品构建 | 将输出放到源码树外的 run-scoped 临时目录后重跑 |
| 浏览器显示上传成功但 ECS 终端找不到文件 | 传输假阳性 | 作废该结果并回到 `publish-verified → VMDeploy`；普通部署不得自动换通道 |

分别记录并行门禁墙钟时间、排队时间和整体部署墙钟时间。并行能缩短关键路径，但每个 Job 独立 `npm ci`，不会自动减少累计核分。
