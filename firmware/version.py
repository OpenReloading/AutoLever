# Stamps the firmware with its version and commit, which the web page shows and links (AGPL section 13).
# ruff: noqa: F821 (Import and env are PlatformIO extra script globals)
import subprocess

Import("env")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=env["PROJECT_DIR"], check=True, capture_output=True, text=True
    ).stdout.strip()


env.Append(
    CPPDEFINES=[
        ("AUTOLEVER_VERSION", env.StringifyMacro(git("describe", "--tags", "--always", "--dirty"))),
        ("AUTOLEVER_COMMIT", env.StringifyMacro(git("rev-parse", "HEAD"))),
    ]
)
