#!/usr/bin/env python3
import subprocess
import json
import os
import signal
import sys
import argparse
from common.config import SYSTEMS
import uvicorn
from common.app import create_app

PID_FILE = ".mocks_pids.json"

def load_pids():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            return json.load(f)
    return {}

def save_pids(pids):
    with open(PID_FILE, "w") as f:
        json.dump(pids, f, indent=2)

def start_system(name, cfg):
    if name not in SYSTEMS:
        print(f"Система '{name}' не найдена")
        return
    cmd = [sys.executable, "run.py", "--run-single", name]
    log = open(f"{name}.log", "w")
    proc = subprocess.Popen(cmd, stdout=log, stderr=log, start_new_session=True)
    pids = load_pids()
    pids[name] = {"pid": proc.pid, "port": cfg["port"]}
    save_pids(pids)
    print(f"{name} запущен на порту {cfg['port']} (PID {proc.pid})")

def stop_system(name):
    pids = load_pids()
    if name in pids:
        try:
            os.kill(pids[name]["pid"], signal.SIGTERM)
            os.waitpid(pids[name]["pid"], 0)
        except:
            pass
        del pids[name]
        save_pids(pids)
        print(f"{name} остановлен")
    else:
        print(f"Система '{name}' не запущена")

def restart_system(name):
    stop_system(name)
    if name in SYSTEMS:
        start_system(name, SYSTEMS[name])

def start_all():
    for name, cfg in SYSTEMS.items():
        start_system(name, cfg)

def stop_all():
    for name in list(load_pids().keys()):
        stop_system(name)

def status():
    pids = load_pids()
    if not pids:
        print("Нет запущенных систем")
        return
    for name, info in pids.items():
        try:
            os.kill(info["pid"], 0)
            print(f"{name}: PID {info['pid']}, порт {info['port']}")
        except:
            print(f"{name}: PID {info['pid']} (не работает)")

def run_single_system(name):
    if name not in SYSTEMS:
        print(f"Неизвестная система: {name}")
        sys.exit(1)
    cfg = SYSTEMS[name]
    app = create_app(cfg["mocks_dir"])
    uvicorn.run(app, host="127.0.0.1", port=cfg["port"], reload=False)

def main():
    parser = argparse.ArgumentParser(description="Управление мок-системами")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Запустить все системы")
    group.add_argument("--system", help="Запустить одну систему")
    group.add_argument("--restart", help="Перезапустить (all или имя системы)")
    group.add_argument("--stop", help="Остановить (all или имя системы)")
    group.add_argument("--status", action="store_true", help="Показать статус")
    group.add_argument("--run-single", help="Внутренний аргумент: запуск одной системы")
    args = parser.parse_args()

    if args.run_single:
        run_single_system(args.run_single)
        return

    if args.all:
        start_all()
    elif args.system:
        if args.system in SYSTEMS:
            start_system(args.system, SYSTEMS[args.system])
        else:
            print(f"Система '{args.system}' не найдена в конфиге")
    elif args.restart:
        if args.restart == "all":
            for name in SYSTEMS:
                restart_system(name)
        elif args.restart in SYSTEMS:
            restart_system(args.restart)
        else:
            print(f"Система '{args.restart}' не найдена")
    elif args.stop:
        if args.stop == "all":
            stop_all()
        elif args.stop in SYSTEMS:
            stop_system(args.stop)
        else:
            print(f"Система '{args.stop}' не найдена")
    elif args.status:
        status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()