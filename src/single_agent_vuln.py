#!/usr/bin/env python3
# ================================================================
# Single-Agent Vulnerability Detection 
# ================================================================

import os
import json
import time
import argparse
from datetime import datetime
from autogen import AssistantAgent
from codecarbon import OfflineEmissionsTracker
from vuln_evaluation import evaluate_and_save_vulnerability, normalize_vulnerability_basic
from sklearn.metrics import classification_report, confusion_matrix
import config


# ================================================================
# CONFIGURATION
# ================================================================
llm_config = config.LLM_CONFIG
DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)


# ================================================================
# CLI ARGUMENT PARSING (Unified)
# ================================================================
parser = argparse.ArgumentParser(description="Run single-agent vulnerability detection")
parser.add_argument(
    "--prompt_type", choices=["zero_shot", "few_shot"], default="few_shot",
    help="Choose between zero_shot or few_shot prompting."
)
args = parser.parse_args()
prompt_type = args.prompt_type


# ================================================================
# EXPERIMENT NAMING
# ================================================================
DESIGN = f"SA-vuln-one-{prompt_type}"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"


# ================================================================
# AGENT CREATION
# ================================================================
def create_single_agent(llm_config, prompt_type):
    if prompt_type == "few_shot":
        sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT
        print("Using FEW-SHOT prompt for the single-agent vulnerability detector.")
    else:
        sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT
        print("Using ZERO-SHOT prompt for the single-agent vulnerability detector.")

    agent = AssistantAgent(
        name="vulnerability_detector_agent",
        system_message=sys_prompt,
        description="Analyze code functions to detect security vulnerabilities.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    return agent


# ================================================================
# DATASET LOADING
# ================================================================
def load_vulnerability_dataset(file_path):
    samples = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if "func" in data and "target" in data:
                    samples.append(data)
            except json.JSONDecodeError:
                continue
    return samples


# ================================================================
# FILE HANDLING
# ================================================================
def initialize_results_files(exp_name, result_dir):
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")

    with open(csv_file, "w") as f:
        f.write("idx,project,commit_id,ground_truth,vuln,reasoning,cwe,cve,cve_desc,timestamp\n")

    return detailed_file, csv_file


def append_result(result, detailed_file, csv_file):
    with open(detailed_file, "a") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    def esc(x):
        if x is None:
            return ""
        s = str(x)
        if "," in s or '"' in s or "\n" in s:
            return '"' + s.replace('"', '""') + '"'
        return s

    with open(csv_file, "a") as f:
        row = [
            esc(result.get("idx")),
            esc(result.get("project")),
            esc(result.get("commit_id")),
            esc(result.get("ground_truth")),
            esc(result.get("vuln")),
            esc(result.get("reasoning")),
            esc(result.get("cwe")),
            esc(result.get("cve")),
            esc(result.get("cve_desc")),
            esc(result.get("timestamp")),
        ]
        f.write(",".join(row) + "\n")


# ================================================================
# INFERENCE WITH EMISSIONS TRACKING
# ================================================================
def run_inference_with_emissions(samples, llm_config, exp_name, result_dir, prompt_type):
    detailed_file, csv_file = initialize_results_files(exp_name, result_dir)

    tracker = OfflineEmissionsTracker(
        project_name=exp_name, output_dir=result_dir, save_to_file=True, country_iso_code="CAN"
    )
    tracker.start()

    vuln_detector = create_single_agent(llm_config, prompt_type)
    results, errors = [], 0

    try:
        for i, s in enumerate(samples):
            print(f"\n--- Processing sample {i+1}/{len(samples)} ---")
            try:
                # task = config.VULNERABILITY_TASK_PROMPT.format(func=s["func"])
                task = config.VULNERABILITY_TASK_PROMPT.format(code=s["func"])

                response = vuln_detector.generate_reply(messages=[{"role": "user", "content": task}])

                # Parse response
                resp_text = response.get("content", "").strip() if isinstance(response, dict) else str(response).strip()
                resp_lower = resp_text.lower()

                if any(k in resp_lower for k in ["yes", "vulnerability detected", "(1) yes"]):
                    vuln = 1
                elif any(k in resp_lower for k in ["no", "no vulnerability", "(2) no"]):
                    vuln = 0
                else:
                    vuln = 1 if any(k in resp_lower for k in ["unsafe", "exploit", "overflow"]) else 0

                result = dict(s)
                result.update({
                    "vuln": vuln,
                    "reasoning": resp_text,
                    "timestamp": datetime.now().isoformat()
                })

                append_result(result, detailed_file, csv_file)
                results.append(result)
                print(f"Completed: vuln={vuln}, gt={s.get('target')}")

            except Exception as e:
                errors += 1
                print(f"Error: {e}")
                result = dict(s)
                result.update({
                    "vuln": 0,
                    "reasoning": f"ERROR: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "skipped": True
                })
                append_result(result, detailed_file, csv_file)
                results.append(result)

    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO₂")
        print(f"Errors encountered: {errors}")

    return results


# ================================================================
# MAIN EXECUTION
# ================================================================
def main():
    print("📂 Loading dataset...")
    samples = load_vulnerability_dataset(DATASET_FILE)
    print(f"Loaded {len(samples)} samples.")

    if not samples:
        print("No samples found, exiting.")
        return

    print(f"Running {DESIGN} ({prompt_type.upper()} mode, 1 agent 1 round)...")
    results = run_inference_with_emissions(samples, llm_config, exp_name, RESULT_DIR, prompt_type)

    # ==================== Inline Evaluation ====================
    preds = [r.get("vuln", 0) for r in results]
    gts = [r.get("target", 0) for r in results]
    acc = sum(p == g for p, g in zip(preds, gts)) / len(results) if results else 0

    cm = confusion_matrix(gts, preds)
    report = classification_report(gts, preds, target_names=["Not Vulnerable", "Vulnerable"])

    print("\n=== EVALUATION SUMMARY ===")
    print(f"Samples evaluated: {len(results)}")
    print(f"Accuracy: {acc:.4f}")
    print("\nConfusion Matrix:\n", cm)
    print("\nClassification Report:\n", report)

    detailed_file = os.path.join(RESULT_DIR, f"{exp_name}_detailed_results.jsonl")
    with open(detailed_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "evaluation_summary": {
                "accuracy": round(acc, 4),
                "confusion_matrix": cm.tolist(),
                "classification_report": report
            }
        }, ensure_ascii=False) + "\n")

    print(f"Evaluation results appended to: {detailed_file}")

    try:
        evaluate_and_save_vulnerability(normalize_vulnerability_basic, preds, DATASET_FILE, exp_name)
    except Exception as e:
        print(f"Evaluation skipped due to: {e}")

    print("\n=== FINAL SUMMARY ===")
    print(f"Samples processed: {len(results)}")
    print("Single-agent vulnerability detection completed successfully.")


if __name__ == "__main__":
    main()
