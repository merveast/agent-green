import os
import json
import config
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
from vuln_evaluation import evaluate_and_save_vulnerability, normalize_vulnerability_basic
from agent_utils_vuln import create_agent
from autogen.agentchat.conversable_agent import ConversableAgent
from pathlib import Path

# --- Configuration ---
llm_config = config.LLM_CONFIG
DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

DESIGN = "MA-vuln-four"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_vuln_{timestamp}"


# --- Agent Creation ---
def create_vulnerability_agents(llm_config):
    """Create the four vulnerability detection agents"""
    user_proxy = create_agent(
        "conversable",
        "user_proxy_agent",
        llm_config,
        sys_prompt="A human admin coordinating the vulnerability assessment.",
        description="A proxy for human input coordinating the multi-agent vulnerability assessment."
    )

    security_researcher = create_agent(
        "assistant",
        "security_researcher_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_SECURITY_RESEARCHER,
        description="Identify potential security vulnerabilities in code."
    )

    code_author = create_agent(
        "assistant",
        "code_author_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_CODE_AUTHOR,
        description="Defend code against vulnerability claims or propose mitigations."
    )

    moderator = create_agent(
        "assistant",
        "moderator_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_MODERATOR,
        description="Provide neutral summaries of the vulnerability discussion."
    )

    review_board = create_agent(
        "assistant",
        "review_board_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_REVIEW_BOARD,
        description="Make final decisions on vulnerability validity and severity."
    )

    return user_proxy, security_researcher, code_author, moderator, review_board


# --- Data Loading ---
def load_vulnerability_dataset(file_path):
    """Load vulnerability dataset from JSONL file"""
    samples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if 'func' in data and 'target' in data:
                    sample = {
                        'idx': data.get('idx'),
                        'project': data.get('project'),
                        'commit_id': data.get('commit_id'),
                        'project_url': data.get('project_url'),
                        'commit_url': data.get('commit_url'),
                        'commit_message': data.get('commit_message'),
                        'func': data['func'],
                        'target': data['target'],
                        'cwe': data.get('cwe'),
                        'cve': data.get('cve'),
                        'cve_desc': data.get('cve_desc')
                    }
                    samples.append(sample)
            except json.JSONDecodeError:
                continue
    return samples


# --- Result Helpers ---
def initialize_results_files(exp_name, result_dir):
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")
    energy_file = os.path.join(result_dir, f"{exp_name}_energy_tracking.json")

    with open(csv_file, 'w') as f:
        f.write("idx,project,commit_id,project_url,commit_url,commit_message,"
                "ground_truth,vuln,reasoning,cwe,cve,cve_desc\n")

    return detailed_file, csv_file, energy_file


def append_result(result, detailed_file, csv_file):
    """Append a result to both JSONL and CSV"""
    with open(detailed_file, 'a') as f:
        f.write(json.dumps(result) + '\n')

    with open(csv_file, 'a') as f:
        def escape(field):
            if field is None:
                return ""
            field_str = str(field)
            if ',' in field_str or '"' in field_str or '\n' in field_str:
                return '"' + field_str.replace('"', '""') + '"'
            return field_str

        row = [
            escape(result['idx']),
            escape(result['project']),
            escape(result['commit_id']),
            escape(result['project_url']),
            escape(result['commit_url']),
            escape(result['commit_message']),
            escape(result['ground_truth']),
            escape(result['vuln']),
            escape(result['reasoning']),
            escape(result['cwe']),
            escape(result['cve']),
            escape(result['cve_desc'])
        ]
        f.write(','.join(row) + '\n')


def extract_vulnerability_decision(review_board_response):
    """
    Parse review board response based on VulTrial's documented logic.
    
    KEY INSIGHT from Appendix J:
    - "partially valid" = BENIGN (below vulnerability threshold)
    - Only "valid" decisions count as actual vulnerabilities
    
    Returns: (vuln_prediction, reasoning_string)
    where vuln_prediction is 0 (safe) or 1 (vulnerable)
    """
    import json
    
    try:
        # Try to parse as JSON array first
        verdicts = json.loads(review_board_response.strip())
        
        if not isinstance(verdicts, list):
            verdicts = [verdicts]
        
        # Count different decision types
        valid_count = 0
        invalid_count = 0
        partially_valid_count = 0
        
        for v in verdicts:
            decision = str(v.get('decision', '')).lower()
            if decision == 'valid':
                valid_count += 1
            elif decision == 'invalid':
                invalid_count += 1
            elif 'partial' in decision:
                partially_valid_count += 1
        

        # Simple threshold: valid must outnumber all non-valid combined
        has_vulnerability = valid_count > (invalid_count + partially_valid_count)
        
        # Build reasoning string
        reasoning = "; ".join(
            f"{v.get('vulnerability','Unknown')}: {v.get('decision','Unknown')} "
            f"(severity: {v.get('severity', 'N/A')}, action: {v.get('recommended_action', 'N/A')})"
            for v in verdicts
        )
        
        return (1 if has_vulnerability else 0), reasoning
        
    except json.JSONDecodeError as e:
        # JSON parsing failed - try text analysis as fallback
        text = review_board_response.lower()
        
        # Count explicit "valid" vs "invalid" in JSON-like strings
        valid_count = text.count('"decision": "valid"') + text.count('"decision":"valid"')
        invalid_count = text.count('"decision": "invalid"') + text.count('"decision":"invalid"')
        partial_count = text.count('"decision": "partially valid"') + text.count('"decision":"partially valid"')
        
        # Apply same logic
        if valid_count > 0 or invalid_count > 0 or partial_count > 0:
            has_vulnerability = valid_count > (invalid_count + partial_count)
            return (1 if has_vulnerability else 0), review_board_response
        
        # Complete parsing failure - log it but mark as safe (conservative)
        print(f"PARSE ERROR: {e}")
        print(f"Response: {review_board_response[:200]}")
        return 0, f"PARSE_ERROR: {str(e)[:100]}"
    
    except Exception as e:
        # Unexpected error
        print(f"UNEXPECTED ERROR: {e}")
        print(f"Response: {review_board_response[:200]}")
        return 0, f"ERROR: {type(e).__name__}"



# In multi_agent_vuln_detection_four_agents.py

def run_inference_with_emissions(samples, llm_config, exp_name, result_dir):
    detailed_file, csv_file, energy_file = initialize_results_files(exp_name, result_dir)
    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        save_to_file=True,
        country_iso_code="CAN"
    )
    
    tracker.start()
    
    user_proxy, security_researcher, code_author, moderator, review_board = create_vulnerability_agents(llm_config)
    results = []
    
    error_count = 0
    skipped_samples = []
    
    try:
        for i, sample in enumerate(samples):
            print(f"\n--- Processing sample {i+1}/{len(samples)} (idx: {sample['idx']}) ---")
            
            try:
                # Step 1: Security Researcher
                researcher = user_proxy.initiate_chat(
                    recipient=security_researcher,
                    message=config.MULTI_AGENT_TASK_SECURITY_RESEARCHER.format(code=sample['func']),
                    max_turns=1,
                    summary_method="last_msg"
                ).summary.strip()
                
                # Step 2: Code Author
                author = user_proxy.initiate_chat(
                    recipient=code_author,
                    message=config.MULTI_AGENT_TASK_CODE_AUTHOR.format(
                        researcher_findings=researcher,
                        code=sample['func']
                    ),
                    max_turns=1,
                    summary_method="last_msg"
                ).summary.strip()
                
                # Step 3: Moderator
                moderator_resp = user_proxy.initiate_chat(
                    recipient=moderator,
                    message=config.MULTI_AGENT_TASK_MODERATOR.format(
                        researcher_findings=researcher,
                        author_response=author
                    ),
                    max_turns=1,
                    summary_method="last_msg"
                ).summary.strip()
                
                # Step 4: Review Board
                board = user_proxy.initiate_chat(
                    recipient=review_board,
                    message=config.MULTI_AGENT_TASK_REVIEW_BOARD.format(
                        moderator_summary=moderator_resp,
                        code=sample['func'],
                        researcher_findings=researcher,
                        author_response=author
                    ),
                    max_turns=1,
                    summary_method="last_msg"
                ).summary.strip()
                
                # Decision
                vuln_decision, reasoning = extract_vulnerability_decision(board)
                
                result = {
                    'idx': sample['idx'],
                    'project': sample['project'],
                    'commit_id': sample['commit_id'],
                    'project_url': sample['project_url'],
                    'commit_url': sample['commit_url'],
                    'commit_message': sample['commit_message'],
                    'ground_truth': sample['target'],
                    'vuln': vuln_decision,
                    'reasoning': reasoning,
                    'full_discussion': {
                        'security_researcher': researcher,
                        'code_author': author,
                        'moderator': moderator_resp,
                        'review_board': board
                    },
                    'cwe': sample['cwe'],
                    'cve': sample['cve'],
                    'cve_desc': sample['cve_desc'],
                    'session': 1,
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"  ✅ Completed: vuln={vuln_decision}, gt={sample['target']}")
                
            except Exception as e:
                # Handle ANY error (API errors, timeouts, etc.)
                error_count += 1
                skipped_samples.append(sample['idx'])
                
                print(f"  ❌ ERROR: {type(e).__name__}: {str(e)[:100]}")
                print(f"  → Skipping sample and marking as NON-VULNERABLE (vuln=0)")
                
                # Create result with error flag
                result = {
                    'idx': sample['idx'],
                    'project': sample['project'],
                    'commit_id': sample['commit_id'],
                    'project_url': sample['project_url'],
                    'commit_url': sample['commit_url'],
                    'commit_message': sample['commit_message'],
                    'ground_truth': sample['target'],
                    'vuln': 0,  # Mark as NON-VULNERABLE on error
                    'reasoning': f"ERROR: {type(e).__name__} - Sample skipped",
                    'full_discussion': {
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    'cwe': sample['cwe'],
                    'cve': sample['cve'],
                    'cve_desc': sample['cve_desc'],
                    'session': 1,
                    'timestamp': datetime.now().isoformat(),
                    'skipped': True  # Flag as skipped
                }
            
            append_result(result, detailed_file, csv_file)
            results.append(result)
            
            if (i + 1) % 10 == 0:
                print(f"\n📊 Progress: {i+1}/{len(samples)} samples")
                print(f"   Errors/Skipped: {error_count}")
        
        print(f"\n{'='*60}")
        print(f"Processing complete!")
        print(f"Total samples: {len(samples)}")
        print(f"Successfully processed: {len(samples) - error_count}")
        print(f"Skipped (errors): {error_count}")
        if skipped_samples:
            print(f"Skipped sample IDs: {skipped_samples[:10]}{'...' if len(skipped_samples) > 10 else ''}")
        print(f"{'='*60}")
    
    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO2")
    
    return results


# --- Main Execution ---
def main():
    print("Loading dataset...")
    samples = load_vulnerability_dataset(DATASET_FILE)
    print(f"Loaded {len(samples)} samples")

    print(f"Running {DESIGN} vulnerability detection...")
    results = run_inference_with_emissions(samples, llm_config, exp_name, RESULT_DIR)

    predictions = [r['vuln'] for r in results]
    ground_truth = [r['ground_truth'] for r in results]

    try:
        eval_results = evaluate_and_save_vulnerability(
            normalize_vulnerability_basic,
            predictions,
            DATASET_FILE,
            exp_name
        )
        print("Evaluation Results:", eval_results)
    except Exception as e:
        print("Evaluation failed:", e)

    print("\n=== FINAL SUMMARY ===")
    print(f"Samples processed: {len(results)}")
    print("Multi-agent vulnerability detection completed!")


if __name__ == "__main__":
    main()
