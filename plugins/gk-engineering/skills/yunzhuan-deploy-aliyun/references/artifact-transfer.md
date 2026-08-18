# 无浏览器可信制品传输

## 目录

1. 唯一常态通道
2. 失败关闭与应急边界
3. ECS 落盘验证
4. 清理

## 1. 唯一常态通道

普通部署只允许云效 `VMDeploy`：`publish-verified` 成功后，平台把精确 Packages 包装制品直接下发到 `video2-production`（`machineGroup: video2prod`），并以 `ecs-user` 执行发布和验收。具体配置见 [VMDeploy Job 契约](vmdeploy-job.md)。

Packages 下载请求由 ECS 自己发出。确保独立 IP 组 `ecs-codeup-video2` 已启用，精确出口 `47.98.184.79` 只放行“代码管理”和“制品仓库”。机器日志出现 `NO_PERMISSION_IP_INSECURITY` 时，只按响应中的 client IP 修复该组；不要把 ECS IP 混入公共执行器组，也不要放行所有应用。

不得下载到本地，不得打开 Workbench，不得通过浏览器上传，不得自动改用 Cloud Assistant。直接路径不可用时应失败关闭，而不是选择第二通道。

不得把浏览器 Cookie、Bearer Token 或云效会话写入 ECS 命令、shell history 或部署日志。不得让 ECS 直接请求需要浏览器登录态的 Packages `/content` 地址；它可能返回小体积登录 HTML，而不是 Release。

## 2. 失败关闭与应急边界

只有用户在看到直接路径的具体阻塞证据后，明确授权“本次紧急恢复”，才可以单次启用 Workbench 文件任务中心或 Cloud Assistant。它们是人工应急，不是普通部署 fallback，也不得被写成默认优先级。

若用户明确授权 Workbench，应取得以下三段证据：

- OSS 上传进度达到 100%；
- 文件任务状态为 `SUCCESS`，且 ECS `curl` 接收字节数等于本地 verified 文件大小；
- ECS 终端能够 `stat` 该精确路径并重新计算匹配的 SHA-256。

Workbench 页面包含两套上传实现。通用 Theia 隐藏控件可能返回 `file:///tmp/<name>` 或显示已选文件，但文件并未进入当前 ECS。以下信号都不能作为成功证据：

- `input[type=file]` 中存在文件名；
- 通用 `FileUploadService` 返回 `uploaded`；
- 文件管理树未刷新前显示临时节点；
- 浏览器本地下载完成。

如果 ECS 终端找不到文件，立即把该传输判为失败，不要继续解包或部署。文件任务中心的 OSS→ECS curl 只能作为已获单次授权的应急证据，不能写回普通流程。

## 3. ECS 落盘验证

对精确 run-scoped 路径执行等价检查：

```bash
set -Eeuo pipefail

test -f "$ARTIFACT"
test "$(sha256sum "$ARTIFACT" | awk '{print $1}')" = "$EXPECTED_SHA256"
tar -tzf "$ARTIFACT" >/dev/null
```

如果 Packages 下载的是外层包装包，先解到本地或 staging 临时目录，要求其中恰好有目标 Release tar 和配套 checksum，再校验内层 Release。不要根据扩展名猜测层级。

解包后继续验证：

```bash
test "$(tr -d '[:space:]' < "$STAGING_DIR/.video2-build-commit")" = "$TARGET_SHA"
test -f "$STAGING_DIR/dist/app/index.html"
```

任何文件尺寸异常、gzip/tar 检查失败、HTML 登录页、checksum 不匹配或构建身份不符，都要删除该次传输文件并重新取得 verified 制品。

对 Release inventory 的敏感内容检查只匹配根目录：

```bash
if grep -Eq '^(\./)?(\.env($|\.[^/]+$|/)|data/|storage/|[^/]*\.sqlite([.-][^/]*)?$|id_(rsa|ed25519)($|/))' "$INVENTORY"; then
  exit 65
fi
```

不要匹配任意层级的 `data/` 或 `storage/`；这会误杀 `src/**/storage/` 和依赖包代码。

## 4. 清理

部署验收完成后：

1. 先打印并盘点 ECS 与本地的精确 run-scoped staging、包装包和 Release tar。
2. 只删除本次 run 的临时文件；保留 Packages verified 制品、当前 Release 与上一回滚 Release。
3. 记录 `VMDeploy`、主机组、Runner 与制品引用。若本次获授权使用应急通道，必须明确标记例外及其原因，不能把浏览器上传描述成自动化路线。
