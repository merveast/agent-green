#!/usr/bin/env python3
"""
Run multi-agent log parsing experiment.
This script runs a user proxy, a generator (parser) agent, a critic agent, and a refiner agent 
to produce, validate, and refine log templates. It uses CodeCarbon's OfflineEmissionsTracker to
record emissions for the experiment.
"""
import os
import time
import argparse
from datetime import datetime
import config
from log_utils import read_log_messages, normalize_template, save_templates
from ollama_utils import start_ollama_server, stop_ollama_server
from agent_utils import create_agent
from codecarbon import OfflineEmissionsTracker
from evaluation import evaluate_and_save_parsing


# --- Inference with Multi Agents and Emissions Tracking ---
def run_multi_agent_inference_with_emissions_log_parsing(logs, llm_config, sys_prompt_log_parser, sys_prompt_critic, sys_prompt_refiner, task_prompt, exp_name, result_dir):
    gen_log_templates = []
    critic_log_templates = []
    refiner_log_templates = []
    tracker = OfflineEmissionsTracker(project_name=exp_name, output_dir=result_dir, country_iso_code="CAN", save_to_file=True)
    tracker.start()
    try:
        user_proxy = create_agent(
            agent_type="conversable",
            name="user_proxy_agent",
            llm_config=llm_config,
            sys_prompt="A human admin.",
            description="A proxy for human input."
        )

        log_parser = create_agent(
            agent_type="assistant",
            name="log_parser_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_log_parser,
            description="Analyze the log message in order to determine the corresponding template."
        )

        critic = create_agent(
            agent_type="assistant",
            name="log_parser_critic_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_critic,
            #description="Analyze the log message in order to determine the corresponding template."
        )
        refiner = create_agent(
            agent_type="assistant",
            name="log_parser_refiner_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_refiner,
            #description="Analyze the log message in order to determine the corresponding template."
        )

        for i, log_message in enumerate(logs):
            #print(f"\n--- Processing log message {i+1}/{len(logs)} ---")
            parser_response = user_proxy.initiate_chat(
                recipient=log_parser,
                message=task_prompt + log_message,
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            if parser_response is not None:
                gen_log_template = normalize_template(parser_response)
                #print(f"[Info] Log parser agent processed log message {i+1}: {gen_log_template}")
                gen_log_templates.append(gen_log_template)
            else:
                gen_log_templates.append("NONE")
                print(f"[Warning] Skipped log message {i+1} — no response or invalid format.")

            content_critic = f"""
                Check if the provided template correctly represents the message body of the original log message, excluding the header. 
                All variable values in the message body should be replaced with the <*> placeholder.
                If the provided template is correct, return it exactly as is. 
                If it is incorrect, return the corrected template only (no explanations or extra text).

                ORIGINAL_LOG_MESSAGE: {log_message}
                PROVIDED_TEMPLATE: {gen_log_template}
                """
            
            res_critic = critic.generate_reply(messages=[{"content": content_critic, "role": "user"}])
            if res_critic is not None and "content" in res_critic:
                critic_log_template = normalize_template(res_critic["content"].strip())
                #print(f"[Info] Critic agent processed log message {i+1}: {critic_log_template}")
                critic_log_templates.append(critic_log_template)
            else:
                critic_log_templates.append("NONE")
                print(f"[Warning] Critic skipped log message {i+1} — no response or invalid format.")

            content_refiner = f"""
                Refine the log template to ensure it correctly represents the message body of the original log message, excluding the header. 
                All variable values in the message body should be replaced with the <*> placeholder. 
                If both provided templates are incorrect, create a new correct one from the log. 
                If unsure, prefer the CRITIC_TEMPLATE. 
                Return only the final refined template (no explanations or extra text).

                ORIGINAL_LOG_MESSAGE: {log_message}
                PARSER_TEMPLATE: {gen_log_template}
                CRITIC_TEMPLATE: {critic_log_template}
                """
            res_refiner = refiner.generate_reply(messages=[{"content": content_refiner, "role": "user"}])
            if res_refiner is not None and "content" in res_refiner:
                refiner_log_template = normalize_template(res_refiner["content"].strip())
                #print(f"[Info] Refiner agent processed log message {i+1}: {refiner_log_template}")
                refiner_log_templates.append(refiner_log_template)
            else:
                refiner_log_templates.append("NONE")
                print(f"[Warning] Refiner skipped log message {i+1} — no response or invalid format.")

    finally:
        emissions = tracker.stop()
    print(f"Emissions: {emissions} kg CO2")
    return refiner_log_templates


def main():
    parser = argparse.ArgumentParser(description="Multi-agent log parsing runner")
    parser.add_argument("--input", default=config.IN_FILE, help="Input log file name (in config.DATA_DIR)")
    parser.add_argument("--gt", default=config.GT_FILE, help="Ground-truth file name (in config.DATA_DIR)")
    parser.add_argument("--result-dir", default=config.RESULT_DIR, help="Directory to store results")
    parser.add_argument("--design", default=None, help="Experiment design name (prefixes allowed: NA-, SA-, DA-, MA-). If omitted, DA-{shot} will be used.")
    parser.add_argument("--shot", default="few", choices=["zero", "few"], help="zero or few shot prompt selection")
    args = parser.parse_args()

    TASK = "log-parsing"  
    shot = args.shot.lower()
    if shot not in ("zero", "few"):
        raise SystemExit("--shot must be 'zero' or 'few'")

    # Select prompts based on shot
    if shot == "zero":
        sys_prompt_generator = config.SYS_MSG_LOG_PARSER_GENERATOR_ZERO_SHOT
        sys_prompt_critic = config.SYS_MSG_LOG_PARSER_CRITIC_ZERO_SHOT
        sys_prompt_refiner = config.SYS_MSG_LOG_PARSER_REFINER_ZERO_SHOT
    else:
        sys_prompt_generator = config.SYS_MSG_LOG_PARSER_GENERATOR_FEW_SHOT
        sys_prompt_critic = config.SYS_MSG_LOG_PARSER_CRITIC_FEW_SHOT
        sys_prompt_refiner = config.SYS_MSG_LOG_PARSER_REFINER_FEW_SHOT

    llm_config = config.LLM_CONFIG
    DATA_DIR = config.DATA_DIR
    RESULT_DIR = args.result_dir
    os.makedirs(RESULT_DIR, exist_ok=True)

    # Determine DESIGN with MA- prefix by default 
    design = args.design
    if design is None:
        DESIGN = f"MA-{shot}"
    else:
        if any(design.startswith(p) for p in ("NA-", "SA-", "DA-", "MA-")):
            DESIGN = design
        else:
            DESIGN = design

    project_name = f"{TASK}_{DESIGN}"
    model = llm_config["config_list"][0]["model"].replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"{project_name}_{model}_{timestamp}"

    input_file_path = os.path.join(DATA_DIR, args.input)
    ground_truth_file_path = os.path.join(DATA_DIR, args.gt)

    # Read inputs
    logs = read_log_messages(input_file_path)

    proc = start_ollama_server()
    time.sleep(5)
    try:
        last_templates = run_multi_agent_inference_with_emissions_log_parsing(logs, llm_config, sys_prompt_generator, sys_prompt_critic, sys_prompt_refiner, config.TASK_PROMPT_LOG_PARSING, exp_name, RESULT_DIR)
        save_templates(last_templates, llm_config, DESIGN, RESULT_DIR)
    finally:
        stop_ollama_server(proc)
    # Evaluate 
    results = evaluate_and_save_parsing(normalize_template, last_templates, ground_truth_file_path, exp_name)
    #print("Evaluation results:", results)

if __name__ == "__main__":
    main()
