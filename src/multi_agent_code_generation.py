import os
import json
import time
import config
import argparse
import re
from datetime import datetime
from autogen import AssistantAgent
from codecarbon import OfflineEmissionsTracker
from ollama_utils import start_ollama_server,stop_ollama_server
import sys
import subprocess


# --- Parse command line arguments ---
def parse_arguments():
    parser = argparse.ArgumentParser(description='Run multi-agent code generation')
    parser.add_argument('--prompt_type', type=str, choices=['zero_shot', 'few_shot'], 
                    default='zero_shot', help='Type of prompt to use')
    return parser.parse_args()

args = parse_arguments()

# --- Configuration ---
llm_config = config.LLM_CONFIG
DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

# Design configuration
DESIGN = f"MA-code-{args.prompt_type}"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

print(f"Experiment: {exp_name}")
print(f"Dataset: {DATASET_FILE}")
print(f"Prompt Type: {args.prompt_type}")
print(f"Results will be saved to: {RESULT_DIR}")


# --- Agent Creation ---
def create_requirements_analyst(llm_config, sys_prompt):
    return AssistantAgent(
        name="requirements_analyst",
        system_message=sys_prompt,
        description="Analyze requirements and identify challenges.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

def create_programmer_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="programmer",
        system_message=sys_prompt,
        description="Implement code solutions.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

def create_moderator_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="moderator",
        system_message=sys_prompt,
        description="Review code and provide feedback.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

def create_review_board_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="review_board",
        system_message=sys_prompt,
        description="Make final assessment and improvements.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )


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


# --- Multi-Agent Inference with Emissions Tracking ---
def run_inference_with_emissions(code_samples, llm_config, sys_prompts, exp_name, result_dir, prompt_type):
    """Run multi-agent code generation with emissions tracking - always use all 4 agents"""
    
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    summary_file = os.path.join(result_dir, f"{exp_name}_summary.json")
    
    if os.path.exists(detailed_file):
        os.remove(detailed_file)
    
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
        'failed_extractions': 0,
        'used_programmer_code': 0,
        'used_review_board_code': 0,
        'prompt_type': prompt_type
    }
    
    try:
        # Create agents with appropriate system messages
        analyst = create_requirements_analyst(llm_config, sys_prompts["analyst"])
        programmer = create_programmer_agent(llm_config, sys_prompts["programmer"])
        moderator = create_moderator_agent(llm_config, sys_prompts["moderator"])
        review_board = create_review_board_agent(llm_config, sys_prompts["review_board"])
        
        for i, sample in enumerate(code_samples):
            task_id = sample.get('task_id', f'sample_{i}')
            print(f"\n{'='*60}")
            print(f"Processing {i+1}/{len(code_samples)}: {task_id}")
            print(f"{'='*60}")
            
            problem_prompt = sample.get('prompt', '')
            
            # === TURN 1: Requirements Analyst ===
            print("Turn 1: Requirements Analyst analyzing...")
            # Select appropriate task prompt based on prompt_type
            if args.prompt_type == 'zero_shot':
                analyst_task = config.MULTI_AGENT_TASK_REQUIREMENTS_ANALYST_ZERO_SHOT.format(prompt=problem_prompt)
            else:  # few_shot
                analyst_task = config.MULTI_AGENT_TASK_ANALYST.format(prompt=problem_prompt)
                
            res1 = analyst.generate_reply(messages=[{"content": analyst_task, "role": "user"}])
            analyst_findings = res1.get("content", "") if res1 else ""
            print(f"  Analyst findings: {len(analyst_findings)} chars")
            
            # === TURN 2: Programmer Implementation ===
            print("Turn 2: Programmer implementing code...")
            if args.prompt_type == 'zero_shot':
                programmer_task = config.MULTI_AGENT_TASK_PROGRAMMER_ZERO_SHOT.format(
                    analyst_findings=analyst_findings,
                    prompt=problem_prompt
                )
            else:  # few_shot
                programmer_task = config.MULTI_AGENT_TASK_PROGRAMMER.format(
                    analyst_findings=analyst_findings,
                    prompt=problem_prompt
                )
                
            res2 = programmer.generate_reply(messages=[{"content": programmer_task, "role": "user"}])
            programmer_response = res2.get("content", "") if res2 else ""
            programmer_code = extract_code_from_response(programmer_response)
            print(f"  Programmer code: {len(programmer_code)} chars")
            
            # === TURN 3: Moderator Review ===
            print("Turn 3: Moderator reviewing code...")
            moderator_task = config.MULTI_AGENT_TASK_MODERATOR_CODE.format(
                prompt=problem_prompt,
                programmer_response=programmer_code
            )
            
            res3 = moderator.generate_reply(messages=[{"content": moderator_task, "role": "user"}])
            moderator_review = res3.get("content", "") if res3 else ""
            print(f"  Moderator review: {len(moderator_review)} chars")
            
            # === TURN 4: Review Board Assessment ===
            print("Turn 4: Review Board making final assessment...")
            review_board_task = config.MULTI_AGENT_TASK_REVIEW_BOARD_CODE.format(
                prompt=problem_prompt,
                programmer_response=programmer_code,
                moderator_summary=moderator_review
            )
            
            res4 = review_board.generate_reply(messages=[{"content": review_board_task, "role": "user"}])
            review_board_assessment = res4.get("content", "") if res4 else ""
            review_board_code = extract_code_from_response(review_board_assessment)
            print(f"  Review Board assessment: {len(review_board_assessment)} chars")
            
            # === Determine final code to use ===
            if review_board_code and 'def' in review_board_code:
                final_code = review_board_code
                stats['used_review_board_code'] += 1
                print(f"  ✓ Using Review Board's code ({len(final_code)} chars)")
            else:
                final_code = programmer_code
                stats['used_programmer_code'] += 1
                print(f"  ✓ Using Programmer's code ({len(final_code)} chars) - Review Board didn't provide valid code")
            
            # === Check extraction quality ===
            if final_code and 'def' in final_code:
                stats['successful_extractions'] += 1
            else:
                stats['failed_extractions'] += 1
                print("  ✗ WARNING: No valid function definition found!")
            
            # === Save result ===
            result = {
                'task_id': task_id,
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', ''),
                'generated_solution': final_code,
                'conversation': {
                    'analyst_findings': analyst_findings,
                    'programmer_code': programmer_code,
                    'moderator_review': moderator_review,
                    'review_board_assessment': review_board_assessment,
                    'review_board_code': review_board_code
                },
                'metadata': {
                    'used_code_source': 'review_board' if final_code == review_board_code else 'programmer',
                    'prompt_type': prompt_type,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            with open(detailed_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result) + '\n')
            
            # Progress checkpoint
            if (i + 1) % 10 == 0:
                print(f"\n✓ Progress checkpoint: {i + 1}/{len(code_samples)} samples completed")
                print(f"  Success rate: {stats['successful_extractions']}/{i+1} ({stats['successful_extractions']/(i+1)*100:.1f}%)")
                print(f"  Using Review Board code: {stats['used_review_board_code']}")
                print(f"  Using Programmer code: {stats['used_programmer_code']}")
    
    finally:
        emissions = tracker.stop()
        stats['emissions_kg_co2'] = emissions
        
        print(f"\n{'='*60}")
        print("MULTI-AGENT CODE GENERATION COMPLETED")
        print(f"{'='*60}")
        print(f"Total samples: {stats['total_samples']}")
        print(f"Successful extractions: {stats['successful_extractions']} ({stats['successful_extractions']/stats['total_samples']*100:.1f}%)")
        print(f"Failed extractions: {stats['failed_extractions']}")
        print(f"Used programmer code: {stats['used_programmer_code']} ({stats['used_programmer_code']/stats['total_samples']*100:.1f}%)")
        print(f"Used review board code: {stats['used_review_board_code']} ({stats['used_review_board_code']/stats['total_samples']*100:.1f}%)")
        print(f"Prompt type: {stats['prompt_type']}")
        print(f"Emissions: {emissions:.6f} kg CO2")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
    
    return detailed_file


# --- Main Execution ---
def main():
    print("\n" + "="*60)
    print(f"MULTI-AGENT CODE GENERATION - {args.prompt_type.upper()}")
    print("="*60)

    print("Starting Ollama server...")
    proc = start_ollama_server()
    time.sleep(5)  # give it a few seconds to start up

    try:
        # Load dataset
        code_samples = read_code_generation_data(DATASET_FILE)
        
        # Select appropriate system prompts based on prompt_type
        sys_prompts = {}
        if args.prompt_type == 'zero_shot':
            sys_prompts["analyst"] = config.SYS_MSG_REQUIREMENTS_ANALYST_ZERO_SHOT
            sys_prompts["programmer"] = config.SYS_MSG_PROGRAMMER_MA_ZERO_SHOT
            sys_prompts["moderator"] = config.SYS_MSG_MODERATOR_CODE_ZERO_SHOT
            sys_prompts["review_board"] = config.SYS_MSG_REVIEW_BOARD_CODE_ZERO_SHOT
        else:  # few_shot
            sys_prompts["analyst"] = config.SYS_MSG_REQUIREMENTS_ANALYST
            sys_prompts["programmer"] = config.SYS_MSG_PROGRAMMER_MA
            sys_prompts["moderator"] = config.SYS_MSG_MODERATOR_CODE
            sys_prompts["review_board"] = config.SYS_MSG_REVIEW_BOARD_CODE
        
        # Run inference
        print(f"\nRunning {DESIGN} multi-agent code generation...")
        detailed_file = run_inference_with_emissions(
            code_samples,
            llm_config,
            sys_prompts,
            exp_name,
            RESULT_DIR,
            args.prompt_type
        )
        
        print(f"\nResults saved to: {detailed_file}")
    except Exception as e:
        print(f"Error during code generation: {e}")

    finally:
        print("Stopping Ollama server...")
        stop_ollama_server(proc)
    
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
