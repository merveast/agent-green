#!/usr/bin/env python3
"""
Run Log Parsing experiment using a single agent.

"""
import os
import time
import argparse
from datetime import datetime

import config
from codecarbon import OfflineEmissionsTracker
from log_utils import read_log_messages, normalize_template, normalize_template_v1, normalize_template_v2, save_templates
from agent_utils import create_agent
from ollama_utils import start_ollama_server, stop_ollama_server
from evaluation import evaluate_and_save_parsing


def run_inference_with_emissions_log_parsing_agent(logs, llm_config, sys_prompt_log_parser, task_prompt, exp_name, result_dir):
    parsed_templates = []
    tracker = OfflineEmissionsTracker(project_name=exp_name, output_dir=result_dir, country_iso_code="CAN", save_to_file=True)
    tracker.start()
    try:
        log_parser = create_agent(
            agent_type="assistant",
            name="log_parser_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_log_parser,
            description="Analyze the log message in order to determine the corresponding template.",
        )
        for i, log_message in enumerate(logs):
            content = task_prompt + log_message
            #print(f"Processing log {i+1}/{len(logs)}")
            res = log_parser.generate_reply(messages=[{"content": content, "role": "user"}])
            if res is not None and "content" in res:
                parsed_templates.append(res["content"].strip())
            else:
                parsed_templates.append("NONE")
                print(f"[Warning] Skipped log {i} — no response or invalid format.")
    finally:
        emissions = tracker.stop()
    print(f"Emissions: {emissions} kg CO2")
    return parsed_templates


def main():
    parser = argparse.ArgumentParser(description="Run single-agent Log Parsing experiment")
    parser.add_argument("--input", default=config.IN_FILE, help="Input file name in data dir")
    parser.add_argument("--gt", default=config.GT_FILE, help="Ground truth file name in data dir")
    parser.add_argument("--result-dir", default=config.RESULT_DIR, help="Directory to save results")
    parser.add_argument("--design", default=config.DESIGN, help="Design label (overrides config.DESIGN)")
    parser.add_argument("--shot", choices=["zero","few"], default="few", help="Use zero-shot or few-shot system prompt")
    args = parser.parse_args()

    llm_config = config.LLM_CONFIG
    DATA_DIR = config.DATA_DIR
    RESULT_DIR = args.result_dir
    os.makedirs(RESULT_DIR, exist_ok=True)

    TASK = "log-parsing"
    shot = args.shot
    # For single-agent experiments, prefix design with SA-
    if args.design and args.design.upper().startswith("SA-"):
        DESIGN = args.design.capitalize()
    else:
        DESIGN = f"SA-{shot}"

    project_name = f"{TASK}_{DESIGN}"
    model_name = llm_config["config_list"][0]["model"]
    model = llm_config["config_list"][0]["model"].replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"{project_name}_{model}_{timestamp}"

    input_file_path = os.path.join(DATA_DIR, args.input)
    ground_truth_file_path = os.path.join(DATA_DIR, args.gt)

    task_prompt = config.TASK_PROMPT_LOG_PARSING
    if shot == "zero":
        sys_prompt_generator = config.SYS_MSG_LOG_PARSER_GENERATOR_ZERO_SHOT
    else:
        sys_prompt_generator = config.SYS_MSG_LOG_PARSER_GENERATOR_FEW_SHOT

    logs = read_log_messages(input_file_path)

    proc = start_ollama_server()
    time.sleep(5)
    try:
        parsed_templates = run_inference_with_emissions_log_parsing_agent(logs, llm_config, sys_prompt_generator, task_prompt, exp_name, RESULT_DIR)
        save_templates(parsed_templates, llm_config, DESIGN, RESULT_DIR)
    finally:
        stop_ollama_server(proc)

    # Evaluate using different normalizers
    results = evaluate_and_save_parsing(normalize_template, parsed_templates, ground_truth_file_path, exp_name)
    #results_v1 = evaluate_and_save_parsing(normalize_template_v1, parsed_templates, ground_truth_file_path, exp_name)
    #results_v2 = evaluate_and_save_parsing(normalize_template_v2, parsed_templates, ground_truth_file_path, exp_name)

    #print("Evaluation results:")
    #print("normalize_template:", results)
    #print("normalize_template_v1:", results_v1)
    #print("normalize_template_v2:", results_v2)


if __name__ == "__main__":
    main()
