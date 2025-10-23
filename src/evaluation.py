import csv
import Levenshtein
from difflib import SequenceMatcher
import pandas as pd
import config
import os
from debt_utils import map_ground_truth_label

def load_ground_truth(file_path):
    ground_truth = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ground_truth[int(row["LineId"])] = row["EventTemplate"]
    return ground_truth

def calculate_edit_distance(str1, str2):
    return Levenshtein.distance(str1, str2)

def calculate_lcs(str1, str2):
    matcher = SequenceMatcher(None, str1, str2)
    return sum(block.size for block in matcher.get_matching_blocks())

def load_ground_truth_list(file_path):
    templates = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            templates.append(row["EventTemplate"])
    return templates

def evaluate_parsing(parsed_templates, ground_truth_templates):
    total_logs = len(ground_truth_templates)
    correct_parses = 0
    total_edit_distance = 0
    total_lcs_length = 0
    total_edit_sim = 0
    total_lcs_sim = 0

    TP = FP = TN = FN = 0  

    line_metrics = []

    for idx, (parsed_template, ground_truth_template) in enumerate(zip(parsed_templates, ground_truth_templates), start=1):
        # --- Compute raw metrics ---
        edit_distance = calculate_edit_distance(parsed_template, ground_truth_template)
        lcs_length = calculate_lcs(parsed_template, ground_truth_template)

        # --- Compute normalized metrics ---
        max_len = max(len(parsed_template), len(ground_truth_template))
        gt_len = len(ground_truth_template)
        edit_sim = 1 - (edit_distance / max_len) if max_len > 0 else 0
        lcs_sim = (lcs_length / gt_len) if gt_len > 0 else 0

        total_edit_sim += edit_sim
        total_lcs_sim += lcs_sim

        # --- Correctness ---
        is_correct = parsed_template == ground_truth_template
        if is_correct:
            correct_parses += 1
            TP += 1
        else:
            FP += 1

        print(f"Log Line {idx}:")
        print(f"  Parsed:    {parsed_template}")
        print(f"  Ground:    {ground_truth_template}")
        print(f"  Edit Dist: {edit_distance}")
        print(f"  LCS:       {lcs_length}")
        print("-" * 50)

        line_metrics.append({
            "Line Number": idx,
            "Parsed": parsed_template,
            "Ground Truth": ground_truth_template,
            "Edit Distance": edit_distance,
            "Edit Similarity": round(edit_sim, 4),
            "LCS Length": lcs_length,
            "LCS Similarity": round(lcs_sim, 4),
            "Is Correct": is_correct
        })

    
     # --- Averages ---
    avg_edit_distance = total_edit_distance / total_logs
    avg_lcs_length = total_lcs_length / total_logs
    avg_edit_sim = total_edit_sim / total_logs
    avg_lcs_sim = total_lcs_sim / total_logs
    parsing_accuracy = correct_parses / total_logs

    print("\n=== Log Parsing Evaluation Summary ===")
    print(f"Parsing Accuracy:        {parsing_accuracy:.2%}")
    print(f"Average Edit Similarity: {avg_edit_sim:.4f}")
    print(f"Average LCS Similarity:  {avg_lcs_sim:.4f}")
    print(f"TP: {TP}, FP: {FP}, TN: {TN}, FN: {FN}")
    print("======================================")

    return {
        "Parsing Accuracy": parsing_accuracy,
        "Average Edit Similarity": avg_edit_sim,
        "Average LCS Similarity": avg_lcs_sim,
        "Average Edit Distance": avg_edit_distance,
        "Average LCS Length": avg_lcs_length,
        "TP": TP,
        "FP": FP,
        "TN": TN,
        "FN": FN,
        "Per-Line Metrics": line_metrics
    }


def save_per_line_metrics(results, design, results_dir=config.RESULT_DIR):
    filename = os.path.join(results_dir, f"{design}_per_line_metrics.csv")
    df_metrics = pd.DataFrame(results["Per-Line Metrics"])
    df_metrics.to_csv(filename, index=False)
    print(f"Per-line metrics saved to: {filename}")

def save_summary_metrics(results, design, results_dir=config.RESULT_DIR):
    filename = os.path.join(results_dir, f"{design}_summary_metrics.csv")
    summary_df = pd.DataFrame([{
        "Parsing Accuracy": results["Parsing Accuracy"],
        "Average Edit Similarity": results["Average Edit Similarity"],
        "Average LCS Similarity": results["Average LCS Similarity"],
        "Average Edit Distance": results["Average Edit Distance"],
        "Average LCS Length": results["Average LCS Length"]
    }])
    summary_df.to_csv(filename, index=False)
    print(f"Summary metrics saved to: {filename}")

# --- Evaluate all for log parsing---
def evaluate_and_save_parsing(normalize_fn, parsed_templates, ground_truth_file_path, exp_name):
    normalized_templates = [normalize_fn(t) for t in parsed_templates]
    ground_truth_templates = load_ground_truth_list(ground_truth_file_path)
    results = evaluate_parsing(normalized_templates, ground_truth_templates)
    save_per_line_metrics(results, exp_name)
    save_summary_metrics(results, exp_name)
    return results


def evaluate_td_per_line(ground_truth, normalized_preds):
    """Compute per-line metrics for technical debt detection."""
    per_line = []
    TP = FP = TN = FN = 0
    total_correct = 0

    for idx, (gt_entry, pred) in enumerate(zip(ground_truth, normalized_preds), start=1):
        true_label = map_ground_truth_label(gt_entry)
        pred_positive = pred != "0"
        true_positive = true_label != "0"

        if pred_positive and true_positive:
            TP += 1
        elif pred_positive and not true_positive:
            FP += 1
        elif not pred_positive and not true_positive:
            TN += 1
        elif not pred_positive and true_positive:
            FN += 1

        if pred == true_label:
            total_correct += 1

        per_line.append({
            "Line Number": idx,
            "Code Snippet": gt_entry["code_snippet"],
            "Ground Truth Label": true_label,
            "Predicted Label": pred,
            "Is Correct": pred == true_label
        })

    accuracy = total_correct / len(ground_truth)

    return {
        "Per-Line Metrics": per_line,
        "Accuracy": accuracy,
        "TP": TP,
        "FP": FP,
        "TN": TN,
        "FN": FN
    }


def save_td_per_line_metrics(results, exp_name, results_dir=config.RESULT_DIR):
    os.makedirs(results_dir, exist_ok=True)
    filename = os.path.join(results_dir, f"{exp_name}_per_line_metrics.csv")
    df = pd.DataFrame(results["Per-Line Metrics"])
    df.to_csv(filename, index=False)
    print(f"TD per-line metrics saved to: {filename}")


def save_td_summary_metrics(results, exp_name, results_dir=config.RESULT_DIR):
    os.makedirs(results_dir, exist_ok=True)
    summary_file = os.path.join(results_dir, f"{exp_name}_summary_metrics.csv")
    summary_df = pd.DataFrame([{
        "Accuracy": results["Accuracy"],
        "TP": results["TP"],
        "FP": results["FP"],
        "TN": results["TN"],
        "FN": results["FN"]
    }])
    summary_df.to_csv(summary_file, index=False)
    print(f"TD summary metrics saved to: {summary_file}")


def evaluate_and_save_td(normalize_fn, ground_truth, raw_preds, exp_name, results_dir=config.RESULT_DIR):
    """
    Wrapper function to normalize TD predictions, compute metrics, and save CSV files.

    Args:
        normalize_fn: Function to normalize raw predictions (e.g., convert "No smell"/"Blob" to "0"-"4")
        ground_truth: List of ground truth entries (from get_td_ground_truth)
        raw_preds: List of raw predictions generated by agents
        exp_name: Experiment/design name for file naming
        results_dir: Directory to save results
    """
    # Apply normalization to raw predictions
    normalized_preds = [normalize_fn(p) for p in raw_preds]

    # Compute per-line metrics and summary
    results = evaluate_td_per_line(ground_truth, normalized_preds)
    save_td_per_line_metrics(results, exp_name, results_dir)
    save_td_summary_metrics(results, exp_name, results_dir)

    # --- summary printout ---
    print("\n=== Technical Debt Detection Evaluation Summary ===")
    print(f"Accuracy: {results['Accuracy']:.2%}")
    print(f"TP: {results['TP']} | FP: {results['FP']} | TN: {results['TN']} | FN: {results['FN']}")
    print("====================================================\n")

    # Return only the summary info (not per-line details)
    return {
        "Accuracy": results["Accuracy"],
        "TP": results["TP"],
        "FP": results["FP"],
        "TN": results["TN"],
        "FN": results["FN"]
    }
