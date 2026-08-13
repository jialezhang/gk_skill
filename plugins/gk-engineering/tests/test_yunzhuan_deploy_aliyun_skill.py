#!/usr/bin/env python3
"""Contract checks for the Yunxiao-to-Aliyun deployment skill."""

from __future__ import annotations

from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "yunzhuan-deploy-aliyun"


def main() -> int:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    reference = (SKILL_ROOT / "references" / "parallel-gate.md").read_text(encoding="utf-8")
    readiness = (SKILL_ROOT / "references" / "yunxiao-readiness.md").read_text(
        encoding="utf-8"
    )
    transfer = (SKILL_ROOT / "references" / "artifact-transfer.md").read_text(
        encoding="utf-8"
    )
    all_text = skill + reference + readiness + transfer

    required_jobs = {
        "quality",
        "test-1",
        "test-2",
        "test-3",
        "test-4",
        "test-media",
        "build-release",
        "publish-verified",
    }
    missing_jobs = sorted(job for job in required_jobs if job not in all_text)
    assert not missing_jobs, f"missing parallel jobs: {missing_jobs}"

    required_contracts = {
        "TARGET_SHA",
        "git rev-parse HEAD",
        "npm ci",
        "--shard=\"${SHARD}/4\"",
        "npm audit --omit=dev --audit-level=critical",
        "dist/app/index.html",
        ".video2-build-commit",
        "sha256sum --check",
        "sudo -u ecs-user -H",
        "verify-aliyun-runtime.sh",
        "/proc/<pid>/cwd",
    }
    missing_contracts = sorted(item for item in required_contracts if item not in all_text)
    assert not missing_contracts, f"missing deployment contracts: {missing_contracts}"

    incident_contracts = {
        "116.62.173.28",
        "47.96.173.226",
        "代码管理",
        "制品仓库",
        "python38",
        "@ffmpeg-installer/linux-x64@4.1.0",
        "@ffprobe-installer/linux-x64@5.2.0",
        "源码树之外",
        "部署组",
        "OSS→ECS curl",
        "file:///tmp/<name>",
        "Bearer Token",
        "登录 HTML",
        "ECS 终端",
    }
    missing_incident_contracts = sorted(
        item for item in incident_contracts if item not in all_text
    )
    assert not missing_incident_contracts, (
        f"missing incident-derived contracts: {missing_incident_contracts}"
    )

    assert "continueOnFail" in skill
    assert "不得" in skill
    assert "present" in skill
    assert "root" in skill
    assert "基础设施失败" in skill and "代码失败" in skill
    assert "通用 Theia" in skill and "文件任务中心" in transfer
    assert "浏览器 Cookie" in transfer
    assert "data/" in reference and "storage/" in reference and ".env" in reference
    print("OK: yunzhuan-deploy-aliyun skill contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
