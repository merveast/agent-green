import os
import json
import argparse
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
import config
from vuln_evaluation import evaluate_and_save_vulnerability, normalize_vulnerability_basic
from agent_utils_vuln import create_agent
from sklearn.metrics import classification_report, confusion_matrix

# --- Configuration ---
llm_config = config.LLM_CONFIG
DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)


# ========================================================================
# Helper functions
# ========================================================================
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


def extract_vulnerability_decision(response):
    """
    Parse board agent output and infer vulnerability decision robustly.
    Supports keys like 'decision': 'valid', 'accept', 'resolved', etc.
    """
    try:
        verdicts = json.loads(response.strip())
        if not isinstance(verdicts, list):
            verdicts = [verdicts]

        valid_keywords = ["valid", "accept", "resolved", "true"]
        invalid_keywords = ["invalid", "false", "no"]
        partial_keywords = ["partial", "unclear", "ambiguous"]

        valid = sum(
            1 for v in verdicts
            if any(k in str(v.get("decision", "")).lower() for k in valid_keywords)
        )
        invalid = sum(
            1 for v in verdicts
            if any(k in str(v.get("decision", "")).lower() for k in invalid_keywords)
        )
        partial = sum(
            1 for v in verdicts
            if any(k in str(v.get("decision", "")).lower() for k in partial_keywords)
        )

        vuln = 1 if valid > (invalid + partial) else 0
        reasoning = "; ".join(
            f"{v.get('vulnerability','Unknown')}: {v.get('decision','?')} "
            f"(severity: {v.get('severity','N/A')}, action: {v.get('recommended_action','N/A')})"
            for v in verdicts
        )
        return vuln, reasoning

    except Exception as e:
        return 0, f"Error parsing JSON decision: {e}"


# ========================================================================
# Agent creation
# ========================================================================
def create_vulnerability_agents(llm_config, prompt_type="zero_shot"):
    """Create the 4 agents depending on prompt_type."""
    if prompt_type == "few_shot":
        researcher_prompt = config.SYS_MSG_SECURITY_RESEARCHER_FEW_SHOT
        author_prompt = config.SYS_MSG_CODE_AUTHOR_FEW_SHOT
        moderator_prompt = config.SYS_MSG_MODERATOR_FEW_SHOT
        board_prompt = config.SYS_MSG_REVIEW_BOARD_FEW_SHOT
        print("🧩 Using FEW-SHOT prompts for all agents.")
    else:
        researcher_prompt = config.SYS_MSG_SECURITY_RESEARCHER_ZERO_SHOT
        author_prompt = config.SYS_MSG_CODE_AUTHOR_ZERO_SHOT
        moderator_prompt = config.SYS_MSG_MODERATOR_ZERO_SHOT
        board_prompt = config.SYS_MSG_REVIEW_BOARD_ZERO_SHOT
        print("🧠 Using ZERO-SHOT prompts for all agents.")

    security_researcher = create_agent(
        "assistant", "security_researcher_agent", llm_config,
        sys_prompt=researcher_prompt,
        description="Identify potential vulnerabilities in the code."
    )

    code_author = create_agent(
        "assistant", "code_author_agent", llm_config,
        sys_prompt=author_prompt,
        description="Defend or mitigate vulnerabilities reported by the researcher."
    )

    moderator = create_agent(
        "assistant", "moderator_agent", llm_config,
        sys_prompt=moderator_prompt,
        description="Provide a neutral summary of the discussion."
    )

    review_board = create_agent(
        "assistant", "review_board_agent", llm_config,
        sys_prompt=board_prompt,
        description="Make final decisions on vulnerability validity and severity."
    )

    return security_researcher, code_author, moderator, review_board


# ========================================================================
# Inference with emissions tracking
# ========================================================================
def run_inference_with_emissions(samples, llm_config, exp_name, result_dir, prompt_type):
    dataset_keys = list(samples[0].keys()) if samples else []
    header_fields = dataset_keys + ["vuln", "reasoning", "timestamp"]
    detailed_file, csv_file = initialize_results_files(exp_name, result_dir, header_fields)

    tracker = OfflineEmissionsTracker(
        project_name=exp_name, output_dir=result_dir, save_to_file=True, country_iso_code="CAN"
    )
    tracker.start()

    researcher, author, moderator, board = create_vulnerability_agents(llm_config, prompt_type)
    results, errors = [], 0

    try:
        for i, s in enumerate(samples):
            print(f"\n--- Processing sample {i+1}/{len(samples)} ---")

            try:
                # Step 1: Security Researcher analyzes code
                researcher_task = config.MULTI_AGENT_TASK_SECURITY_RESEARCHER.format(code=s["func"])
                researcher_response = researcher.generate_reply(
                    messages=[{"role": "user", "content": researcher_task}]
                ).get("content", "")
                print(f"  ✓ Researcher analysis: {len(researcher_response)} chars")

                # Step 2: Code Author responds to findings
                author_task = config.MULTI_AGENT_TASK_CODE_AUTHOR.format(
                    researcher_findings=researcher_response, code=s["func"]
                )
                author_response = author.generate_reply(
                    messages=[{"role": "user", "content": author_task}]
                ).get("content", "")
                print(f"  ✓ Author response: {len(author_response)} chars")

                # Step 3: Moderator summarizes the discussion
                moderator_task = config.MULTI_AGENT_TASK_MODERATOR.format(
                    researcher_findings=researcher_response, author_response=author_response
                )
                moderator_response = moderator.generate_reply(
                    messages=[{"role": "user", "content": moderator_task}]
                ).get("content", "")
                print(f"  ✓ Moderator summary: {len(moderator_response)} chars")

                # Step 4: Review Board makes final decision
                board_task = config.MULTI_AGENT_TASK_REVIEW_BOARD.format(
                    moderator_summary=moderator_response, code=s["func"],
                    researcher_findings=researcher_response, author_response=author_response
                )
                board_response = board.generate_reply(
                    messages=[{"role": "user", "content": board_task}]
                ).get("content", "")
                print(f"  ✓ Review Board decision: {len(board_response)} chars")

                vuln, reasoning = extract_vulnerability_decision(board_response)

                result = dict(s)
                result.update({
                    "vuln": vuln,
                    "reasoning": reasoning,
                    "discussion": {
                        "researcher": researcher_response, 
                        "author": author_response, 
                        "moderator": moderator_response, 
                        "board": board_response
                    },
                    "timestamp": datetime.now().isoformat(),
                })

                append_result(result, detailed_file, csv_file, header_fields)
                results.append(result)
                print(f"  ✅ Completed: vuln={vuln}, gt={s.get('target')}")

            except Exception as e:
                errors += 1
                print(f"  ❌ Error: {e}")
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


# ========================================================================
# Main entry point
# ========================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt_type", choices=["zero_shot", "few_shot"], default="zero_shot",
                        help="Choose between zero_shot or few_shot prompting.")
    args = parser.parse_args()

    prompt_type = args.prompt_type
    DESIGN = f"MA-vuln-four-{prompt_type}"

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
    test_samples = samples  # full dataset

    print(f"Running {DESIGN} vulnerability detection ({prompt_type.upper()} mode)...")
    results = run_inference_with_emissions(test_samples, llm_config, exp_name, RESULT_DIR, prompt_type)

    # --------------------------------------------------------------------
    # Inline Evaluation (same file output)
    # --------------------------------------------------------------------
    preds = [r.get("vuln", 0) for r in results]
    gts = [r.get("target", 0) for r in results]

    acc = sum(p == g for p, g in zip(preds, gts)) / len(results) if results else 0
    print(f"\nAccuracy: {acc:.2f} ({sum(p == g for p, g in zip(preds, gts))}/{len(results)})")

    cm = confusion_matrix(gts, preds)
    report = classification_report(gts, preds, target_names=["Not Vulnerable", "Vulnerable"])

    print("\nConfusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(report)

    # Append summary to same file
    detailed_file = os.path.join(RESULT_DIR, f"{exp_name}_detailed_results.jsonl")
    eval_summary = {
        "evaluation_summary": {
            "accuracy": round(acc, 4),
            "confusion_matrix": cm.tolist(),
            "classification_report": report
        }
    }
    with open(detailed_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(eval_summary, ensure_ascii=False) + "\n")

    print(f"✅ Evaluation results appended to {detailed_file}")

    try:
        evaluate_and_save_vulnerability(normalize_vulnerability_basic, preds, DATASET_FILE, exp_name)
    except Exception as e:
        print(f"Evaluation skipped due to: {e}")

    print("\n=== FINAL SUMMARY ===")
    print(f"Samples processed: {len(results)}")
    print("Multi-agent vulnerability detection completed successfully.")


if __name__ == "__main__":
    main()
