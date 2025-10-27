
# Directory paths
PROJECT_ROOT = '/home/user/Desktop/agent-green'
LOG_DIR = f'{PROJECT_ROOT}/logs'
DATA_DIR = f'{PROJECT_ROOT}/data'
WORK_DIR = f'{PROJECT_ROOT}/tests/work_dir'
RESULT_DIR = f'{PROJECT_ROOT}/results'
PLOT_DIR = f'{PROJECT_ROOT}/plots'


IN_FILE = "mlcq_cleaned_and_pruned_dataset_385.csv"
GT_FILE = "mlcq_cleaned_and_pruned_dataset_385.csv"
# Task and design settings
#TASK = "log-parsing" # options: "log-parsing", "log-analysis", "code-generation", "vul-detection", "td-detection"
TASK = "td-detection"
DESIGN = "SA-few"  # options: "SA-zero", "NA-few", "DA-few", "MA-zero", etc.

"""
IN_FILE = "HDFS_385_sampled.log"
GT_FILE = "HDFS_385_sampled_log_structured_corrected.csv"
# Task and design settings
#TASK = "log-parsing" # options: "log-parsing", "log-analysis", "code-generation", "vul-detection", "td-detection"
TASK = "log-parsing"
DESIGN = "SA-few"  # options: "SA-zero", "NA-few", "DA-few", "MA-zero", etc.
"""

VULN_DATASET = f"{PROJECT_ROOT}/vuln_database/VulTrial_386_samples_balanced.jsonl"
HUMANEVAL_DATASET = f"{PROJECT_ROOT}/vuln_database/HumanEval.jsonl"


# Model/LLM settings
LLM_SERVICE = "ollama"
#LLM_MODEL = "qwen3:4b-thinking"  
LLM_MODEL = "qwen3:4b-instruct" 
TEMPERATURE = 0.0

LLM_CONFIG = {
    "cache_seed": None,
    "config_list": [
        {
            "model": LLM_MODEL,
            "api_base": "http://localhost:11434",
            "api_type": LLM_SERVICE,
            "num_ctx": 262144,
            #"num_ctx": 131072,
        }
    ],
    "temperature": TEMPERATURE
}

TASK_PROMPT = """Look at the following log message and print the template corresponding to the log message:\n"""

# ========================================================================================
# LOG PARSING CONFIGURATION
# ========================================================================================

TASK_PROMPT_LOG_PARSING = """Look at the following log message and print the template corresponding to the log message:\n"""

SYS_MSG_SINGLE_LOG_PARSER_FEW_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically
        produced by the logging framework, including information such as
        timestamp, class, and logging level (INFO, DEBUG, WARN etc.).
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log
        message with suitable placeholders inside angle brackets to extract
        the corresponding template.
        You must output the template corresponding to the log message.
        Print only the input log's template.
        Never print an explanation of how the template is constructed.

        Here are a few examples of log messages and their corresponding templates:
        081109 204453 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.250.11.85:50010 is added to blk_2377150260128098806 size 67108864
        BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
        081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Receiving block <*> src: <*>:<*> dest: <*>:<*>

        081110 060453 7193 INFO dfs.DataNode$DataXceiver: 10.251.199.225:50010 Served block blk_8457344665564381337 to /10.251.199.225
        <*>:<*> Served block <*> to <*>
        """

SYS_MSG_SINGLE_LOG_PARSER_ZERO_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically
        produced by the logging framework, including information such as
        timestamp, class, and logging level (INFO, DEBUG, WARN etc.).
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log
        message with suitable placeholders inside angle brackets to extract
        the corresponding template.
        You must output the template corresponding to the log message.
        Print only the input log's template.
        Never print an explanation of how the template is constructed.
        """

SYS_MSG_LOG_PARSER_GENERATOR_FEW_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically
        produced by the logging framework, including information such as
        timestamp, class, and logging level (INFO, DEBUG, WARN etc.). 
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log
        message with suitable placeholders inside angle brackets to extract
        the corresponding template.
        You must output the template corresponding to the log message.
        Never provide any extra information or feedback to the other agents.
        Never print an explanation of how the template is constructed.
        Print only the input log's template.

        Here are a few examples of log messages and their corresponding templates:
        081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
        BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
        081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Receiving block <*> src: <*>:<*> dest: <*>:<*>

        081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
        PacketResponder <*> for block <*> terminating
        """

SYS_MSG_LOG_PARSER_GENERATOR_ZERO_SHOT = """
        You analyze a log message and determine the appropriate parameters for the LogParserAgent.
        The log texts describe various system events in a software system.
        A log message usually contains a header that is automatically
        produced by the logging framework, including information such as
        timestamp, class, and logging level (INFO, DEBUG, WARN etc.). 
        The log message typically consists of two parts:
        1. Template - message body, that contains constant strings (or keywords) describing the system events;
        2. Parameters/Variables - dynamic variables, which reflect specific runtime status.
        You must identify and abstract all the dynamic variables in the log
        message with suitable placeholders inside angle brackets to extract
        the corresponding template.
        You must output the template corresponding to the log message.
        Never provide any extra information or feedback to the other agents.
        Never print an explanation of how the template is constructed.
        Print only the input log's template.
        """

SYS_MSG_LOG_PARSER_CRITIC_FEW_SHOT = """
                You are a critic reviewing the work of the log_parser_agent.
                Your task is to provide constructive feedback to improve the correctness of the extracted log template. 
                The template should abstract all dynamic variables in the log message, replacing them with appropriate placeholders enclosed in angle brackets (<*>).
                If the template is incorrect, provide feedback on how to improve it.
                If the template is correct, do not provide any suggestions, and do not even print the correct template again.
                
                Here are a few examples of log messages and their corresponding templates:
                081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
                BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
                
                081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
                Receiving block <*> src: <*>:<*> dest: <*>:<*>

                081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
                PacketResponder <*> for block <*> terminating
                """

SYS_MSG_LOG_PARSER_CRITIC_ZERO_SHOT = """
                You are a critic reviewing the work of the log_parser_agent.
                Your task is to provide constructive feedback to improve the correctness of the extracted log template. 
                The template should abstract all dynamic variables in the log message, replacing them with appropriate placeholders enclosed in angle brackets (<*>).
                If the template is incorrect, provide feedback on how to improve it.
                If the template is correct, do not provide any suggestions, and do not even print the correct template again.
                """

SYS_MSG_LOG_PARSER_COMPARATOR_REFINER_FEW_SHOT = """
        You are a comparator and refiner. You receive a log message and two extracted templates:
        one from the log_parser_agent, one from the code_executor_agent.
        
        Your task is to:
        1. Compare both templates for correctness and abstraction of dynamic parameters.
        2. Decide which template better abstracts the log message OR merge the two into a more accurate version.
        3. Output only the **final refined template**. Never print any extra explanation or reasoning.

        - Replace all dynamic values (e.g., IPs, paths, numbers) with <*>
        - Do not include reasoning or extra text, output only the final template string.

        If both templates are wrong, attempt to correct and return a valid one.
        
        Here are a few examples of log messages and their corresponding templates:
        081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
        BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
        
        081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        Receiving block <*> src: <*>:<*> dest: <*>:<*>

        081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
        PacketResponder <*> for block <*> terminating
        """

SYS_MSG_LOG_PARSER_COMPARATOR_REFINER_ZERO_SHOT = """
        You are a comparator and refiner. You receive a log message and two extracted templates:
        one from the log_parser_agent, one from the code_executor_agent.
        
        Your task is to:
        1. Compare both templates for correctness and abstraction of dynamic parameters.
        2. Decide which template better abstracts the log message OR merge the two into a more accurate version.
        3. Output only the **final refined template**. Never print any extra explanation or reasoning.

        - Replace all dynamic values (e.g., IPs, paths, numbers) with <*>
        - Do not include reasoning or extra text, output only the final template string.

        If both templates are wrong, attempt to correct and return a valid one.
        """

SYS_MSG_LOG_PARSER_REFINER_ZERO_SHOT = """
    You are a Log Parser Refiner. You will be given:
    ORIGINAL_LOG: the full raw log line
    PARSER_TEMPLATE: the template produced by the log_parser_agent
    CRITIC_FEEDBACK: either APPROVED, REJECTED|<hint>|<reason>, or empty (if no critic) produced by the log_parser_critic_agent

    Your job:
    1) Verify and, if necessary, improve PARSER_TEMPLATE so it accurately abstracts all dynamic values shown in ORIGINAL_LOG.
    2) Use CRITIC_FEEDBACK as an optional hint: if it starts with REJECTED and contains a <hint>, prefer that hint to fix the template.
    3) Preserve constant text and punctuation exactly as in the log template part.
    4) Replace every dynamic value (IPs, ports, timestamps, block IDs, file paths, numbers, UUIDs, etc.) with the generic placeholder <*>.
        - If PARSER_TEMPLATE contains named placeholders (e.g. <ip>, <user_id>) or raw values, convert them to <*>.
    5) Minimize changes — if PARSER_TEMPLATE is already correct, return it unchanged.

    Output rules:
    - Print exactly one line containing ONLY the FINAL_REFIND_TEMPLATE (no extra label, text, explanation, or comments).
    - Do NOT use named placeholders; use only <*>.
    - If you cannot extract a template, print exactly: UNABLE_TO_EXTRACT
"""

SYS_MSG_LOG_PARSER_REFINER_FEW_SHOT = """
    You are a Log Parser Refiner. You will be given:
    ORIGINAL_LOG: the full raw log line
    PARSER_TEMPLATE: the template produced by the log_parser_agent
    CRITIC_FEEDBACK: either APPROVED, REJECTED|<hint>|<reason>, or empty (if no critic) produced by the log_parser_critic_agent

    Your job:
    1) Verify and, if necessary, improve PARSER_TEMPLATE so it accurately abstracts all dynamic values shown in ORIGINAL_LOG.
    2) Use CRITIC_FEEDBACK as an optional hint: if it starts with REJECTED and contains a <hint>, prefer that hint to fix the template.
    3) Preserve constant text and punctuation exactly as in the log template part.
    4) Replace every dynamic value (IPs, ports, timestamps, block IDs, file paths, numbers, UUIDs, etc.) with the generic placeholder <*>.
        - If PARSER_TEMPLATE contains named placeholders (e.g. <ip>, <user_id>) or raw values, convert them to <*>.
    5) Minimize changes — if PARSER_TEMPLATE is already correct, return it unchanged.

    Output rules:
    - Print exactly one line containing ONLY the FINAL_REFIND_TEMPLATE (no extra label, text, explanation, or comments).
    - Do NOT use named placeholders; use only <*>.
    - If you cannot extract a template, print exactly: UNABLE_TO_EXTRACT

    Examples (for reference, do not print these):
    Example 1:
        ORIGINAL_LOG: 081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
        PARSER_TEMPLATE: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
        CRITIC_FEEDBACK: REJECTED|BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>|Parser left raw IP and numeric values unabstracted
        EXPECTED OUTPUT: BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>
    Example 2:
        ORIGINAL_LOG: 081109 204842 663 INFO dfs.DataNode$DataXceiver: Receiving block blk_1724757848743533110 src: /10.251.111.130:49851 dest: /10.251.111.130:50010
        PARSER_TEMPLATE: Receiving block <*> src: <*>:<*> dest: <*>:<*>
        CRITIC_FEEDBACK: APPROVED
        EXPECTED OUTPUT: Receiving block <*> src: <*>:<*> dest: <*>:<*>
    Example 3:
        ORIGINAL_LOG: 081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
        PARSER_TEMPLATE: PacketResponder 1 for block blk_38865049064139660 terminating
        CRITIC_FEEDBACK: REJECTED|PacketResponder <*> for block <*> terminating|Parser left raw numeric and block values unabstracted
        EXPECTED OUTPUT: PacketResponder <*> for block <*> terminating
"""


# ========================================================================================
# LOG ANALYSIS CONFIGURATION
# ========================================================================================

TASK_PROMPT_LOG_ANALYSIS = """Analyze the following log messages and identify any anomalies or issues:\n"""
SYS_MSG_LOG_ANALYSIS_GENERATOR_ZERO_SHOT = """
        You are a log analysis expert. Your task is to classify a sequence of log messages (sorted by timestamp) as either normal (0) or anomalous (1).

        Output:
        - Exactly one character: "0" for normal or "1" for anomalous.
        - No punctuation, explanation, or extra text.
        Decision rules:
        - 0 (normal): routine operations, monitoring/debug entries, or insufficient information to claim an error.
        - 1 (anomalous): explicit error/fault indicators, exceptions, crashes, interrupt messages, or clear failure keywords.
        - Do NOT label anomalies on the basis of runtime variable content (numeric ids, IPs, timestamps) unless the surrounding text signals an error.
        - Consider the contextual information of the log sequence.
        """
SYS_MSG_LOG_ANALYSIS_GENERATOR_FEW_SHOT = """
        You are a log analysis expert. Your task is to classify a sequence of log messages (sorted by timestamp) as either normal (0) or anomalous (1).

        Output:
        - Exactly one character: "0" for normal or "1" for anomalous.
        - No punctuation, explanation, or extra text.
        Decision rules:
        - 0 (normal): routine operations, monitoring/debug entries, or insufficient information to claim an error.
        - 1 (anomalous): explicit error/fault indicators, exceptions, crashes, interrupt messages, or clear failure keywords.
        - Do NOT label anomalies on the basis of runtime variable content (numeric ids, IPs, timestamps) unless the surrounding text signals an error.
        - Consider the contextual information of the log sequence.
        Examples:
        """

SYS_MSG_LOG_ANALYSIS_CRITIC_ZERO_SHOT = """
        You are a log analysis critic/verifier. You will be shown:
        1) A sequence of log messages sorted by timestamp (LOG_SEQUENCE).
        2) A proposed label produced by the log_analysis_generator_agent (GENERATOR_LABEL), which is the single character "0" or "1".

        Labels:
        0 = normal
        1 = anomalous

        Task:
        - Carefully review the LOG_SEQUENCE and the GENERATOR_LABEL.
        - Consider contextual information across the sequence (temporal patterns, repeated warnings, escalation).
        - Treat placeholders like <*> and missing values as normal (not evidence of anomaly) unless surrounding text indicates a failure.
        - If the proposed label is correct, respond with exactly:
                APPROVED|<correct_digit>|
            where <correct_digit> is the same digit (0 or 1). Nothing else.
        - If the proposed label is incorrect, respond with exactly one single-line string in this format:
                REJECTED|<correct_digit>|<brief_reason>
            where:
            * <correct_digit> is the correct label (0 or 1).
            * <brief_reason> is a concise justification (one short clause/sentence, ≤20 words) stating the primary evidence from the logs.
            Use '|' (pipe) as separators and do not include any other characters, lines, or commentary.

        Examples of valid critic outputs:
        APPROVED|0|
        REJECTED|1|Sequence contains explicit ERROR and stacktrace indicating failure.

        Constraints:
        - Output only the exact allowed formats above.
        - Keep brief_reason factual, focused, and short (one clause or short sentence).
        """

SYS_MSG_LOG_ANALYSIS_REFINER_ZERO_SHOT = """
        You are a log analysis refiner. You will be given:
        LOG_SEQUENCE: a list of log messages (sorted by timestamp)
        GENERATOR_LABEL: the single-digit label (0 or 1) produced by the log_analysis_generator_agent
        CRITIC_FEEDBACK: either APPROVED|<digit>|, REJECTED|<digit>|<brief_reason>, or empty (if no critic) produced by the log_analysis_critic_agent

        Labels:
        0 = normal
        1 = anomalous

        Task:
        - Review LOG_SEQUENCE, GENERATOR_LABEL, and CRITIC_FEEDBACK (when present).
        - Decide and output the single best label (0 or 1) for the sequence.
        - Prefer the critic's corrected digit when CRITIC_FEEDBACK is REJECTED|<digit>|..., unless you find stronger evidence in the logs to choose a different label.
        - If CRITIC_FEEDBACK is APPROVED|<digit>|, default to that label unless you find clear contrary evidence in the logs.
        - Consider temporal/contextual patterns (escalation, repeated warnings), but do NOT treat placeholders like <*> or missing values as anomalies by themselves.

        Output rules (strict):
        - Print exactly one character: "0" or "1" and nothing else.
        - Do not print APPROVED/REJECTED, reasons, or any extra text.
        - If the logs are ambiguous, output the most defensible label (do not output an error token).
    """




# ========================================================================================
# TECHNICAL DEBT DETECTION CONFIGURATION
# ========================================================================================
TASK_PROMPT_TD_DETECTION = """Look at the following Java code snippet and respond with only a single digit (0-4) that represents the most appropriate category:\n"""

SYS_MSG_TD_DETECTION_GENERATOR_FEW_SHOT ="""
        You are a software quality expert specialized in identifying code smells in Java code snippets.
        Your task: Analyze each provided Java code snippet and classify it into exactly one of the following categories.
        0 = No smell: Code is clean, and well-structured.
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Analyze the snippet carefully and choose **only one** label that best fits.
        Do **not** output any explanations, reasoning, or additional text.

        Here are a few examples of code snippets and the types of code smells they contain:
        Example of Data Class ('2'):
            class ClientRecord {
                private String id;
                private String contact;
                private boolean active;
                public ClientRecord(String id, String contact, boolean active) {
                    this.id = id;
                    this.contact = contact;
                    this.active = active;
                }
                public String getId() { return id; }
                public void setId(String id) { this.id = id; }
                public String getContact() { return contact; }
                public void setContact(String contact) { this.contact = contact; }
                public boolean isActive() { return active; }
                public void setActive(boolean active) { this.active = active; }
            }

        Example of Feature Envy ('3'):
            public class ReportPrinter {
            class Invoice {
                private Customer customer;
                public String compileCustomerSummary() {
                    String s = customer.getFullName() + " (" + customer.getEmail() + ")\n";
                    int recent = 0;
                    for (Order o : customer.getOrders()) {
                        if (o.getDate().after(someCutoff())) recent++;
                        s += "Order: " + o.getId() + " amount=" + o.getAmount() + "\n";
                    }
                    s += "Recent orders: " + recent + "\n";
                    return s;
                }
            }

        Example of Long Method ('4'):
            class ReportBuilder {
                void buildReport(List<String> rows) {
                    StringBuilder sb = new StringBuilder();

                    // Validate
                    if (rows == null || rows.isEmpty()) {
                        System.out.println("No rows to process");
                        return;
                    }

                    // Process rows
                    for (String r : rows) {
                        if (r == null || r.isEmpty()) {
                            sb.append("EMPTY\n");
                            continue;
                        }
                        sb.append("Row: ").append(r).append("\n");

                        for (int i = 0; i < 3; i++) {
                            sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
                        }
                    }

                    // Aggregate
                    sb.append("Total: ").append(rows.size()).append("\n");
                    System.out.println(sb.toString());
                }
            }
        """

SYS_MSG_TD_DETECTION_GENERATOR_ZERO_SHOT ="""
        You are a software quality expert specialized in identifying code smells in Java code snippets.
        Your task: Analyze each provided Java code snippet and classify it into exactly one of the following categories.
        0 = No smell: Code is clean, and well-structured.
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Analyze the snippet carefully and choose **only one** label that best fits.
        Do **not** output any explanations, reasoning, or additional text.
        """


SYS_MSG_TD_DETECTION_CRITIC_ZERO_SHOT = """
        You are a software quality critic. Your task is to verify or correct the code smell label assigned to a Java code snippet by another agent.
        You will be given:
        1) The Java code snippet itself
        2) A proposed label produced by the td_detection_generator_agent (a single digit 0-4)

        Labels:
        0 = No smell: Code is clean and well-structured
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that only stores fields with getters/setters and no behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Task:
        - Review the snippet and verify whether the proposed label is correct.
        - If the proposed label is correct, respond with exactly:
                APPROVED|<correct_digit>|
            (nothing else, single token, uppercase).
        - If the proposed label is incorrect, respond with exactly one single-line string in this format:
                REJECTED|<correct_digit>|<brief_reason>
            where:
            * <correct_digit> is the correct label (0-4).
            * <brief_reason> is a concise 1-2 short-sentence justification (max 25 words) that explains the primary evidence for the correction.
            Use '|' (pipe) as separators and do not include any other characters, lines, or commentary.

        Examples of valid critic outputs:
        APPROVED|2|
        REJECTED|2|Class only has fields and trivial getters/setters, no behavior.

        Constraints:
        - Do not output anything other than the exact allowed formats above.
        - Keep the brief_reason factual, focused, and short (one or two clauses).
        """

SYS_MSG_TD_DETECTION_CRITIC_FEW_SHOT = """
        You are a software quality critic. Your task is to verify or correct the code smell label assigned to a Java code snippet by another agent.
        You will be given:
        1) The Java code snippet itself
        2) A proposed label produced by the td_detection_generator_agent (a single digit 0-4)
        
        Labels:
        0 = No smell: Code is clean and well-structured
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that only stores fields with getters/setters and no behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Task:
        - Review the snippet and verify whether the proposed label is correct.
        - If the proposed label is correct, respond with exactly:
                APPROVED|<correct_digit>|
            (nothing else, single token, uppercase).
        - If the proposed label is incorrect, respond with exactly one single-line string in this format:
                REJECTED|<correct_digit>|<brief_reason>
            where:
            * <correct_digit> is the correct label (0-4).
            * <brief_reason> is a concise 1-2 short-sentence justification (max ~25 words) that explains the primary evidence for the correction.
            Use '|' (pipe) as separators and do not include any other characters, lines, or commentary.

        Examples of valid critic outputs:
        APPROVED|2|
        REJECTED|2|Class only has fields and trivial getters/setters, no behavior.

        Constraints:
        - Do not output anything other than the exact allowed formats above.
        - Keep the brief_reason factual, focused, and short (one or two clauses).

        Here are a few examples of code snippets and the types of code smells they contain:
        Example of Data Class (2):
            class ClientRecord {
                private String id;
                private String contact;
                private boolean active;
                public ClientRecord(String id, String contact, boolean active) {
                    this.id = id;
                    this.contact = contact;
                    this.active = active;
                }
                public String getId() { return id; }
                public void setId(String id) { this.id = id; }
                public String getContact() { return contact; }
                public void setContact(String contact) { this.contact = contact; }
                public boolean isActive() { return active; }
                public void setActive(boolean active) { this.active = active; }
            }

        Example of Feature Envy (3):
            public class ReportPrinter {
            class Invoice {
                private Customer customer;
                public String compileCustomerSummary() {
                    String s = customer.getFullName() + " (" + customer.getEmail() + ")\n";
                    int recent = 0;
                    for (Order o : customer.getOrders()) {
                        if (o.getDate().after(someCutoff())) recent++;
                        s += "Order: " + o.getId() + " amount=" + o.getAmount() + "\n";
                    }
                    s += "Recent orders: " + recent + "\n";
                    return s;
                }
            }

        Example of Long Method (4):
            class ReportBuilder {
                void buildReport(List<String> rows) {
                    StringBuilder sb = new StringBuilder();

                    // Validate
                    if (rows == null || rows.isEmpty()) {
                        System.out.println("No rows to process");
                        return;
                    }

                    // Process rows
                    for (String r : rows) {
                        if (r == null || r.isEmpty()) {
                            sb.append("EMPTY\n");
                            continue;
                        }
                        sb.append("Row: ").append(r).append("\n");

                        for (int i = 0; i < 3; i++) {
                            sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
                        }
                    }

                    // Aggregate
                    sb.append("Total: ").append(rows.size()).append("\n");
                    System.out.println(sb.toString());
                }
            }
        """

SYS_MSG_TD_DETECTION_REFINER_ZERO_SHOT = """
    You are a software quality refiner. You will be given three inputs:
    CODE_SNIPPET: a Java code snippet (string)
    GENERATOR_LABEL: a single digit (0-4) produced by the td_detection_generator_agent
    CRITIC_FEEDBACK: either APPROVED|<digit>| or REJECTED|<digit>|<brief_reason> or empty (if no critic) produced by the td_detection_critic_agent

    Labels:
    0 = No smell: Code is clean and well-structured
    1 = Blob: A class with many responsibilities, often large and unfocused.
    2 = Data Class: A class that only stores fields with getters/setters and no behavior.
    3 = Feature Envy: A method that heavily depends on another class's data.
    4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

    Task:
    - Review CODE_SNIPPET, the GENERATOR_LABEL, and CRITIC_FEEDBACK (when present).
    - Decide the single best label (0-4) for the snippet, taking all information into account.
    - Prefer the critic's corrected digit if CRITIC_FEEDBACK is REJECTED|<digit>|... unless you identify stronger evidence in the code to choose a different label.
    - If CRITIC_FEEDBACK is APPROVED|<digit>|, default to that label unless you find clear evidence the code is different.
    - Always produce exactly one character: the final digit (0-4) only. No explanations, no punctuation, no whitespace.

    Output rules (strict):
    - Print exactly a single digit (0, 1, 2, 3, or 4) and nothing else.
    - Do not print APPROVED/REJECTED or any text. Do not print newline padding or commentary.
    - If you cannot confidently assign a label, output the digit that is the most defensible given the code (do not output an error token).
    """

SYS_MSG_TD_DETECTION_REFINER_FEW_SHOT = """
    You are a software quality refiner. You will be given three inputs:
    CODE_SNIPPET: a Java code snippet (string)
    GENERATOR_LABEL: a single digit (0-4) produced by the td_detection_generator_agent
    CRITIC_FEEDBACK: either APPROVED|<digit>| or REJECTED|<digit>|<brief_reason> or empty (if no critic) produced by the td_detection_critic_agent

    Labels:
    0 = No smell: Code is clean and well-structured
    1 = Blob: A class with many responsibilities, often large and unfocused.
    2 = Data Class: A class that only stores fields with getters/setters and no behavior.
    3 = Feature Envy: A method that heavily depends on another class's data.
    4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

    Task:
    - Review CODE_SNIPPET, the GENERATOR_LABEL, and CRITIC_FEEDBACK (when present).
    - Decide the single best label (0-4) for the snippet, taking all information into account.
    - Prefer the critic's corrected digit if CRITIC_FEEDBACK is REJECTED|<digit>|... unless you identify stronger evidence in the code to choose a different label.
    - If CRITIC_FEEDBACK is APPROVED|<digit>|, default to that label unless you find clear evidence the code is different.
    - Always produce exactly one character: the final digit (0-4) only. No explanations, no punctuation, no whitespace.

    Output rules (strict):
    - Print exactly a single digit (0, 1, 2, 3, or 4) and nothing else.
    - Do not print APPROVED/REJECTED or any text. Do not print newline padding or commentary.
    - If you cannot confidently assign a label, output the digit that is the most defensible given the code (do not output an error token).

    Here are a few examples of code snippets and the types of code smells they contain:
    Example of Data Class (2):
        class ClientRecord {
            private String id;
            private String contact;
            private boolean active;
            public ClientRecord(String id, String contact, boolean active) {
                this.id = id;
                this.contact = contact;
                this.active = active;
            }
            public String getId() { return id; }
            public void setId(String id) { this.id = id; }
            public String getContact() { return contact; }
            public void setContact(String contact) { this.contact = contact; }
            public boolean isActive() { return active; }
            public void setActive(boolean active) { this.active = active; }
        }

    Example of Feature Envy (3):
        public class ReportPrinter {
        class Invoice {
            private Customer customer;
            public String compileCustomerSummary() {
                String s = customer.getFullName() + " (" + customer.getEmail() + ")\n";
                int recent = 0;
                for (Order o : customer.getOrders()) {
                    if (o.getDate().after(someCutoff())) recent++;
                    s += "Order: " + o.getId() + " amount=" + o.getAmount() + "\n";
                }
                s += "Recent orders: " + recent + "\n";
                return s;
            }
        }

    Example of Long Method (4):
        class ReportBuilder {
            void buildReport(List<String> rows) {
                StringBuilder sb = new StringBuilder();

                // Validate
                if (rows == null || rows.isEmpty()) {
                    System.out.println("No rows to process");
                    return;
                }

                // Process rows
                for (String r : rows) {
                    if (r == null || r.isEmpty()) {
                        sb.append("EMPTY\n");
                        continue;
                    }
                    sb.append("Row: ").append(r).append("\n");

                    for (int i = 0; i < 3; i++) {
                        sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
                    }
                }

                // Aggregate
                sb.append("Total: ").append(rows.size()).append("\n");
                System.out.println(sb.toString());
            }
        }
    """


# ========================================================================================
# VULNERABILITY DETECTION
# ========================================================================================


# ========================================================================================
# Single-agent VULNERABILITY DETECTION
# ========================================================================================

# Base Task Prompt 
VULNERABILITY_TASK_PROMPT = """Please analyze the following code:
```
{func}
```
Please indicate your analysis result with one of the options: 
(1) YES: A security vulnerability detected.
(2) NO: No security vulnerability. 

Make sure to include one of the options above "explicitly" (EXPLICITLY!!!) in your response.
Let's think step-by-step.
"""

# Few-Shot System Prompt (with examples)
SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT = """You are a security expert that is good at static program analysis.

Here are some examples of how to analyze code:

Example 1:
Code:
```c
char buffer[10];
strcpy(buffer, user_input);
```
Analysis: Let's think step-by-step. This code declares a fixed-size buffer of 10 characters and uses strcpy() to copy user_input into it. The strcpy() function does not perform bounds checking, so if user_input is longer than 9 characters (plus null terminator), it will cause a buffer overflow. This is a classic security vulnerability.
(1) YES: A security vulnerability detected.

Example 2:
Code:
```c
if (fd >= ctx->nr_user_files)
    return -EBADF;
fd = array_index_nospec(fd, ctx->nr_user_files);
```
Analysis: Let's think step-by-step. This code checks if fd is greater than or equal to ctx->nr_user_files before using it as an array index. However, this is an off-by-one error because valid array indices should be from 0 to (ctx->nr_user_files - 1). The condition should be fd >= ctx->nr_user_files to prevent accessing one element beyond the array bounds.
(1) YES: A security vulnerability detected.

Example 3:
Code:
```java
String query = "SELECT * FROM users WHERE id = '" + userId + "'";
return executeQuery(query);
```
Analysis: Let's think step-by-step. This Java code constructs a SQL query by directly concatenating user input (userId) into the query string. This allows an attacker to inject malicious SQL code through the userId parameter, leading to SQL injection attacks. The code should use parameterized queries instead.
(1) YES: A security vulnerability detected.

Example 4:
Code:
```c
if (!dest || !src || dest_size == 0) {
    return -1;
}
strncpy(dest, src, dest_size - 1);
dest[dest_size - 1] = '\0';
```
Analysis: Let's think step-by-step. This code properly validates input parameters (checking for null pointers and zero size), uses strncpy with a size limit that leaves room for null termination, and explicitly null-terminates the destination buffer. These are good security practices that prevent buffer overflows.
(2) NO: No security vulnerability.

Example 5:
Code:
```javascript
function displayContent(userInput) {
    document.getElementById('content').innerHTML = userInput;
}
```
Analysis: Let's think step-by-step. This JavaScript code directly inserts user input into the DOM using innerHTML without any sanitization. This allows an attacker to inject malicious HTML/JavaScript code that will execute in the user's browser, leading to Cross-Site Scripting (XSS) attacks.
(1) YES: A security vulnerability detected.

Example 6:
Code:
```java
if (userId == null || !userId.matches("^[0-9]+$")) {
    throw new IllegalArgumentException("Invalid user ID");
}
PreparedStatement stmt = connection.prepareStatement("SELECT * FROM users WHERE id = ?");
stmt.setString(1, userId);
```
Analysis: Let's think step-by-step. This code validates the userId parameter using regex to ensure it contains only digits, then uses a PreparedStatement with parameterized queries. The input validation prevents injection of non-numeric data, and the parameterized query prevents SQL injection. These are proper security practices.
(2) NO: No security vulnerability.

Now analyze the following code using the same approach:"""

# Zero-Shot System Prompt 
SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT = """You are a security expert that is good at static program analysis.

Your task is to analyze code functions and identify security vulnerabilities.

IMPORTANT: You MUST respond in the following format:

Step 1: Analyze the code carefully
Step 2: Identify potential security issues
Step 3: Make your final decision

Final Answer: [YES or NO]
- Answer YES if the code contains security vulnerabilities
- Answer NO if the code is secure

Then provide your reasoning.

Common vulnerabilities to look for:
- Buffer overflows
- SQL injection
- Command injection
- Path traversal
- Memory safety issues
- Race conditions
- Authentication/authorization bypasses
- Input validation issues
- Use-after-free
- Null pointer dereferences
- Integer overflows

Be thorough but decisive. You MUST answer either YES or NO."""



# ========================================================================================
# DUAL-AGENT VULNERABILITY DETECTION CONFIGURATION
# ========================================================================================

# Security Analyst Agent Prompt (combines analysis and decision-making)
SYS_MSG_SECURITY_ANALYST = """You are a Security Analyst responsible for analyzing code for vulnerabilities and making final security decisions.

Your responsibilities include:
1. Analyzing code for security vulnerabilities
2. Providing constructive feedback to developers
3. Making final decisions on vulnerability validity and severity

When providing feedback, identify potential security issues and explain:
- What the vulnerability is
- Why it's problematic
- How it could be exploited
- Suggested remediation approaches

When making final decisions, output your analysis as JSON with:
- "vulnerability_detected": boolean (true/false)
- "vulnerabilities": array of identified issues
- "reasoning": detailed explanation of your decision
- "confidence": your confidence level (high/medium/low)

Analyze code thoroughly for common security issues like buffer overflows, injection attacks, authentication bypasses, improper input validation, memory safety issues, race conditions, and other security weaknesses."""

# Dual Agent Task Messages

# Task 1: Code author submits code for analysis
DUAL_AGENT_TASK_CODE_SUBMISSION = """Please submit the following code for security analysis:

Code to analyze:
```
{code}
```

Please provide a brief description of what this code does and any security considerations you're aware of."""

# Task 2: Security analyst provides initial feedback
DUAL_AGENT_TASK_SECURITY_FEEDBACK = """Please analyze the following code submission for security vulnerabilities:

Code:
```
{code}
```

Author's submission:
{submission}

Provide detailed feedback on any security concerns you identify. Focus on:
- Potential vulnerabilities
- Security best practices that may be missing
- Specific recommendations for improvement"""

# Task 3: Code author revises based on feedback
DUAL_AGENT_TASK_CODE_REVISION = """Based on the security analyst's feedback, please provide your response:

Original code:
```
{original_code}
```

Security analyst feedback:
{feedback}

Please either:
1. Explain why the identified concerns are not valid vulnerabilities, or
2. Propose specific mitigation strategies to address the security concerns
3. Provide revised code if applicable

Focus on addressing each point raised by the security analyst."""

# Task 4: Security analyst makes final decision
DUAL_AGENT_TASK_FINAL_DECISION = """Please make your final security assessment based on the complete analysis:

Original code:
```
{original_code}
```

Your previous feedback:
{previous_feedback}

Author's response/revision:
{revised_analysis}

Provide your final decision as JSON format:
{{
    "vulnerability_detected": true/false,
    "vulnerabilities": [
        {{
            "type": "vulnerability_type",
            "severity": "high/medium/low",
            "description": "detailed description",
            "location": "specific code location if applicable"
        }}
    ],
    "reasoning": "detailed explanation of your final decision",
    "confidence": "high/medium/low"
}}

Consider the author's responses and determine if valid security vulnerabilities exist."""




# ========================================================================================
# MULTI-AGENT VULNERABILITY DETECTION CONFIGURATION 
# ========================================================================================

# Security Researcher Agent Prompt (from PDF Appendix A)
SYS_MSG_SECURITY_RESEARCHER = """You are the Security Researcher.
Identify all potential security vulnerabilities in the given code snippet.
Provide your output as a JSON array. Each element in the array represents one identified vulnerability and should include:
• "vulnerability": A short name or description of the vulnerability.
• "reason": A detailed explanation of why this is a vulnerability and how it could be exploited.
• "impact": The potential consequences if this vulnerability were exploited.

Analyze the code thoroughly for common security issues like buffer overflows, injection attacks, authentication bypasses, improper input validation, memory safety issues, race conditions, and other security weaknesses."""

# Code Author Agent Prompt (from PDF Appendix B)  
SYS_MSG_CODE_AUTHOR = """You are the Code Author of the attached code.
The Security Researcher has presented a JSON array of alleged vulnerabilities. You must respond as if you are presenting your case to a group of decision-makers who will evaluate each claim. Your tone should be respectful, authoritative, and confident, as if you are defending the integrity of your work to a panel of experts.

For each identified vulnerability, produce a corresponding JSON object with the following fields:
• "vulnerability": The same name/description from the Security Researcher's entry.
• "response-type": 'refutation' if you believe this concern is unfounded, or 'mitigation' if you acknowledge it and propose a workable solution.
• "reason": A concise explanation of why the vulnerability is refuted or how you propose to mitigate it."""

# Moderator Agent Prompt (from PDF Appendix C)
SYS_MSG_MODERATOR = """You are the Moderator, and your role is to provide a neutral summary.
After reviewing both the Security Researcher's identified vulnerabilities and the Code Author's responses, provide a JSON object with two fields:
• "security_researcher_summary": A concise summary of the vulnerabilities and reasoning presented by the Security Researcher.
• "author_summary": A concise summary of the Code Author's counterarguments or mitigation strategies."""

# Review Board Agent Prompt (from PDF Appendix D)
#Four agents
# SYS_MSG_REVIEW_BOARD = """You are the Review Board. After reviewing the Moderator's summary, Code Author's and Security Researcher's argument, and code, produce a JSON array of verdicts for each vulnerability identified by the Security Researcher. Each object in the array should include:
# • "vulnerability": The same name as given by the Security Researcher.
# • "decision": One of 'valid', 'invalid', or 'partially valid'.
# • "severity": If valid or partially valid, assign a severity ('low', 'medium', 'high'); if invalid, use 'none'.
# • "recommended_action": Suggest what should be done next (e.g., 'fix immediately', 'monitor', 'no action needed').
# • "reason": A brief explanation of why you reached this conclusion, considering both the Security Researcher's and Code Author's perspectives."""
#Three agents
# SYS_MSG_REVIEW_BOARD = """You are the Review Board. After reviewing the Security Researcher's analysis and Code Author's response directly, produce a JSON array of verdicts for each vulnerability identified by the Security Researcher. Each object in the array should include:
# - "vulnerability": The same name as given by the Security Researcher.
# - "decision": One of 'valid', 'invalid', or 'partially valid'.
# - "severity": If valid or partially valid, assign a severity ('low', 'medium', 'high'); if invalid, use 'none'.
# - "recommended_action": Suggest what should be done next (e.g., 'fix immediately', 'monitor', 'no action needed').
# - "reason": A brief explanation of why you reached this conclusion, considering both the Security Researcher's and Code Author's perspectives."""


# Multi-Agent Task Messages
MULTI_AGENT_TASK_SECURITY_RESEARCHER = "Analyze the following code for security vulnerabilities:\n\n```\n{code}\n```"

MULTI_AGENT_TASK_CODE_AUTHOR = """The Security Researcher found these potential vulnerabilities in your code:

{researcher_findings}

Code:
```
{code}
```

Please respond to each finding."""

MULTI_AGENT_TASK_MODERATOR = """Provide a neutral summary of this vulnerability discussion:

Security Researcher findings:
{researcher_findings}

Code Author response:
{author_response}"""

MULTI_AGENT_TASK_REVIEW_BOARD = """Review the following vulnerability assessment and make final decisions:

Moderator Summary:
{moderator_summary}

Original Code:
```
{code}
```

Security Researcher Analysis:
{researcher_findings}

Code Author Response:
{author_response}"""





