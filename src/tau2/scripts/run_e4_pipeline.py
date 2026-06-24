from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

TASK_IDS = ["3", "8", "10", "11", "14", "16", "19", "21", "22", "23"]
ROOT = Path.cwd()
SIM_DIR = ROOT / "data" / "simulations"
FINAL_DIR = ROOT / "data" / "tau2" / "domains" / "ecommerce_calle" / "simulations"
B_PATH = SIM_DIR / "sim_e4_B_headers_k3.json"
C_PATH = SIM_DIR / "sim_e4_C_fixed_k3.json"
D_PATH = SIM_DIR / "sim_e4_D_best_think.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def simulation_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(load_json(path).get("simulations", []))


def wait_until_complete(path: Path, poll_seconds: int = 60) -> None:
    while simulation_count(path) < 50:
        count = simulation_count(path)
        print(f"waiting_for {path.name} count={count}/50", flush=True)
        time.sleep(poll_seconds)
    print(f"completed_file {path.name}", flush=True)


def run_condition(*args: str) -> None:
    cmd = [sys.executable, "-m", "tau2.scripts.run_e4_ecommerce_calle", *args]
    print("running", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def summarize(path: Path) -> dict:
    data = load_json(path)
    sims = data.get("simulations", [])
    by_task: dict[str, list[float]] = defaultdict(list)
    success_count = 0
    for sim in sims:
        reward = float(((sim.get("reward_info") or {}).get("reward")) or 0.0)
        by_task[str(sim.get("task_id"))].append(reward)
        if reward >= 1.0:
            success_count += 1
    pass5_tasks = sum(
        1 for task_id in TASK_IDS if len(by_task[task_id]) == 5 and sum(by_task[task_id]) >= 5.0
    )
    return {
        "path": str(path),
        "successful_trajectories": success_count,
        "total_trajectories": len(sims),
        "pass5_tasks": pass5_tasks,
    }


def choose_best_chunking() -> str:
    b = summarize(B_PATH)
    c = summarize(C_PATH)
    print("summary_B", b, flush=True)
    print("summary_C", c, flush=True)
    if c["successful_trajectories"] > b["successful_trajectories"]:
        return "fixed_200"
    if c["successful_trajectories"] < b["successful_trajectories"]:
        return "headers"
    if c["pass5_tasks"] > b["pass5_tasks"]:
        return "fixed_200"
    return "headers"


def copy_final_outputs() -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    for src in [B_PATH, C_PATH, D_PATH]:
        if src.exists():
            shutil.copy2(src, FINAL_DIR / src.name)


def main() -> None:
    wait_until_complete(B_PATH)
    if simulation_count(C_PATH) < 50:
        run_condition("--condition", "C", "--chunking-strategy", "fixed_200")
    wait_until_complete(C_PATH)
    best_strategy = choose_best_chunking()
    if simulation_count(D_PATH) < 50:
        run_condition("--condition", "D", "--chunking-strategy", best_strategy)
    wait_until_complete(D_PATH)
    copy_final_outputs()
    print("pipeline_complete", flush=True)


if __name__ == "__main__":
    main()
