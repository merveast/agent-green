#!/usr/bin/env python3
# ================================================================
# No-Agent Code Generation (Zero-Shot and Few-Shot)
# ================================================================

#!/usr/bin/env python3
import os
import json
import time
import config
import sys
import subprocess
import argparse
import ollama
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
from ollama_utils import start_ollama_server, stop_ollama_server

# --- Parse Command Line Arguments ---
def parse_arguments():
    parser = argparse.ArgumentParser(description="No-Agent Code Generation")
    parser.add_argument(
        "--prompt_type",
        type=str,
        choices=["zero_shot", "few_shot"],
        default="zero_shot",
        help="Prompt type: zero_shot or few_shot (default: zero_shot)"
    )
    return parser.parse_args()

args = parse_arguments()

# --- Configuration ---
llm_config = config.LLM_CONFIG
DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

DESIGN = f"NA-code-{'few' if args.prompt_type == 'few_shot' else 'zero'}"

model = llm_config["config_list"][0]["model"]
temperature = llm_config.get("temperature", 0.0)
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

# --- Direct Ollama Query ---
def query_ollama(model, prompt):
    """Query Ollama model directly without agent framework"""
    try:
        response = ollama.generate(
            model=model, 
            prompt=prompt, 
            options={"temperature": temperature}
        )
        return response.get("response", None)
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return None

# --- Data Reading ---
def read_code_generation_data(dataset_path):
    code_problems = []
    with open(dataset_path, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            code_problems.append(data)
    return code_problems

print(f"Reading dataset from: {DATASET_FILE}")
code_samples = read_code_generation_data(DATASET_FILE)
print(f"Loaded {len(code_samples)} code samples")

# --- Helper Functions ---
def extract_code_from_response(response_text):
    """Extract Python code from model response"""
    if not response_text:
        return ""
    
    response_text = response_text.strip()
    
    # Check for code blocks
    if "```python" in response_text:
        parts = response_text.split("```python")
        if len(parts) > 1:
            code_part = parts[1].split("```")[0]
            return code_part.strip()
    elif "```" in response_text:
        parts = response_text.split("```")
        if len(parts) >= 3:
            code_part = parts[1]
            return code_part.strip()
    
    # Find function definition
    lines = response_text.split('\n')
    code_lines = []
    found_def = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith(('To solve', 'The ', 'This ', 'Here', 'Note:', '**')):
            if not found_def:
                continue
            else:
                break
        
        if stripped.startswith(('def ', 'from ', 'import ')):
            found_def = True
        
        if found_def:
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return response_text.strip()

# --- Inference with Emissions Tracking ---
def run_inference_with_emissions(code_samples, model_name, sys_prompt, task, exp_name, result_dir):
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    
    tracker = OfflineEmissionsTracker(
        project_name=exp_name, 
        output_dir=result_dir, 
        country_iso_code="CAN",
        save_to_file=True
    )
    tracker.start()
    
    try:
        for i, sample in enumerate(code_samples):
            print(f"Processing sample {i+1}/{len(code_samples)} (task_id: {sample.get('task_id', i)})")
            
            problem_prompt = sample.get('prompt', sample.get('description', ''))
            content = task.format(prompt=problem_prompt)
            
            # Direct Ollama call without agent
            formatted_prompt = sys_prompt + "\n\n" + content
            response_text = query_ollama(model_name, formatted_prompt)
            
            result = {
                'task_id': sample.get('task_id', ''),
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', '')
            }
            
            if response_text:
                generated_code = extract_code_from_response(response_text)
                result['generated_solution'] = generated_code
            else:
                result['generated_solution'] = ""
                print(f"[Warning] Skipped sample {i} — no response or invalid format.")
            
            with open(detailed_file, 'a') as f:
                f.write(json.dumps(result) + '\n')
            
            if (i + 1) % 10 == 0:
                print(f"Progress saved: {i + 1}/{len(code_samples)} samples completed")
                
    finally:
        emissions = tracker.stop()
        print(f"Emissions: {emissions} kg CO2")
    
    return detailed_file

# --- Main Execution ---
def main():
    time.sleep(1)
    
    if args.prompt_type == "few_shot":
        sys_prompt = config.SYS_MSG_CODE_GENERATOR_FEW_SHOT
        print("Using few-shot system prompt")
    else:
        sys_prompt = config.SYS_MSG_CODE_GENERATOR_ZERO_SHOT
        print("Using zero-shot system prompt")
    
    print(f"\nRunning {DESIGN} code generation (direct model inference)...")
    print(f"Model: {model}")
    print(f"Temperature: {temperature}")
    print(f"Experiment: {exp_name}")
    
    print("Starting Ollama server...")
    proc = start_ollama_server()
    time.sleep(5)
    
    try:
        detailed_file = run_inference_with_emissions(
            code_samples, 
            model, 
            sys_prompt, 
            config.SINGLE_AGENT_TASK_CODE_GENERATION, 
            exp_name, 
            RESULT_DIR
        )
    except Exception as e:
        print(f"Error during inference: {e}")
        detailed_file = None
    finally:
        print("Stopping Ollama server...")
        stop_ollama_server(proc)
    
    if detailed_file:
        print(f"\nCode generation completed for experiment: {exp_name}")
        print(f"Total samples processed: {len(code_samples)}")
        print(f"Results saved to: {detailed_file}")
        
        # --- Call Evaluation Script ---
        print("\n" + "="*80)
        print("STARTING EVALUATION")
        print("="*80)
        
        try:
            eval_result = subprocess.run(
                ["python", "src/evaluate_code_generation.py", detailed_file],
                capture_output=True,
                text=True
            )
            
            print(eval_result.stdout)
            
            if eval_result.returncode != 0:
                print("Evaluation encountered an error:")
                print(eval_result.stderr)
            else:
                print("\n" + "="*80)
                print("EVALUATION COMPLETED SUCCESSFULLY")
                print("="*80)
                
        except Exception as e:
            print(f"Failed to run evaluation: {e}")
            print("You can manually evaluate by running:")
            print(f"python src/evaluate_code_generation.py {detailed_file}")
    else:
        print("\nCode generation failed - no results to evaluate")

if __name__ == "__main__":
    main()
