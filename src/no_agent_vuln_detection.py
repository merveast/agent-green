#!/usr/bin/env python3
# ================================================================
# No-Agent Vulnerability Detection (Zero-Shot Only)
# ================================================================

import os
import time
import json
import config
import ollama
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
from log_utils import save_templates
from ollama_utils import start_ollama_server, stop_ollama_server
from vuln_evaluation import (
    evaluate_and_save_vulnerability,
    normalize_vulnerability_basic,
    normalize_vulnerability_conservative,
    normalize_vulnerability_strict,
)

# ================================================================
# CONFIGURATION
# ================================================================
llm_config = config.LLM_CONFIG
task = config.VULNERABILITY_TASK_PROMPT
sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT  #zero-shot only

LOG_DIR = config.LOG_DIR
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)
DATASET_FILE = config.VULN_DATASET

DESIGN = "NA-vuln_"
model = llm_config["config_list"][0]["model"]

temperature = llm_config["temperature"]
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

# ================================================================
# OLLAMA QUERY FUNCTION
# ================================================================
def ask_ollama(model, prompt):
    """Query Ollama model with a prompt"""
    try:
        response = ollama.generate(model=model, prompt=prompt, options={"temperature": temperature})
        return response.get("response", None)
    except ollama.ResponseError as e:
        print("Error:", e.error)
        return None

# ================================================================
# DATA LOADING
# ================================================================
def read_vulnerability_data(vuln_dataset_path):
    """Read vulnerability data from JSONL dataset"""
    with open(vuln_dataset_path, "r", encoding="utf-8") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

print(f"Loading dataset from {DATASET_FILE}")
vuln_data = read_vulnerability_data(DATASET_FILE)
print(f"Loaded {len(vuln_data)} samples.")

ground_truth = [v["target"] for v in vuln_data]

# ================================================================
# CORE EXECUTION
# ================================================================
def run_vulnerability_detection_with_emissions(vuln_data, model_name, sys_prompt, task, exp_name, result_dir):
    """Run vulnerability detection with emissions tracking"""
    results = []
    detailed_jsonl = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    detailed_csv = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")

    # Initialize CSV
    with open(detailed_csv, "w", encoding="utf-8") as f:
        f.write("idx,project,commit_id,ground_truth,response,timestamp\n")

    tracker = OfflineEmissionsTracker(
        project_name=exp_name, output_dir=result_dir, country_iso_code="CAN", save_to_file=True
    )
    tracker.start()

    try:
        for i, item in enumerate(vuln_data):
            print(f"\n--- Processing sample {i+1}/{len(vuln_data)} ---")

            formatted_prompt = sys_prompt + "\n\n" + task.format(code=item["func"])
            response = ask_ollama(model_name, formatted_prompt)

            record = {
                "idx": item.get("idx", i),
                "project": item.get("project", ""),
                "commit_id": item.get("commit_id", ""),
                "ground_truth": item.get("target", 0),
                "response": response or "",
                "timestamp": datetime.now().isoformat(),
            }
            results.append(record)

            with open(detailed_jsonl, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            # Append to CSV
            with open(detailed_csv, "a", encoding="utf-8") as f:
                safe = lambda x: str(x).replace(",", ";").replace("\n", " ")
                f.write(f"{record['idx']},{safe(record['project'])},{safe(record['commit_id'])},{record['ground_truth']},{safe(record['response'])},{record['timestamp']}\n")

    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO₂")

    return results

# ================================================================
# MAIN EXECUTION
# ================================================================
print(f"\nRunning {DESIGN} (ZERO_SHOT mode, direct model inference)...")
print(f"Model: {model}")
print(f"Temperature: {temperature}")
print(f"Experiment: {exp_name}")

proc = start_ollama_server()
time.sleep(5)

try:
    results = run_vulnerability_detection_with_emissions(
        vuln_data, model, sys_prompt, task, exp_name, RESULT_DIR
    )
    print(f"\nDetailed results saved incrementally to: {RESULT_DIR}/{exp_name}_detailed_results.jsonl")

    save_templates([r["response"] for r in results], llm_config, DESIGN, RESULT_DIR)

    print(f"Templates saved for experiment: {exp_name}")

finally:
    stop_ollama_server(proc)
    print("\nOllama server stopped.")

# ================================================================
# EVALUATION
# ================================================================
print("\n" + "=" * 60)
print("STARTING EVALUATIONS")
print("=" * 60)

predictions = [r["response"] for r in results]

for i, (fn, name) in enumerate(
    [
        (normalize_vulnerability_basic, "basic"),
        (normalize_vulnerability_conservative, "conservative"),
        (normalize_vulnerability_strict, "strict"),
    ],
    1,
):
    print(f"\n[{i}/3] Evaluating with {name} normalization...")
    try:
        eval_result = evaluate_and_save_vulnerability(fn, predictions, DATASET_FILE, f"{exp_name}_{name}")
        print(f"✓ {name.capitalize()} evaluation complete: Accuracy = {eval_result.get('accuracy', 0):.4f}")
    except Exception as e:
        print(f"✗ Error during {name} evaluation: {e}")

print("\n" + "=" * 60)
print("ALL EVALUATIONS COMPLETED")
print("=" * 60)
print(f"Results directory: {RESULT_DIR}")
print(f"Experiment name: {exp_name}")
