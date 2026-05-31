#!/usr/bin/env python3
"""一键启动所有前端项目（本地开发模式）"""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

FRONTENDS = [
    ("web-admin", "apps/web-admin", 5173),
    ("web-asset", "apps/web-asset", 5174),
    ("web-sales", "apps/web-sales", 5175),
]

processes: list[tuple[str, subprocess.Popen]] = []


def check_port(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def signal_handler(sig, frame):
    print("\n\n🛑 收到停止信号，正在关闭所有前端...")
    for name, proc in processes:
        if proc.poll() is None:
            proc.terminate()
            print(f"  已发送终止信号: {name}")
    for name, proc in processes:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            print(f"  强制结束: {name}")
    print("✅ 全部前端已停止")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    proj_root = Path(__file__).parent.parent
    print("=" * 50)
    print("🚀 前端项目一键启动")
    print("=" * 50)

    for name, workdir, port in FRONTENDS:
        web_dir = proj_root / workdir
        if not (web_dir / "package.json").exists():
            print(f"  ⚠️ 未找到 {name}")
            continue

        if check_port(port):
            print(f"  ⚠️ {name} 端口 {port} 已被占用，跳过")
            continue

        log_dir = proj_root / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"{name}.log"
        log_fp = open(log_file, "a")

        proc = subprocess.Popen(
            ["pnpm", "dev"],
            cwd=web_dir,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
        )
        processes.append((name, proc))
        print(f"  ✅ {name} 已启动 (端口 {port})")

    print("\n" + "=" * 50)
    print("📊 前端访问地址")
    print("=" * 50)
    for name, _, port in FRONTENDS:
        if check_port(port):
            print(f"  🌐 {name:20s} http://localhost:{port}")
    print("\n📁 日志目录: kk-ai/logs/")
    print("🛑 停止方式: 在本窗口按 Ctrl+C")
    print("\n按 Ctrl+C 停止所有前端...\n")

    while True:
        time.sleep(1)
        for name, proc in list(processes):
            if proc.poll() is not None and proc.poll() != 0:
                print(f"⚠️ {name} 异常退出 (code={proc.poll()})")


if __name__ == "__main__":
    main()
