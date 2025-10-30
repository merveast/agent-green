import os
import json
import time
import config
import re
import argparse
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
import requests
import subprocess


# --- Parse Command Line Arguments ---
def parse_arguments():
    parser = argparse.ArgumentParser(description="No-Agent Code Generation")
    
    # Add prompt_type argument
    parser.add_argument(
        "--prompt_type",
        type=str,
        choices=["zero_shot", "few_shot"],
        default="zero_shot",
        help="Prompt type: zero_shot or few_shot (default: zero_shot)"
    )
    
    return parser.parse_args()

# Parse arguments
args = parse_arguments()

# --- Configuration ---
llm_config = config.LLM_CONFIG
DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

# Map prompt_type to design name
DESIGN = f"NA-{'few' if args.prompt_type == 'few_shot' else 'zero'}"

model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

print(f"Experiment: {exp_name}")
print(f"Dataset: {DATASET_FILE}")
print(f"Results will be saved to: {RESULT_DIR}")


# --- Data Reading ---
def read_code_generation_data(dataset_path):
    """Read code generation data from JSONL file"""
    code_problems = []
    print(f"\nReading dataset from: {dataset_path}")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                code_problems.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipped malformed line: {e}")
                continue
    
    print(f"Loaded {len(code_problems)} code samples")
    return code_problems


# --- Helper Functions ---
def generate_code_direct_api(prompt, model_name, api_base, system_prompt):
    """Call API directly without agents - pure API call"""
    url = f"{api_base}/v1/chat/completions"
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling API: {e}")
        return ""


def extract_code_from_response(response_text):
    """Extract Python code from model response"""
    if not response_text:
        return ""
    
    # Remove <think> blocks if present
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
    response_text = response_text.strip()
    
    # Method 1: ```python blocks
    if "```python" in response_text:
        parts = response_text.split("```python")
        if len(parts) > 1:
            code = parts[1].split("```")[0]
            return code.strip()
    
    # Method 2: ``` blocks
    if "```" in response_text:
        parts = response_text.split("```")
        if len(parts) >= 3:
            code = parts[1]
            lines = code.split('\n')
            if lines[0].strip() in ['python', 'py', 'json']:
                code = '\n'.join(lines[1:])
            return code.strip()
    
    # Method 3: Extract from 'def' or 'from' or 'import' to end
    lines = response_text.split('\n')
    code_lines = []
    found_start = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip explanatory text
        if not found_start and stripped.startswith(('To solve', 'The ', 'This ', 'Here', 'Note:', '**', '[', 'I ', 'First', 'Challenge', 'Wait,', 'Let', 'So ', 'Yes,', 'Okay')):
            continue
        
        # Start collecting from imports or code
        if stripped.startswith(('def ', 'from ', 'import ', 'class ')):
            found_start = True
        
        if found_start:
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return response_text.strip()


# --- No-Agent Inference with Emissions Tracking ---
def run_direct_inference_with_emissions(code_samples, llm_config, task, sys_prompt, exp_name, result_dir):
    """Direct inference with emissions tracking - no agent framework used"""
    
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    summary_file = os.path.join(result_dir, f"{exp_name}_summary.json")
    
    if os.path.exists(detailed_file):
        os.remove(detailed_file)
    
    model_name = llm_config["config_list"][0]["model"]
    api_base = llm_config["config_list"][0]["api_base"]
    
    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        country_iso_code="CAN",
        save_to_file=True
    )
    tracker.start()
    
    stats = {
        'total_samples': len(code_samples),
        'successful_extractions': 0,
        'failed_extractions': 0
    }
    
    try:
        for i, sample in enumerate(code_samples):
            task_id = sample.get('task_id', f'sample_{i}')
            print(f"\n{'='*60}")
            print(f"Processing {i+1}/{len(code_samples)}: {task_id}")
            print(f"{'='*60}")
            
            # Get problem prompt
            problem_prompt = sample.get('prompt', '')
            
            # Format task with prompt
            content = task.format(prompt=problem_prompt)
            
            # Direct API call - no agent framework or additional processing
            print("Calling API directly (no agent framework)...")
            response_text = generate_code_direct_api(
                content, 
                model_name, 
                api_base,
                sys_prompt
            )
            
            # Extract code from response
            final_code = extract_code_from_response(response_text)
            print(f"  Generated code: {len(final_code)} chars")
            
            # Check extraction quality
            if final_code and 'def' in final_code:
                stats['successful_extractions'] += 1
            else:
                stats['failed_extractions'] += 1
                print("  ✗ WARNING: No valid function definition found!")
            
            # Create result
            result = {
                'task_id': task_id,
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', ''),
                'generated_solution': final_code,
                'raw_response': response_text,
                'metadata': {
                    'approach': 'direct_api',
                    'prompt_type': args.prompt_type,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # Save immediately after each sample (append mode)
            with open(detailed_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result) + '\n')
            
            # Progress checkpoint
            if (i + 1) % 10 == 0:
                print(f"\n✓ Progress checkpoint: {i + 1}/{len(code_samples)} samples completed")
                print(f"  Success rate: {stats['successful_extractions']}/{i+1} ({stats['successful_extractions']/(i+1)*100:.1f}%)")
    
    finally:
        emissions = tracker.stop()
        stats['emissions_kg_co2'] = emissions
        
        print(f"\n{'='*60}")
        print("NO-AGENT CODE GENERATION COMPLETED")
        print(f"{'='*60}")
        print(f"Total samples: {stats['total_samples']}")
        print(f"Successful extractions: {stats['successful_extractions']} ({stats['successful_extractions']/stats['total_samples']*100:.1f}%)")
        print(f"Failed extractions: {stats['failed_extractions']}")
        print(f"Emissions: {emissions:.6f} kg CO2")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
    
    return detailed_file


# --- Main Execution ---
def main():
    print("\n" + "="*60)
    print(f"DIRECT API CODE GENERATION (NO AGENT FRAMEWORK) - {args.prompt_type.upper()}")
    print("="*60)
    
    # Load dataset
    code_samples = read_code_generation_data(DATASET_FILE)
    
    # Select system prompt based on prompt type
    if args.prompt_type == "few_shot":
        sys_prompt = config.SYS_MSG_CODE_GENERATOR_FEW_SHOT
        print("Using few-shot system prompt")
    else:  # zero_shot
        sys_prompt = config.SYS_MSG_CODE_GENERATOR_ZERO_SHOT
        print("Using zero-shot system prompt")
    
    # Run direct API inference without any agent framework
    print(f"\nRunning {DESIGN} code generation via direct API calls...")
    detailed_file = run_direct_inference_with_emissions(
        code_samples,
        llm_config,
        config.SINGLE_AGENT_TASK_CODE_GENERATION,
        sys_prompt,
        exp_name,
        RESULT_DIR
    )
    
    print(f"\nResults saved to: {detailed_file}")
    
    # Run evaluation
    print("\n" + "="*60)
    print("STARTING EVALUATION")
    print("="*60)
    
    try:
        eval_result = subprocess.run(
            ["python", "src/evaluate_code_generation.py", detailed_file],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        print(eval_result.stdout)
        
        if eval_result.returncode != 0:
            print("Evaluation encountered an error:")
            print(eval_result.stderr)
        else:
            print("\n" + "="*60)
            print("EVALUATION COMPLETED SUCCESSFULLY")
            print("="*60)
    
    except subprocess.TimeoutExpired:
        print("Evaluation timed out after 10 minutes")
    except Exception as e:
        print(f"Failed to run evaluation: {e}")
        print(f"You can manually evaluate by running:")
        print(f"python src/evaluate_code_generation.py {detailed_file}")


if __name__ == "__main__":
    main()
