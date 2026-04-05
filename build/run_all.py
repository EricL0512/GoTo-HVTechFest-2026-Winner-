#!/usr/bin/env python3
"""
Run the full GoTo build pipeline in the correct order.
Each script enriches app/index.html with real computed data.

Usage:
    python run_all.py path/to/app/index.html
    python run_all.py                          # prompts for path, defaults to ../app/index.html
"""
import subprocess, sys, os

scripts = [
    "reroute_suggestions.py",
    "add_dest_scoring.py",
    "add_cost_distance.py",
    "add_overlap.py",
    "inject_road_paths.py",
    "inject_transit_times.py",
]

if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    default = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "index.html"))
    user_input = input(f"Path to index.html [{default}]: ").strip()
    path = user_input or default

path = os.path.abspath(path)

if not os.path.exists(path):
    print(f"Error: file not found at {path}")
    sys.exit(1)

print(f"Target: {path}\n")

for script in scripts:
    script_path = os.path.join(os.path.dirname(__file__), script)
    print(f"── Running {script} ──")
    result = subprocess.run([sys.executable, script_path, path], check=False)
    if result.returncode != 0:
        print(f"\nError: {script} failed. Stopping pipeline.")
        sys.exit(1)
    print()

print("✓ Build complete")
