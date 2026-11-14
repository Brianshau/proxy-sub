# -*- coding: utf-8 -*-
"""
一键部署到 GitHub：建仓库 -> 推送代码 -> 触发首次 Actions 运行

用法（令牌只从环境变量读取，不写入任何文件）:
    GITHUB_TOKEN=xxx REPO_NAME=proxy-sub python deploy_gh.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

TOKEN = (os.environ.get("GITHUB_TOKEN") or "").strip()
REPO = (os.environ.get("REPO_NAME") or "proxy-sub").strip()
DESC = "代理节点池每日自动整合订阅 (GitHub Actions)"
ROOT = os.path.dirname(os.path.abspath(__file__))
API = "https://api.github.com"


def req(path, method="GET", body=None, raw=False):
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "deploy-script",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            payload = resp.read().decode()
            return resp.status, (payload if raw else json.loads(payload or "{}"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def sh(cmd, cwd=ROOT, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        print(f"[git] {' '.join(cmd[:3])} 失败: {p.stderr.strip()[:400]}", file=sys.stderr)
        sys.exit(1)
    return p.stdout.strip()


def main():
    if not TOKEN:
        print("缺少 GITHUB_TOKEN 环境变量", file=sys.stderr)
        sys.exit(2)

    print("[1/6] 校验令牌 ...")
    code, me = req("/user")
    if code != 200:
        print(f"  令牌无效或权限不足 (HTTP {code}): {me.get('message')}", file=sys.stderr)
        sys.exit(3)
    login = me["login"]
    print(f"  已认证为 {login}")

    print(f"[2/6] 检查仓库 {login}/{REPO} ...")
    code, info = req(f"/repos/{login}/{REPO}")
    if code == 200:
        print("  仓库已存在，直接沿用")
        html = info["html_url"]
    else:
        print("  仓库不存在，开始创建 ...")
        code, info = req("/user/repos", "POST", {
            "name": REPO, "description": DESC, "private": False,
            "auto_init": False, "has_issues": False, "has_wiki": False,
        })
        if code not in (200, 201):
            print(f"  创建失败 (HTTP {code}): {info.get('message')}", file=sys.stderr)
            print("  提示：经典令牌需要勾选 repo + workflow；细粒度令牌需要"
                  "「All repositories」+ Administration: Read and write", file=sys.stderr)
            sys.exit(4)
        html = info["html_url"]
        print(f"  已创建: {html}")

    print("[3/6] 初始化本地 git 仓库 ...")
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        sh(["git", "init", "-b", "main"])
    sh(["git", "config", "user.name", login])
    sh(["git", "config", "user.email", f"{login}@users.noreply.github.com"])
    sh(["git", "add", "-A"])
    has_commit = subprocess.run(["git", "rev-parse", "--verify", "HEAD"],
                                cwd=ROOT, capture_output=True).returncode == 0
    if not has_commit:
        sh(["git", "commit", "-m", "feat: 代理节点池每日整合订阅"])
    else:
        p = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
        if p.returncode != 0:
            sh(["git", "commit", "-m", "chore: 更新脚本"])

    print("[4/6] 推送到 GitHub ...")
    push_url = f"https://x-access-token:{TOKEN}@github.com/{login}/{REPO}.git"
    sh(["git", "remote", "remove", "origin"], check=False)
    sh(["git", "remote", "add", "origin", push_url])
    sh(["git", "push", "-u", "origin", "main", "--force"])
    # 立刻把带令牌的地址换掉，避免留在 .git/config
    sh(["git", "remote", "set-url", "origin", f"https://github.com/{login}/{REPO}.git"])

    print("[5/6] 触发首次运行 ...")
    time.sleep(4)
    code, r = req(f"/repos/{login}/{REPO}/actions/workflows/daily.yml/dispatches",
                  "POST", {"ref": "main"})
    if code == 204:
        print("  已触发 daily-subscription")
    else:
        print(f"  触发返回 HTTP {code}: {r.get('message')}", file=sys.stderr)
        print("  （可在仓库 Actions 页面手动点 Run workflow）", file=sys.stderr)

    print("[6/6] 完成")
    base = f"https://cdn.jsdelivr.net/gh/{login}/{REPO}@main"
    print(f"""
  仓库      : {html}
  订阅地址  : {base}/sub/clash.yaml
  原始地址  : https://raw.githubusercontent.com/{login}/{REPO}/main/sub/clash.yaml
  测速报告  : {base}/reports/latest.md
  Actions  : {html}/actions
""")
    open(os.path.join(ROOT, "DEPLOY_INFO.txt"), "w", encoding="utf-8").write(
        f"repo={html}\nsub={base}/sub/clash.yaml\n"
        f"raw=https://raw.githubusercontent.com/{login}/{REPO}/main/sub/clash.yaml\n"
        f"report={base}/reports/latest.md\n")


if __name__ == "__main__":
    main()
