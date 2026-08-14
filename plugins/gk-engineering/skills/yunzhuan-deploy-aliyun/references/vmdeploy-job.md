# VMDeploy Job 契约

## 固定资源

- Flow：`1441793`
- 主机组名称：`video2-production`
- `machineGroup` UUID：`video2prod`
- 控制台数字 ID：`26793`
- ECS：`i-bp11prwf96sm8jc0agfu`
- 执行用户：`ecs-user`

这些值是 Video2 生产发布路径的一部分。每次部署前读取 Flow 持久化配置与主机组状态核对，不根据页面标题、历史截图或浏览器内未保存的编辑器内容推断。

## Job 拓扑与制品绑定

Flow 中必须存在等价配置：

```yaml
deploy_job:
  name: deploy · 主机组自动发布与验收
  needs:
    - publish_verified_job
  timeoutMinutes: 15
  component: VMDeploy
  with:
    downloadArtifact: true
    artifact: $[stages.verify_stage.build_release_job.upload_pending.artifacts.video2-${TARGET_SHA}]
    useEncode: false
    machineGroup: video2prod
    artifactDownloadPath: /tmp/video2-${PIPELINE_ID}-${BUILD_NUMBER}-${TARGET_SHA}.packages.tar.gz
    executeUser: ecs-user
    run: |
      set -Eeuo pipefail
      test "$(id -un)" = "ecs-user"
      : "${TARGET_SHA:?TARGET_SHA is required}"
      : "${PIPELINE_ID:?PIPELINE_ID is required}"
      : "${BUILD_NUMBER:?BUILD_NUMBER is required}"
      test "${#TARGET_SHA}" -eq 40

      package_path="/tmp/video2-${PIPELINE_ID}-${BUILD_NUMBER}-${TARGET_SHA}.packages.tar.gz"
      run_root="/tmp/video2-deploy-${PIPELINE_ID}-${BUILD_NUMBER}-${TARGET_SHA}"
      package_root="$run_root/package"
      staging_dir="$run_root/staging"
      inventory="$run_root/release.inventory"

      cleanup() {
        if [[ "$run_root" == "/tmp/video2-deploy-${PIPELINE_ID}-${BUILD_NUMBER}-${TARGET_SHA}" && -d "$run_root" && ! -L "$run_root" ]]; then
          rm -r -- "$run_root"
        fi
        rm -f -- "$package_path"
      }
      trap cleanup EXIT

      test -f "$package_path"
      test ! -e "$run_root"
      mkdir -m 755 "$run_root" "$package_root" "$staging_dir"
      tar -tzf "$package_path" >/dev/null
      tar -xzf "$package_path" -C "$package_root"

      release_name="video2-${PIPELINE_ID}-${BUILD_NUMBER}-${TARGET_SHA}.tar.gz"
      mapfile -t release_candidates < <(find "$package_root" -type f -name "$release_name" -print)
      mapfile -t checksum_candidates < <(find "$package_root" -type f -name "$release_name.sha256" -print)
      test "${#release_candidates[@]}" -eq 1
      test "${#checksum_candidates[@]}" -eq 1
      release_tar="${release_candidates[0]}"
      checksum_file="${checksum_candidates[0]}"
      test "$(dirname "$release_tar")" = "$(dirname "$checksum_file")"
      (cd "$(dirname "$release_tar")" && sha256sum --check "$(basename "$checksum_file")")

      tar -tzf "$release_tar" > "$inventory"
      if grep -Eq '(^|/)(\.env|data/|storage/|.*\.sqlite([.-]|$)|id_(rsa|ed25519))' "$inventory"; then
        echo 'Protected state or credentials found in verified release' >&2
        exit 65
      fi
      tar -xzf "$release_tar" -C "$staging_dir"
      test "$(tr -d '[:space:]' < "$staging_dir/.video2-build-commit")" = "$TARGET_SHA"
      test -f "$staging_dir/dist/app/index.html"

      env RUNNER_TRACKING_ID= \
        VIDEO2_WORKFLOW_RUNTIME_DOMAIN_AGENT_VIDEO=mastra \
        VIDEO2_MEMORY_RUNTIME=mastra \
        bash "$staging_dir/scripts/deploy-aliyun-release.sh" "$TARGET_SHA" "$staging_dir" prebuilt \
        2>&1 | tee "$run_root/deploy.log"

      env VIDEO2_WORKFLOW_RUNTIME_DOMAIN_AGENT_VIDEO=mastra \
        VIDEO2_MEMORY_RUNTIME=mastra \
        bash "/opt/video2/releases/$TARGET_SHA/scripts/verify-aliyun-runtime.sh" "$TARGET_SHA"

      public_status="$(curl --fail --silent --show-error --max-time 15 --output /dev/null --write-out '%{http_code}' https://47.98.184.79/)"
      test "$public_status" = "200"
      printf 'Browserless deployment verified: sha=%s public_https=%s\n' "$TARGET_SHA" "$public_status"
```

必须先使用云效编辑器的“校验”，再“仅保存”，随后从流水线详情接口重新读取已持久化 `flow`。只有接口返回的配置同时包含上述依赖、制品引用、主机组、用户和验收标记，才算配置完成。配置工作不得点击“保存并运行”。

## 失败关闭

如果 `VMDeploy` 配置校验失败、制品引用不存在、`video2-production` Runner 不是 `ok`、机器安装不是 `Finished` 或直接传输失败：

1. 报告具体基础设施阻塞；
2. 停止本次部署；
3. 不打开 Workbench，不进行浏览器上传，不自动切换 Cloud Assistant；
4. 仅在用户看到阻塞证据后明确授权单次紧急恢复时，另行执行并清楚标记例外路径。

这条失败关闭规则保证普通部署不会因为主路径故障而悄悄退回浏览器。
