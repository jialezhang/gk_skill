# 云效并行门禁参考

## 目录

1. Job 拓扑
2. 公共前置断言
3. 各 Job 命令
4. 制品与晋级契约
5. 并发、超时与计费

## 1. Job 拓扑

将质量检查放在同一个验证 Stage。云效 YAML 中，同一 Stage 下未声明相互 `needs` 的 Job 默认并行：

```text
verify stage
├── quality
├── test-1
├── test-2
├── test-3
├── test-4
├── test-media
└── build-release ── upload pending artifact
          │
          └──────────────┐
                         ▼
publish-verified needs [quality, test-1, test-2, test-3, test-4, test-media, build-release]
                         │
                         ▼
deploy needs [publish-verified]
```

不要在七个验证 Job 之间建立串行依赖。仅 `publish-verified` 汇合所有结果，`deploy` 再依赖可信制品晋级。

若当前公共集群最大并发为 3，保留七个 Job；平台会先运行三个并在空闲后补位。这样仍比一个串行 Job 更快，也保持每个门禁可独立观察和重跑。

## 2. 公共前置断言

每个验证 Job 都先执行等价检查：

```bash
set -Eeuo pipefail

: "${TARGET_SHA:?TARGET_SHA is required}"
test "${#TARGET_SHA}" -eq 40
test "$(git rev-parse HEAD)" = "$TARGET_SHA"
test -z "$(git status --porcelain)"

node_major="$(node --version | sed -E 's/^v([0-9]+).*/\1/')"
test "$node_major" = "22"
python3 - <<'PY'
import sys
assert sys.version_info >= (3, 8), sys.version
PY
command -v make >/dev/null
command -v gcc >/dev/null
command -v g++ >/dev/null
npm ci
```

流水线源必须固定在 `ci-target-<TARGET_SHA_SHORT>`，环境变量保存完整 `TARGET_SHA`。分支名只能帮助定位，不能代替 SHA 断言。公共 Alinux 3 配置使用 `python38`；完整环境要求见 [云效环境预检](yunxiao-readiness.md)。

## 3. 各 Job 命令

### quality

```bash
set -Eeuo pipefail
npm run typecheck
git diff --check
npm audit --omit=dev --audit-level=critical
```

`npm audit` 可以报告 low/moderate/high，但仅 critical 阻止当前发布。完整报告仍进入运行证据和风险摘要。

### test-1 至 test-4

每个 Job 只替换 `SHARD` 的值：

```bash
set -Eeuo pipefail
SHARD=1
mkdir -p tmp/storage-owner
npm test -- \
  --shard="${SHARD}/4" \
  --exclude='src/tests/{aliyunNlsTranscriber,copilotWorkflowRunner,experimentVisualMedia,openAiCompatibleProvider,videoBreakdownMedia}.test.ts'
```

四个 Job 的 `SHARD` 必须恰好为 `1 2 3 4`，不能重复或缺失。保持 `fail-fast` 关闭或等价行为，让全部失败证据可见，但后续晋级仍要求全部成功。

### test-media

```bash
set -Eeuo pipefail
bash scripts/install-ci-media-dependencies.sh
mkdir -p tmp/storage-owner
npm test -- --run \
  src/tests/aliyunNlsTranscriber.test.ts \
  src/tests/copilotWorkflowRunner.test.ts \
  src/tests/experimentVisualMedia.test.ts \
  src/tests/openAiCompatibleProvider.test.ts \
  src/tests/videoBreakdownMedia.test.ts
```

媒体依赖脚本必须保留独立短超时和有限重试。不要在公共容器内使用需要交互密码的 `sudo`。

公共镜像无法稳定提供系统 FFmpeg 时，将 `@ffmpeg-installer/linux-x64@4.1.0` 与 `@ffprobe-installer/linux-x64@5.2.0` 安装到 Job 独占临时目录，并让依赖预检明确输出所用二进制路径。不要把该目录打进 Release。

### build-release

```bash
set -Eeuo pipefail
: "${TARGET_SHA:?TARGET_SHA is required}"
: "${RUN_ID:?RUN_ID is required}"

npm run build
test -f dist/app/index.html
printf '%s\n' "$TARGET_SHA" > .video2-build-commit

artifact_dir="$(mktemp -d)"
artifact="${artifact_dir}/video2-${RUN_ID}-${TARGET_SHA}.tar.gz"
checksum="${artifact}.sha256"

tar \
  --exclude='./.git' \
  --exclude='./.env' \
  --exclude='./node_modules' \
  --exclude='./data' \
  --exclude='./storage' \
  --exclude='./tmp' \
  --exclude='./logs' \
  --exclude='./coverage' \
  --exclude='./playwright-report' \
  --exclude='./test-results' \
  -czf "$artifact" .

sha256sum "$artifact" > "$checksum"
```

通过云效 `ArtifactUpload` 或当前版本等价的制品上传步骤保存 tar 和 checksum。输出目录必须位于源码树之外，避免 tar 在归档时读取自身。制品名称必须同时包含 run ID 与完整 SHA，防止不同 run 或分支碰撞。

## 4. 制品与晋级契约

`publish-verified` 使用 `needs` 等待七个 Job。不要使用 `continueOnFail`、`always` 后无条件发布，或仅检查构建 Job。

下载 pending artifact 后执行：

```bash
set -Eeuo pipefail
sha256sum --check "video2-${RUN_ID}-${TARGET_SHA}.tar.gz.sha256"

inventory="$(mktemp)"
tar -tzf "video2-${RUN_ID}-${TARGET_SHA}.tar.gz" > "$inventory"

grep -Fxq './.video2-build-commit' "$inventory"
grep -Fxq './dist/app/index.html' "$inventory"
if grep -Eq '(^|/)(\.env|data/|storage/|.*\.sqlite([.-]|$)|id_(rsa|ed25519))' "$inventory"; then
  echo 'Protected state or credentials found in artifact' >&2
  exit 65
fi

staging="$(mktemp -d)"
tar -xzf "video2-${RUN_ID}-${TARGET_SHA}.tar.gz" -C "$staging"
test "$(tr -d '[:space:]' < "$staging/.video2-build-commit")" = "$TARGET_SHA"
test -f "$staging/dist/app/index.html"
```

不要在 `set -o pipefail` 下使用 `tar -tzf ... | grep -q`；`grep` 提前退出可能让 `tar` 因 SIGPIPE 返回失败。先完整生成清单再检查。

晋级记录至少绑定：`RUN_ID`、`TARGET_SHA`、artifact 名称、SHA-256、七个 Job 的 success 状态。只有该记录存在时，部署步骤才能取得制品。

若 Packages 下载结果是包含 Release tar 与 checksum 的外层包装包，先解开包装包再执行上述校验；不要对包装包本身读取 `.video2-build-commit`。

## 5. 并发、超时与计费

- 从“Flow → 资源用量”读取当前组织的最大公共任务并发数。不要根据套餐宣传页猜测实际配额。
- 基础并发为 3 时，七个 Job 会分批运行；开通按量计费或套餐支持弹性伸缩时可同时启动更多 Job。
- 公共集群按任务实际运行的 CPU 核数 × 分钟计核分。并行主要缩短墙钟时间，不会自动减少累计核分；独立 `npm ci` 可能略微增加核分。
- Job 排队时间不应记为构建核分，但必须计入整体发布墙钟时间。
- 初始超时建议：quality 15 分钟、普通 shard 各 30 分钟、media 20 分钟、build 15 分钟、publish 5 分钟。根据连续成功运行的 P95 调整，不要统一放大到 90 分钟。
- 同一基础设施原因连续失败三次时停止剩余矩阵，诊断公共故障；不要继续消耗核分制造重复证据。
