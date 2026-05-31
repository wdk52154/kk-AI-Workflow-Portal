#!/usr/bin/env python3
"""一键启动 AI 中台全部服务（本地开发模式）"""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

# 服务配置: (名称, 目录, 启动命令, 端口, 健康检查路径)
SERVICES = [
    ("service-llm", "services/service-llm", ["python", "run.py"], 9001, "/health"),
    ("service-rag", "services/service-rag", ["python", "run.py"], 9002, "/health"),
    ("service-memory", "services/service-memory", ["python", "run.py"], 9003, "/health"),
    ("service-prompt", "services/service-prompt", ["python", "run.py"], 9004, "/health"),
    ("service-data", "services/service-data", ["python", "run.py"], 9005, "/health"),
    ("mcp-hub", "services/mcp-hub", ["python", "run.py"], 8000, "/health"),
]

# 全局进程列表
processes: list[tuple[str, subprocess.Popen]] = []


def check_port(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def wait_for_port(port: int, timeout: int = 30) -> bool:
    """等待端口就绪"""
    for _ in range(timeout * 2):
        if check_port(port):
            return True
        time.sleep(0.5)
    return False


def start_service(name: str, workdir: str, cmd: list[str], port: int) -> subprocess.Popen | None:
    """启动单个服务"""
    if check_port(port):
        print(f"  ⚠️  {name} 端口 {port} 已被占用，跳过")
        return None

    proj_root = Path(__file__).parent.parent
    service_dir = proj_root / workdir
    log_dir = proj_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{name}.log"

    env = os.environ.copy()
    # 服务间调用使用 localhost（本地模式）
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


def signal_handler(sig, frame):
    """Ctrl+C 时优雅停止所有服务"""
    print("\n\n🛑 收到停止信号，正在关闭所有服务...")
    for name, proc in processes:
        if proc.poll() is None:
            proc.terminate()
            print(f"  已发送终止信号: {name}")
    # 等待最多 5 秒
    for name, proc in processes:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            print(f"  强制结束: {name}")
    print("✅ 全部服务已停止")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    proj_root = Path(__file__).parent.parent
    print("=" * 50)
    print("🚀 AI 中台本地一键启动")
    print("=" * 50)

    # 阶段 1: 启动基础服务（无依赖）
    print("\n📦 Phase 1: 启动基础服务...")
    base_services = [s for s in SERVICES if s[0] in ("service-llm", "service-prompt")]
    for name, workdir, cmd, port, health in base_services:
        print(f"  启动 {name} (端口 {port})...")
        proc = start_service(name, workdir, cmd, port)
        if proc:
            processes.append((name, proc))

    # 等待基础服务就绪
    for name, workdir, cmd, port, health in base_services:
        if check_port(port):
            print(f"  ⏳ 等待 {name} 就绪...")
            if wait_for_port(port):
                print(f"  ✅ {name} 已就绪")
            else:
                print(f"  ❌ {name} 启动超时")

    # 阶段 2: 启动依赖服务
    print("\n📦 Phase 2: 启动依赖服务...")
    dep_services = [s for s in SERVICES if s[0] in ("service-rag", "service-memory")]
    for name, workdir, cmd, port, health in dep_services:
        print(f"  启动 {name} (端口 {port})...")
        proc = start_service(name, workdir, cmd, port)
        if proc:
            processes.append((name, proc))

    for name, workdir, cmd, port, health in dep_services:
        if any(p[0] == name for p in processes):
            print(f"  ⏳ 等待 {name} 就绪...")
            if wait_for_port(port):
                print(f"  ✅ {name} 已就绪")
            else:
                print(f"  ❌ {name} 启动超时")

    # 阶段 3: 启动 data center
    print("\n📦 Phase 3: 启动 Data Center...")
    data_service = [s for s in SERVICES if s[0] == "service-data"][0]
    name, workdir, cmd, port, health = data_service
    proc = start_service(name, workdir, cmd, port)
    if proc:
        processes.append((name, proc))
        if wait_for_port(port):
            print(f"  ✅ {name} 已就绪")

    # 阶段 4: 启动 mcp-hub
    print("\n📦 Phase 4: 启动 MCP HUB Gateway...")
    hub_service = [s for s in SERVICES if s[0] == "mcp-hub"][0]
    name, workdir, cmd, port, health = hub_service
    proc = start_service(name, workdir, cmd, port)
    if proc:
        processes.append((name, proc))
        if wait_for_port(port):
            print(f"  ✅ {name} 已就绪")

    # 阶段 5: 启动前端
    print("\n📦 Phase 5: 启动前端...")
    web_apps = [
        ("web-admin", 5173),
        ("web-asset", 5174),
        ("web-sales", 5175),
    ]
    for web_name, web_port in web_apps:
        web_dir = proj_root / "apps" / web_name
        if (web_dir / "package.json").exists():
            if check_port(web_port):
                print(f"  ⚠️ {web_name} 端口 {web_port} 已被占用，跳过")
                continue
            web_log = proj_root / "logs" / f"{web_name}.log"
            web_log_fp = open(web_log, "a")
            web_proc = subprocess.Popen(
                ["pnpm", "dev"],
                cwd=web_dir,
                stdout=web_log_fp,
                stderr=subprocess.STDOUT,
            )
            processes.append((web_name, web_proc))
            print(f"  ✅ {web_name} 已启动 (pnpm dev)")
            print(f"     访问: http://localhost:{web_port}")
        else:
            print(f"  ⚠️ 未找到 {web_name}")

    # 状态汇总
    print("\n" + "=" * 50)
    print("📊 服务状态汇总")
    print("=" * 50)
    all_ok = True
    for name, workdir, cmd, port, health in SERVICES:
        ok = check_port(port)
        status = "✅ 运行中" if ok else "❌ 未启动"
        print(f"  {name:20s} 端口 {port:4d}  {status}")
        if not ok:
            all_ok = False

    for web_name, web_port in web_apps:
        ok = check_port(web_port)
        status = "✅ 运行中" if ok else "❌ 未启动"
        print(f"  {web_name:20s} 端口 {web_port:4d}  {status}")

    print("\n" + "=" * 50)
    if all_ok:
        print("🎉 全部服务启动成功！")
    else:
        print("⚠️ 部分服务未启动，请查看 logs/ 目录")
    print("=" * 50)
    print("\n📁 日志目录: kk-ai/logs/")
    print("🛑 停止方式: 在本窗口按 Ctrl+C")
    print("\n按 Ctrl+C 停止所有服务...\n")

    # 保持主进程运行
    while True:
        time.sleep(1)
        # 检查是否有进程意外退出
        for name, proc in list(processes):
            if proc.poll() is not None and proc.poll() != 0:
                print(f"⚠️ {name} 异常退出 (code={proc.poll()})")


if __name__ == "__main__":
    main()
