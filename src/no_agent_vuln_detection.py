#!/usr/bin/env python3
# ================================================================
# No-Agent Vulnerability Detection (Zero-Shot and Few-Shot)
# ================================================================

import os
import time
import json
import config
import ollama
import argparse
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
from sklearn.metrics import classification_report, confusion_matrix
from log_utils import save_templates
from ollama_utils import start_ollama_server, stop_ollama_server
from vuln_evaluation import (
    evaluate_and_save_vulnerability,
    normalize_vulnerability_basic,
    normalize_vulnerability_conservative,
    normalize_vulnerability_strict,
)

# ================================================================
# CLI ARGUMENT PARSING
# ================================================================
def parse_arguments():
    parser = argparse.ArgumentParser(description="Run no-agent vulnerability detection")
    parser.add_argument(
        "--prompt_type", choices=["zero_shot", "few_shot"], default="zero_shot",
        help="Choose between zero_shot or few_shot prompting."
    )
    return parser.parse_args()

args = parse_arguments()
prompt_type = args.prompt_type

# ================================================================
# CONFIGURATION
# ================================================================
llm_config = config.LLM_CONFIG
task = config.VULNERABILITY_TASK_PROMPT

# Select system prompt based on prompt type
if prompt_type == "few_shot":
    sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT
    print("🧩 Using FEW-SHOT prompt for vulnerability detection.")
else:
    sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT
    print("🧠 Using ZERO-SHOT prompt for vulnerability detection.")

LOG_DIR = config.LOG_DIR
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)
DATASET_FILE = config.VULN_DATASET

DESIGN = f"NA-vuln-{prompt_type}"
model = llm_config["config_list"][0]["model"]

temperature = llm_config["temperature"]
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

# ================================================================
# OLLAMA QUERY FUNCTION
# ================================================================
def query_ollama(model, prompt):
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
def load_dataset(dataset_path):
    """Load vulnerability dataset from JSONL file"""
    data = []
    print(f"\nReading dataset from: {dataset_path}")
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line.strip())
                if "func" in item and "target" in item:
                    data.append(item)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipped malformed line: {e}")
                continue
    
    print(f"Loaded {len(data)} vulnerability samples")
    return data

# ================================================================
# FILE HANDLING
# ================================================================
def initialize_results_files(exp_name, result_dir):
    """Initialize result files with headers"""
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")

    with open(csv_file, "w") as f:
        f.write("idx,project,commit_id,ground_truth,response,vuln,timestamp\n")

    return detailed_file, csv_file

# ================================================================
# RESPONSE PARSING
# ================================================================
def extract_vulnerability_decision(response_text):
    """Extract vulnerability decision from model response"""
    if not response_text:
        return 0
        
    response_lower = response_text.lower()
    
    # Check for explicit yes/no indicators
    if any(k in response_lower for k in ["yes", "vulnerability detected", "(1) yes"]):
        return 1
    elif any(k in response_lower for k in ["no", "no vulnerability", "(2) no"]):
        return 0
    
    # Check for vulnerability-related keywords
    vulnerability_indicators = [
        "vulnerability", "unsafe", "exploit", "attack", "overflow",
        "injection", "leak", "security issue", "insecure"
    ]
    
    if any(indicator in response_lower for indicator in vulnerability_indicators):
        return 1
        
    return 0

# ================================================================
# CORE EXECUTION
# ================================================================
def run_inference_with_emissions(samples, model_name, sys_prompt, task_prompt, exp_name, result_dir):
    """Run vulnerability detection with emissions tracking"""
    detailed_file, csv_file = initialize_results_files(exp_name, result_dir)

    tracker = OfflineEmissionsTracker(
        project_name=exp_name, output_dir=result_dir, country_iso_code="CAN", save_to_file=True
    )
    tracker.start()
    
    results, errors = [], 0

    try:
        for i, item in enumerate(samples):
            print(f"\n--- Processing sample {i+1}/{len(samples)} ---")

            try:
                formatted_prompt = sys_prompt + "\n\n" + task_prompt.format(code=item["func"])
                response = query_ollama(model_name, formatted_prompt)
                
                # Extract vulnerability decision
                vuln = extract_vulnerability_decision(response)

                result = {
                    "idx": item.get("idx", i),
                    "project": item.get("project", ""),
                    "commit_id": item.get("commit_id", ""),
                    "ground_truth": item.get("target", 0),
                    "response": response or "",
                    "vuln": vuln,
                    "timestamp": datetime.now().isoformat(),
                }

                # Save to JSONL
                with open(detailed_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")

                # Save to CSV
                with open(csv_file, "a", encoding="utf-8") as f:
                    safe = lambda x: str(x).replace(",", ";").replace("\n", " ")
                    row = [
                        safe(result["idx"]),
                        safe(result["project"]),
                        safe(result["commit_id"]),
                        safe(result["ground_truth"]),
                        safe(result["response"]),
                        safe(result["vuln"]),
                        safe(result["timestamp"])
                    ]
                    f.write(",".join(row) + "\n")
                
                results.append(result)
                print(f"  ✓ Completed: vuln={vuln}, gt={item.get('target', 0)}")

            except Exception as e:
                errors += 1
                print(f"  ❌ Error: {e}")
                
                result = {
                    "idx": item.get("idx", i),
                    "project": item.get("project", ""),
                    "commit_id": item.get("commit_id", ""),
                    "ground_truth": item.get("target", 0),
                    "response": f"ERROR: {str(e)}",
                    "vuln": 0,
                    "timestamp": datetime.now().isoformat(),
                    "error": True,
                }
                
                with open(detailed_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                
                results.append(result)

    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO₂")
        print(f"Errors encountered: {errors}")

    return results

# ================================================================
# EVALUATION
# ================================================================
def evaluate_results(results, result_dir, exp_name):
    """Evaluate vulnerability detection results"""
    preds = [r["vuln"] for r in results]
    gts = [r.get("ground_truth", 0) for r in results]
    
    # Calculate accuracy
    acc = sum(p == g for p, g in zip(preds, gts)) / len(results) if results else 0
    print(f"\nAccuracy: {acc:.2f} ({sum(p == g for p, g in zip(preds, gts))}/{len(results)})")
    
    # Generate confusion matrix and classification report
    cm = confusion_matrix(gts, preds)
    report = classification_report(gts, preds, target_names=["Not Vulnerable", "Vulnerable"])
    
    print("\nConfusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(report)
    
    # Save evaluation summary
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    eval_summary = {
        "evaluation_summary": {
            "accuracy": round(acc, 4),
            "confusion_matrix": cm.tolist(),
            "classification_report": report
        }
    }
    with open(detailed_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(eval_summary, ensure_ascii=False) + "\n")
    
    return acc, cm, report

# ================================================================
# MAIN EXECUTION
# ================================================================
def main():
    print(f"\nRunning {DESIGN} ({prompt_type.upper()} mode, direct model inference)...")
    print(f"Model: {model}")
    print(f"Temperature: {temperature}")
    print(f"Experiment: {exp_name}")
    
    # Load dataset
    samples = load_dataset(DATASET_FILE)
    
    if not samples:
        print("No samples found, exiting.")
        return

    # Start Ollama server
    proc = start_ollama_server()
    time.sleep(5)

    try:
        # Run inference
        results = run_inference_with_emissions(
            samples, model, sys_prompt, task, exp_name, RESULT_DIR
        )
        
        print(f"\nDetailed results saved to: {RESULT_DIR}/{exp_name}_detailed_results.jsonl")
        
        # Save templates for later analysis
        save_templates([r["response"] for r in results], llm_config, DESIGN, RESULT_DIR)
        print(f"Templates saved for experiment: {exp_name}")
        
        # Evaluate results
        acc, cm, report = evaluate_results(results, RESULT_DIR, exp_name)
        
        # Run additional evaluations
        print("\n" + "=" * 60)
        print("RUNNING ADDITIONAL EVALUATIONS")
        print("=" * 60)
        
        predictions = [r["vuln"] for r in results]
        
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

    finally:
        # Clean up Ollama server
        stop_ollama_server(proc)
        print("\nOllama server stopped.")
    
    print("\n" + "=" * 60)
    print("ALL EVALUATIONS COMPLETED")
    print("=" * 60)
    print(f"Results directory: {RESULT_DIR}")
    print(f"Experiment name: {exp_name}")
    print(f"Accuracy: {acc:.4f}")

if __name__ == "__main__":
    main()
