# Agent Green

Agent Green is a research project for evaluating the energy consumption and accuracy of Large Language Model (LLM) agents in log parsing tasks. The project investigates non-agentic, single-agent, dual-agent, tool-using, and multi-agent LLM configurations, measuring their effectiveness and sustainability.

## Frameworks and Tools

- **AG2 (formerly AutoGen):** Used for building agentic LLM workflows ([AG2 GitHub](https://github.com/ag2ai/ag2)).
- **CodeCarbon:** Used for measuring energy consumption ([CodeCarbon GitHub](https://github.com/mlco2/codecarbon)).
- **Ollama:** Used for running and evaluating LLM models ([Ollama](https://ollama.com/)).

## Dataset

- **Source:** HDFS 2k log file from the [LogHub repository](https://github.com/logpai/loghub).
- **Sampling:** 200 log messages sampled using proportional stratified sampling by template category.
- **Templates:** Modified templates provided by Khan et al.

## Experiment Procedure

- Ollama server is started before and stopped after each run to ensure isolated energy measurements.
- Agent-level caching in AG2 is disabled for all experiments.
- Each experiment is run three times; average results are reported.
- Experiments cover four configurations:
  - **Non-Agentic (NA):** Direct LLM calls.
  - **Single Agent (SA):** One LM-based agent acts autonomously to complete the task.
  - **Dual Agents (DA):** Two LLM-based agents; the first agent (Actor) operates as in SA, producing an initial output, while the second agent (Critic) aims to challenge the correctness of this output.
  - **Multiple Agents (MA):** Four agents are involved in a coordinated setup, where two agents function similarly to those in DA, the third agent (Refiner) synthesizes and refines the outputs of the other two to produce the final response, the fourth agent (Orchestrator) coordinates the workflow. 

## Repository Structure

```
agent-green/
├── config/                # Configuration files and experiment settings
├── logs/                  # Raw and processed log files (e.g., HDFS_200_sampled.log)
├── src/                   # Source code and notebooks
│   ├── agent_utils.py
│   ├── config.py
│   ├── drain_utils.py
│   ├── evaluation.py
│   ├── format_output.py
│   ├── log_utils.py
│   ├── ollama_utils.py
│   ├── visualization.ipynb
│   ├── no_agents.ipynb
│   ├── single_agent.ipynb
│   ├── tool-based_agents.ipynb
│   ├── two_agents.ipynb
│   ├── multi_agents.ipynb
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore file
└── README.md              # Project documentation
```

## How to Use

1. Clone the repository.
2. Install dependencies:  
   ```
   pip install -r requirements.txt
   ```
3. Configure paths and settings in `config/` (for codecarbon) and `src/config.py` (for project folders, LLM configs, and prompts).
4. Place your log files and ground truth templates in the `logs/` folder.
5. Run the notebooks in `src/` to reproduce experiments and results.



## How to run Vuln Detection scripts

If you have multiple GPUs, specify which GPU to use (e.g. CUDA_VISIBLE_DEVICES=1).
Otherwise, just run the command directly.

No Agent Usage 

```
python src/no_agent_vuln_detection.py --prompt_type few_shot   # run with few-shot
python src/no_agent_vuln_detection.py --prompt_type zero_shot   # run with zero-shot

```
or 
```
# With specific GPU (example: GPU 1)
CUDA_VISIBLE_DEVICES=1 python script/no_agent_vuln.py

```

Single Agent Usage
```
python src/single_agent_vuln.py --prompt_type few_shot   # run with few-shot
python src/single_agent_vuln.py --prompt_type zero_shot   # run with zero-shot

```

Dual Agent Usage 
```
python src/dual_agent_vuln.py --prompt_type few_shot
python src/dual_agent_vuln.py --prompt_type zero_shot

```

Multi Agent Usage
```
python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot
python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot
```



## How to run Code Generation scripts


If you have multiple GPUs, specify which GPU to use (e.g. CUDA_VISIBLE_DEVICES=1).
Otherwise, just run the command directly.

No Agent Usage 

```
python src/no_agent_code_generation.py --prompt_type few_shot   # run with few-shot
python src/no_agent_code_generation.py --prompt_type zero_shot   # run with zero-shot

```
or 
```
# With specific GPU (example: GPU 1)
CUDA_VISIBLE_DEVICES=1 python script/no_agent_code_generation.py --prompt_type few_shot   # run with few-shot

```

Single Agent Usage
```
python src/single_agent_code_generation.py --prompt_type few_shot   # run with few-shot
python src/single_agent_code_generation.py --prompt_type zero_shot   # run with zero-shot

```

Dual Agent Usage 
```
python src/dual_agent_code_generation.py --prompt_type few_shot
python src/dual_agent_code_generation.py --prompt_type zero_shot

```

Multi Agent Usage
```
python src/multi_agent_code_generation.py --prompt_type few_shot
python src/multi_agent_code_generation.py --prompt_type zero_shot
```

## How to run Log Parsing experiments

Non-agentic Usage:
```
python src/no_agents_log_parsing.py --shot zero --input HDFS_385_sampled.log --gt HDFS_385_sampled_log_structured_corrected.csv   # run with zero-shot
python src/no_agents_log_parsing.py --shot few --input HDFS_385_sampled.log --gt HDFS_385_sampled_log_structured_corrected.csv  # run with few-shot
```

Single-agent Usage:
```
python src/single_agent_log_parsing.py --shot zero --input HDFS_385_sampled.log --gt HDFS_385_sampled_log_structured_corrected.csv   # run with zero-shot
python src/single_agent_log_parsing.py --shot few --input HDFS_385_sampled.log --gt HDFS_385_sampled_log_structured_corrected.csv  # run with few-shot
```

Dual-agent Usage:
```
python src/two_agent_log_parsing.py --shot zero --input HDFS_385_sampled.log --gt HDFS_385_sampled_log_structured_corrected.csv   # run with zero-shot
python src/two_agent_log_parsing.py --shot few --input HDFS_385_sampled.log --gt HDFS_385_sampled_log_structured_corrected.csv  # run with few-shot
```

Multi-agent Usage:
```
python src/multi_agent_log_parsing.py --shot zero --input HDFS_385_sampled.log --gt HDFS_385_sampled_log_structured_corrected.csv   # run with zero-shot
python src/multi_agent_log_parsing.py --shot few --input HDFS_385_sampled.log --gt HDFS_385_sampled_log_structured_corrected.csv  # run with few-shot
```
## How to run Log Analysis experiments

Non-agentic Usage:
```
python src/no_agents_log_analysis.py --shot zero --input HDFS_385_sampled_sessions --gt HDFS_anomaly_label_385_session_sampled.csv   # run with zero-shot
python src/no_agents_log_analysis.py --shot few --input HDFS_385_sampled_sessions --gt HDFS_anomaly_label_385_session_sampled.csv  # run with few-shot
```

Single-agent Usage:
```
python src/single_agent_log_analysis.py --shot zero --input HDFS_385_sampled_sessions --gt HDFS_anomaly_label_385_session_sampled.csv   # run with zero-shot
python src/single_agent_log_analysis.py --shot few --input HDFS_385_sampled_sessions --gt HDFS_anomaly_label_385_session_sampled.csv  # run with few-shot
```

Dual-agent Usage:
```
python src/two_agent_log_analysis.py --shot zero --input HDFS_385_sampled_sessions --gt HDFS_anomaly_label_385_session_sampled.csv   # run with zero-shot
python src/two_agent_log_analysis.py --shot few --input HDFS_385_sampled_sessions --gt HDFS_anomaly_label_385_session_sampled.csv  # run with few-shot
```

Multi-agent Usage:
```
python src/multi_agent_log_analysis.py --shot zero --input HDFS_385_sampled_sessions --gt HDFS_anomaly_label_385_session_sampled.csv   # run with zero-shot
python src/multi_agent_log_analysis.py --shot few --input HDFS_385_sampled_sessions --gt HDFS_anomaly_label_385_session_sampled.csv  # run with few-shot
```

## How to run Technical Debt Detection experiments
Non-agentic Usage:
```
python src/no_agents_td_detection.py --shot zero --input mlcq_cleaned_and_pruned_dataset_385.csv --gt mlcq_cleaned_and_pruned_dataset_385.csv   # run with zero-shot
python src/no_agents_td_detection.py --shot few --input mlcq_cleaned_and_pruned_dataset_385.csv --gt mlcq_cleaned_and_pruned_dataset_385.csv  # run with few-shot
```

Single-agent Usage:
```
python src/single_agent_td_detection.py --shot zero --input mlcq_cleaned_and_pruned_dataset_385.csv --gt mlcq_cleaned_and_pruned_dataset_385.csv   # run with zero-shot
python src/single_agent_td_detection.py --shot few --input mlcq_cleaned_and_pruned_dataset_385.csv --gt mlcq_cleaned_and_pruned_dataset_385.csv  # run with few-shot
```

Dual-agent Usage:
```
python src/two_agent_td_detection.py --shot zero --input mlcq_cleaned_and_pruned_dataset_385.csv --gt mlcq_cleaned_and_pruned_dataset_385.csv  # run with zero-shot
python src/two_agent_td_detection.py --shot few --input mlcq_cleaned_and_pruned_dataset_385.csv --gt mlcq_cleaned_and_pruned_dataset_385.csv  # run with few-shot
```

Dual-agent Usage:
```
python src/multi_agent_td_detection.py --shot zero --input mlcq_cleaned_and_pruned_dataset_385.csv --gt mlcq_cleaned_and_pruned_dataset_385.csv  # run with zero-shot
python src/multi_agent_td_detection.py --shot few --input mlcq_cleaned_and_pruned_dataset_385.csv --gt mlcq_cleaned_and_pruned_dataset_385.csv  # run with few-shot
```

Common CLI flags
- `--input` (default from `config.IN_FILE`) — filename located inside `data/`.
- `--gt` (default from `config.GT_FILE`) — ground-truth filename inside `data/` used for evaluation.
- `--result-dir` (default from `config.RESULT_DIR`) — directory where outputs and CodeCarbon files are saved.
- `--design` (default from `config.DESIGN`) — experiment design label. 
- `--shot` (choices `zero`,`few`, default `few`) — choose zero-shot or few-shot system prompts where supported. The script auto-sets a prefix based on the experiment type (see mapping below) and the chosen `--shot`.

Experiment design prefixes
- `NA-` — non-agentic (no agents; scripts that call LLM directly). Example: `NA-few` or `NA-zero`.
- `SA-`  — single-agent experiments (agent-based, single assistant). Example: `SA-few`.
- `DA-` — dual/two-agent experiments (generator + critic). Example: `DA-few`.
- `MA-` — multi-agent experiments (four agents). Example: `MA-few`.


How `--shot` affects prompts
- `--shot zero`: the script uses the corresponding ZERO_SHOT sys prompts (e.g. `SYS_MSG_TD_DETECTION_GENERATOR_ZERO_SHOT`).
- `--shot few` : the script uses the FEW_SHOT sys prompts (e.g. `SYS_MSG_TD_DETECTION_GENERATOR_FEW_SHOT`).
