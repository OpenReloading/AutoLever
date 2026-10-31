"""The install retry wrapper of the CI workflow: one retry, a time limit per attempt."""
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".github" / "scripts" / "retry-once.sh"


def run(limit: str, *cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(SCRIPT), limit, *cmd],
        capture_output=True, text=True, timeout=60, check=False,
        env={**os.environ, "RETRY_PAUSE": "0"},
    )


def test_first_success_runs_once(tmp_path: Path):
    count = tmp_path / "count"
    assert run("5", "sh", "-c", f"echo x >> {count}").returncode == 0
    assert len(count.read_text().split()) == 1


def test_failure_is_retried_once(tmp_path: Path):
    count = tmp_path / "count"
    result = run("5", "sh", "-c", f"echo x >> {count}; [ $(wc -l < {count}) -ge 2 ]")
    assert result.returncode == 0
    assert len(count.read_text().split()) == 2


def test_stall_times_out_and_fails_after_two_attempts(tmp_path: Path):
    count = tmp_path / "count"
    result = run("1", "sh", "-c", f"echo x >> {count}; sleep 30")
    assert result.returncode == 1
    assert len(count.read_text().split()) == 2


def test_timeout_kills_descendants(tmp_path: Path):
    pidfile = tmp_path / "pid"
    run("1", "sh", "-c", f"sleep 30 & echo $! > {pidfile}; wait")
    pid = int(pidfile.read_text())
    assert subprocess.run(["kill", "-0", str(pid)], capture_output=True, check=False).returncode != 0


def test_apt_install_runs_the_wrapper_as_root():
    ci = (SCRIPT.parent.parent / "workflows" / "ci.yml").read_text()
    assert "run: sudo .github/scripts/retry-once.sh 180 sh -c 'apt-get update" in ci
