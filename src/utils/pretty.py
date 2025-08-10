# -*- coding: utf-8 -*-
import sys, time
from contextlib import contextmanager

RESET = "\033[0m"; BOLD = "\033[1m"; CYAN = "\033[36m"; GREEN = "\033[32m"; YELLOW = "\033[33m"

def log(msg: str):
    print(f"{CYAN}[RAG]{RESET} {msg}"); sys.stdout.flush()

def ok(msg: str):
    print(f"{GREEN}[OK]{RESET}  {msg}"); sys.stdout.flush()

def warn(msg: str):
    print(f"{YELLOW}[WARN]{RESET} {msg}"); sys.stdout.flush()

def section(title: str):
    print(f"\n{BOLD}{title}{RESET}"); sys.stdout.flush()

@contextmanager
def timer(label: str):
    t0 = time.perf_counter()
    log(f"{label} ...")
    try:
        yield
    finally:
        dt = time.perf_counter() - t0
        ok(f"{label} done in {dt:.2f}s")
