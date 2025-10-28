#!/usr/bin/env python3
# ================================================================
# Dual-Agent Vulnerability Detection
# ================================================================

import os
import json
import argparse
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
from sklearn.metrics import classification_report, confusion_matrix

import config
from vuln_evaluation import evaluate_and_save_vulnerability, normalize_vulnerability_basic
from agent_utils_vuln import create_agent


# ================================================================
# CONFIGURATION
# ================================================================
llm_config = config.LLM_CONFIG
DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)


# ================================================================
# FILE UTILITIES
# ================================================================
def initialize_results_files(exp_name, result_dir, header_fields):
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")

    with open(csv_file, "w") as f:
        f.write(",".join(header_fields) + "\n")

    return detailed_file, csv_file


def append_result(result, detailed_file, csv_file, header_fields):
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
        row = [esc(result.get(h, "")) for h in header_fields]
        f.write(",".join(row) + "\n")


# ================================================================
# DECISION PARSER
# ================================================================
def extract_vulnerability_decision(response):
    """Extract (1=vulnerable, 0=safe) and reasoning text."""
    try:
        text = response.strip()
        if text.startswith("{") or text.startswith("["):
            data = json.loads(text)
            if isinstance(data, dict):
                decision = data.get("vulnerability_detected", False)
                reasoning = data.get("analysis", data.get("reasoning", text))
            elif isinstance(data, list):
                decision = any(d.get("vulnerability_detected", False) for d in data)
                reasoning = "; ".join(d.get("analysis", d.get("reasoning", "")) for d in data)
            else:
                decision, reasoning = False, text
        else:
            lowered = text.lower()
            decision = any(k in lowered for k in ["vulnerable", "unsafe", "security issue"])
            reasoning = text
        return (1 if decision else 0), reasoning
    except Exception as e:
        return 0, f"Error parsing: {e}"


# ================================================================
# AGENT CREATION
# ================================================================
def create_dual_agents(llm_config, prompt_type="zero_shot"):
    """Create Code Author + Security Analyst agents (few/zero shot)."""
    if prompt_type == "few_shot":
        code_author_prompt = config.SYS_MSG_CODE_AUTHOR_DUAL_FEW_SHOT
        analyst_prompt = config.SYS_MSG_SECURITY_ANALYST_FEW_SHOT
        print("Using FEW-SHOT prompts for both agents.")
    else:
        code_author_prompt = config.SYS_MSG_CODE_AUTHOR_DUAL_ZERO_SHOT
        analyst_prompt = config.SYS_MSG_SECURITY_ANALYST_ZERO_SHOT
        print("Using ZERO-SHOT prompts for both agents.")

    code_author = create_agent(
        "assistant", "code_author_agent", llm_config,
        sys_prompt=code_author_prompt,
        description="Explains or defends the code snippet."
    )

    security_analyst = create_agent(
        "assistant", "security_analyst_agent", llm_config,
        sys_prompt=analyst_prompt,
        description="Analyzes the code and produces final vulnerability decision."
    )

    return code_author, security_analyst


# ================================================================
# INFERENCE WITH EMISSIONS TRACKING
# ================================================================
def run_inference_with_emissions(samples, llm_config, exp_name, result_dir, prompt_type):
    dataset_keys = list(samples[0].keys()) if samples else []
    header_fields = dataset_keys + ["vuln", "reasoning", "timestamp"]
    detailed_file, csv_file = initialize_results_files(exp_name, result_dir, header_fields)

    tracker = OfflineEmissionsTracker(
        project_name=exp_name, output_dir=result_dir, save_to_file=True, country_iso_code="CAN"
    )
    tracker.start()

    code_author, security_analyst = create_dual_agents(llm_config, prompt_type)
    results, errors = [], 0

    try:
        for i, s in enumerate(samples):
            print(f"\n--- Processing sample {i+1}/{len(samples)} ---")

            try:
                # 1️ Code Author Stage
                author_submission = code_author.generate_reply(messages=[{
                    "role": "user",
                    "content": config.DUAL_AGENT_TASK_CODE_SUBMISSION.format(code=s["func"])
                }])
                if isinstance(author_submission, dict):
                    author_submission = json.dumps(author_submission, ensure_ascii=False)
                author_submission = str(author_submission).strip()

                # 2️ Security Analyst Stage
                analyst_feedback = security_analyst.generate_reply(messages=[{
                    "role": "user",
                    "content": config.DUAL_AGENT_TASK_FINAL_DECISION.format(
                        code=s["func"], author_response=author_submission
                    )
                }])
                if isinstance(analyst_feedback, dict):
                    analyst_feedback = json.dumps(analyst_feedback, ensure_ascii=False)
                analyst_feedback = str(analyst_feedback).strip()

                vuln, reasoning = extract_vulnerability_decision(analyst_feedback)

                result = dict(s)
                result.update({
                    "vuln": vuln,
                    "reasoning": reasoning,
                    "discussion": {
                        "author_submission": author_submission,
                        "analyst_feedback": analyst_feedback
                    },
                    "timestamp": datetime.now().isoformat(),
                })

                append_result(result, detailed_file, csv_file, header_fields)
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
                    "skipped": True,
                })
                append_result(result, detailed_file, csv_file, header_fields)
                results.append(result)

    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO₂")
        print(f"Errors encountered: {errors}")

    return results


# ================================================================
# MAIN ENTRY POINT
# ================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt_type", choices=["zero_shot", "few_shot"], default="zero_shot")
    args = parser.parse_args()

    prompt_type = args.prompt_type
    DESIGN = f"DA-vuln-two-{prompt_type}"

    model = llm_config["config_list"][0]["model"].replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"{DESIGN}_{model}_vuln_{timestamp}"

    print("Loading dataset...")
    samples = []
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if "func" in data and "target" in data:
                    samples.append(data)
            except json.JSONDecodeError:
                continue

    print(f"Loaded {len(samples)} samples.")
    if not samples:
        print("No valid samples found. Exiting.")
        return

    print(f"Running {DESIGN} (1 round per agent, {prompt_type.upper()} mode)...")
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
    print("Dual-agent vulnerability detection completed successfully.")


if __name__ == "__main__":
    main()
