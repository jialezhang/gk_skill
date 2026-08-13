# 可信制品传输

## 目录

1. 通道优先级
2. Workbench fallback
3. ECS 落盘验证
4. 清理

## 1. 通道优先级

1. **云效主机部署/部署组**：让 `deploy needs [publish-verified]` 取得已晋级制品并在 ECS 执行发布脚本。首次配置后，后续部署不再依赖浏览器。
2. **阿里云云助手**：部署组未就绪时，用云助手向精确 staging 路径下发文件或执行受审计的下载与发布命令。
3. **Workbench 文件任务中心**：仅作临时 fallback。使用其 OSS 中转后由 ECS `curl` 拉取的专用链路。

不得把浏览器 Cookie、Bearer Token 或云效会话写入 ECS 命令、shell history 或部署日志。不得让 ECS 直接请求需要浏览器登录态的 Packages `/content` 地址；它可能返回小体积登录 HTML，而不是 Release。

## 2. Workbench fallback

使用 Workbench 时，必须取得以下三段证据：

- OSS 上传进度达到 100%；
- 文件任务状态为 `SUCCESS`，且 ECS `curl` 接收字节数等于本地 verified 文件大小；
- ECS 终端能够 `stat` 该精确路径并重新计算匹配的 SHA-256。

Workbench 页面包含两套上传实现。通用 Theia 隐藏控件可能返回 `file:///tmp/<name>` 或显示已选文件，但文件并未进入当前 ECS。以下信号都不能作为成功证据：

- `input[type=file]` 中存在文件名；
- 通用 `FileUploadService` 返回 `uploaded`；
- 文件管理树未刷新前显示临时节点；
- 浏览器本地下载完成。

如果 ECS 终端找不到文件，立即把该传输判为失败，不要继续解包或部署。改用 Workbench“文件任务中心”的 OSS→ECS curl 链路，或切回更高优先级通道。

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

## 4. 清理

部署验收完成后：

1. 先打印并盘点 ECS 与本地的精确 run-scoped staging、包装包和 Release tar。
2. 只删除本次 run 的临时文件；保留 Packages verified 制品、当前 Release 与上一回滚 Release。
3. 记录实际传输通道。若仍使用 Workbench fallback，明确把“配置部署组实现全自动下发”列为未完成的运维改进，不能把浏览器上传描述成最终自动化路线。
