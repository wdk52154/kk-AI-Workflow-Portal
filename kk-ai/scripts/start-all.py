#!/usr/bin/env python3
"""一键启动 AI 中台全部服务（本地开发模式）

包含：阶段一 MCP 中台 + 阶段二 B 端赋能 + 阶段三 C 端产品
"""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

# 服务配置: (名称, 目录, 启动命令, 端口)
PHASE1_BASE = [
    ("service-llm",   "services/service-llm",   ["python", "run.py"], 9001),
    ("service-prompt","services/service-prompt",["python", "run.py"], 9004),
]

PHASE2_DEP = [
    ("service-rag",   "services/service-rag",   ["python", "run.py"], 9002),
    ("service-memory","services/service-memory",["python", "run.py"], 9003),
]

PHASE3_HUB = [
    ("service-data",  "services/service-data",  ["python", "run.py"], 9005),
    ("mcp-hub",       "services/mcp-hub",       ["python", "run.py"], 8000),
]

PHASE4_B = [
    ("service-asset", "services/service-asset", ["python", "run.py"], 9006),
    ("service-sales", "services/service-sales", ["python", "run.py"], 9007),
]

PHASE5_C = [
    ("service-voice", "services/service-voice", ["python", "run.py"], 9008),
    ("service-content","services/service-content",["python", "run.py"], 9009),
    ("service-live",  "services/service-live",  ["python", "run.py"], 9011),
]

ALL_SERVICES = PHASE1_BASE + PHASE2_DEP + PHASE3_HUB + PHASE4_B + PHASE5_C

FRONTENDS = [
    ("web-admin",   "apps/web-admin",   5173),
    ("web-asset",   "apps/web-asset",   5174),
    ("web-sales",   "apps/web-sales",   5175),
    ("web-voice",   "apps/web-voice",   5176),
    ("web-content", "apps/web-content", 5177),
    ("web-live",    "apps/web-live",    5178),
]

processes: list[tuple[str, subprocess.Popen]] = []


def check_port(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def wait_for_port(port: int, timeout: int = 30) -> bool:
    for _ in range(timeout * 2):
        if check_port(port):
            return True
        time.sleep(0.5)
    return False


def start_service(name: str, workdir: str, cmd: list[str], port: int) -> subprocess.Popen | None:
    if check_port(port):
        print(f"  ⚠️  {name} 端口 {port} 已被占用，跳过")
        return None

    proj_root = Path(__file__).parent.parent
    service_dir = proj_root / workdir
    log_dir = proj_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{name}.log"

    env = os.environ.copy()
    env["LLM_GATEWAY_URL"] = "http://localhost:9001"
    env["RAG_SERVICE_URL"] = "http://localhost:9002"
    env["MEMORY_SERVICE_URL"] = "http://localhost:9003"
    env["MCPHUB_REDIS_URL"] = "redis://localhost:6379/0"

    log_fp = open(log_file, "a")
    proc = subprocess.Popen(
        cmd,
        cwd=service_dir,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        env=env,
    )
    return proc


def start_frontend(name: str, workdir: str, port: int) -> subprocess.Popen | None:
    if check_port(port):
        print(f"  ⚠️  {name} 端口 {port} 已被占用，跳过")
        return None

    proj_root = Path(__file__).parent.parent
    web_dir = proj_root / workdir
    if not (web_dir / "package.json").exists():
        print(f"  ⚠️  未找到 {name}")
        return None

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
    return proc


def signal_handler(sig, frame):
    print("\n\n🛑 收到停止信号，正在关闭全部服务...")
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
    print("✅ 全部服务已停止")
    sys.exit(0)


def start_phase(phase_name: str, services: list):
    print(f"\n📦 {phase_name}")
    for name, workdir, cmd, port in services:
        print(f"  启动 {name} (端口 {port})...")
        proc = start_service(name, workdir, cmd, port)
        if proc:
            processes.append((name, proc))
    for name, workdir, cmd, port in services:
        if any(p[0] == name for p in processes):
            print(f"  ⏳ 等待 {name} 就绪...")
            if wait_for_port(port):
                print(f"  ✅ {name} 已就绪")
            else:
                print(f"  ❌ {name} 启动超时")


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("🚀 康康 AI 全栈系统一键启动")
    print("   阶段一 MCP 中台 + 阶段二 B 端赋能 + 阶段三 C 端产品")
    print("=" * 60)

    start_phase("Phase 1: 启动基础服务 (LLM + Prompt)", PHASE1_BASE)
    start_phase("Phase 2: 启动依赖服务 (RAG + Memory)", PHASE2_DEP)
    start_phase("Phase 3: 启动中台网关 (Data + MCP HUB)", PHASE3_HUB)
    start_phase("Phase 4: 启动 B 端服务 (Asset + Sales)", PHASE4_B)
    start_phase("Phase 5: 启动 C 端服务 (Voice + Content + Live)", PHASE5_C)

    print("\n📦 Phase 6: 启动前端项目...")
    for name, workdir, port in FRONTENDS:
        proc = start_frontend(name, workdir, port)
        if proc:
            processes.append((name, proc))
            print(f"  ✅ {name} 已启动 (端口 {port})")
            print(f"     访问: http://localhost:{port}")

    # 状态汇总
    print("\n" + "=" * 60)
    print("📊 服务状态汇总")
    print("=" * 60)

    backend_ok = 0
    backend_total = len(ALL_SERVICES)
    for name, _, _, port in ALL_SERVICES:
        ok = check_port(port)
        status = "✅" if ok else "❌"
        print(f"  {status} {name:22s} 端口 {port:5d}")
        if ok:
            backend_ok += 1

    print("-" * 60)
    frontend_ok = 0
    frontend_total = len(FRONTENDS)
    for name, _, port in FRONTENDS:
        ok = check_port(port)
        status = "✅" if ok else "❌"
        print(f"  {status} {name:22s} 端口 {port:5d}")
        if ok:
            frontend_ok += 1

    print("=" * 60)
    total_ok = backend_ok + frontend_ok
    total = backend_total + frontend_total
    print(f"🎉 启动完成：后端 {backend_ok}/{backend_total}，前端 {frontend_ok}/{frontend_total}")
    if total_ok == total:
        print("🎊 全部服务启动成功！")
    else:
        print("⚠️  部分服务未启动，请查看 logs/ 目录")
    print("=" * 60)
    print("\n📁 日志目录: kk-ai/logs/")
    print("🛑 停止方式: 在本窗口按 Ctrl+C")
    print("\n按 Ctrl+C 停止所有服务...\n")

    while True:
        time.sleep(1)
        for name, proc in list(processes):
            if proc.poll() is not None and proc.poll() != 0:
                print(f"⚠️ {name} 异常退出 (code={proc.poll()})")


if __name__ == "__main__":
    main()
