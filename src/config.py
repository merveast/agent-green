
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



# =======================================================================
# VULNERABILITY DETECTION
# =======================================================================

# ---------------------------
# Few-Shot Examples
# ---------------------------
EXAMPLE_C_VULN = r"""```c
char buffer[10];
strcpy(buffer, user_input);
```
Analysis: This code uses strcpy() with no bounds checking. If user_input exceeds 10 bytes, a buffer overflow occurs.
"""

EXAMPLE_C_SAFE = r"""```c
int validate_and_copy(char *dest, const char *src, size_t dest_size) {
    if (!dest || !src || dest_size == 0) return -1;
    size_t src_len = strlen(src);
    if (src_len >= dest_size) return -1;
    strncpy(dest, src, dest_size - 1);
    dest[dest_size - 1] = '\\0';
    return 0;
}
```
Analysis: All inputs validated, copy is bounded and null-terminated. No overflow risk.
"""

EXAMPLE_CPP_VULN = r"""```cpp
class UserManager {
private:
    std::vector<User*> users;
public:
    void addUser(const std::string& name, const std::string& password) {
        users.push_back(new User(name, password));
    }
    void deleteUser(int idx) {
        if (idx >= 0 && idx < users.size())
            users.erase(users.begin() + idx);
    }
    ~UserManager() {}
};
```
Analysis: deleteUser removes elements without deleting underlying objects. Destructor does not free memory -> memory leak.
"""

# =======================================================================
# SINGLE AGENT PROMPTS Vulnerability Detection
# =======================================================================
VULNERABILITY_TASK_PROMPT = """Please analyze the following code:
```
{code}
```
Please indicate your result:
(1) YES: Vulnerability detected.
(2) NO: No vulnerability.
Let's think step-by-step."""

SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT = f"""You are a security expert skilled in static analysis.
Use these canonical examples as your guide:

Example 1 (C vulnerable):
{EXAMPLE_C_VULN}
(1) YES

Example 2 (C safe):
{EXAMPLE_C_SAFE}
(2) NO

Example 3 (C++ vulnerable):
{EXAMPLE_CPP_VULN}
(1) YES

Now analyze the following code and respond with explicit YES or NO."""

SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT = """You are a security expert skilled in static program analysis.
Analyze the provided code and decide whether it is vulnerable (YES) or not (NO)."""

# =======================================================================
# DUAL AGENT PROMPTS (Analyst -> Code Author) Vulnerability Detection
# =======================================================================
SYS_MSG_SECURITY_ANALYST_FEW_SHOT = f"""You are a Security Analyst. Analyze code and produce structured JSON outputs.
Use these examples to guide structure and depth:

Example 1 (C vulnerable):
{EXAMPLE_C_VULN}
Output:
{{
  "vulnerability_detected": true,
  "vulnerabilities": [{{"type": "Buffer overflow", "description": "strcpy() used without bounds checking", "location": "strcpy(buffer, user_input)"}}],
  "reasoning": "Unbounded strcpy may cause overflow.",
  "confidence": "high"
}}

Example 2 (C safe):
{EXAMPLE_C_SAFE}
Output:
{{
  "vulnerability_detected": false,
  "vulnerabilities": [],
  "reasoning": "Input validation and bounded copy prevent overflow.",
  "confidence": "high"
}}

Example 3 (C++ vulnerable):
{EXAMPLE_CPP_VULN}
Output:
{{
  "vulnerability_detected": true,
  "vulnerabilities": [{{"type": "Memory leak", "description": "Objects not deleted in destructor", "location": "~UserManager"}}],
  "reasoning": "Allocated objects not freed; memory leak risk.",
  "confidence": "high"
}}

Now analyze the provided code in the same JSON format."""

SYS_MSG_SECURITY_ANALYST_ZERO_SHOT = """You are a Security Analyst. Identify vulnerabilities and output JSON with:
vulnerability_detected (bool), vulnerabilities (array), reasoning, confidence."""

SYS_MSG_CODE_AUTHOR_DUAL_FEW_SHOT = f"""You are the Code Author responding to the Security Analyst's findings.
Use the same canonical examples to stay consistent:

Example 1 (C vulnerable):
Finding: Buffer overflow due to strcpy()
Response:
[{{"vulnerability": "Buffer Overflow", "response-type": "mitigation", "reason": "Replace strcpy with strncpy and add length validation."}}]

Example 2 (C safe):
Finding: None
Response: []

Example 3 (C++ vulnerable):
Finding: Memory leak due to missing delete
Response:
[{{"vulnerability": "Memory Leak", "response-type": "mitigation", "reason": "Implement destructor to delete allocated User objects."}}]

Now respond to the findings using JSON format."""

SYS_MSG_CODE_AUTHOR_DUAL_ZERO_SHOT = """You are the Code Author. For each finding, respond in JSON with keys:
vulnerability, response-type ('mitigation' or 'refutation'), and reason."""

# --- Dual-Agent Task Templates ---
DUAL_AGENT_TASK_CODE_SUBMISSION = """The following code is written by you (Code Author). 
Please explain or justify its behavior as if you implemented it:

```
{code}
```
Describe its intent and any design choices made. Be honest about potential risky parts if any exist."""

DUAL_AGENT_TASK_FINAL_DECISION = """You are the Security Analyst reviewing the Code Author's explanation. 
Please decide whether the following code contains a vulnerability.

Original Code:
```
{code}
```
Author’s Explanation:
{author_response}

Respond clearly in JSON format:
{{
  "vulnerability_detected": true/false,
  "vulnerabilities": [{{"type": "...", "description": "..."}}],
  "analysis": "concise reasoning or justification"
}}"""

# =======================================================================
# MULTI AGENT PROMPTS Vulnerability Detection
# =======================================================================
SYS_MSG_SECURITY_RESEARCHER_FEW_SHOT = f"""You are the Security Researcher. Identify vulnerabilities in JSON (vulnerability, reason, impact).
Use these examples:

Example 1 (C vulnerable):
{EXAMPLE_C_VULN}
Output:
[{{"vulnerability": "Buffer Overflow", "reason": "strcpy without bounds checking", "impact": "Stack overflow / code execution"}}]

Example 2 (C safe):
{EXAMPLE_C_SAFE}
Output: []

Example 3 (C++ vulnerable):
{EXAMPLE_CPP_VULN}
Output:
[{{"vulnerability": "Memory Leak", "reason": "Objects not freed in destructor", "impact": "Resource exhaustion"}}]

Now analyze the given code."""

SYS_MSG_SECURITY_RESEARCHER_ZERO_SHOT = """You are the Security Researcher. Output JSON list of vulnerabilities with keys: vulnerability, reason, impact."""

SYS_MSG_CODE_AUTHOR_FEW_SHOT = f"""You are the Code Author. Respond to the Researcher's findings.
Use the same canonical examples as guide:

Example 1 (C vulnerable):
Finding: Buffer overflow
Response:
[{{"vulnerability": "Buffer Overflow", "response-type": "mitigation", "reason": "Replace strcpy with strncpy and validate input length."}}]

Example 2 (C safe):
Finding: None
Response: []

Example 3 (C++ vulnerable):
Finding: Memory leak
Response:
[{{"vulnerability": "Memory Leak", "response-type": "mitigation", "reason": "Add destructor to free memory."}}]"""

SYS_MSG_CODE_AUTHOR_ZERO_SHOT = """You are the Code Author. For each vulnerability, output JSON with vulnerability, response-type, and reason."""

SYS_MSG_MODERATOR_FEW_SHOT = """You are the Moderator. Summarize neutrally both parties' arguments in JSON:
{{
  "security_researcher_summary": "...",
  "author_summary": "..."
}}
Use same examples for consistency."""

SYS_MSG_MODERATOR_ZERO_SHOT = """You are the Moderator. Output neutral JSON summary comparing Researcher and Author."""

SYS_MSG_REVIEW_BOARD_FEW_SHOT = """You are the Review Board. Based on the Moderator's summary, issue final verdicts in JSON array with fields:
vulnerability, decision, severity, recommended_action, reason."""

SYS_MSG_REVIEW_BOARD_ZERO_SHOT = """You are the Review Board. Produce final JSON verdicts (vulnerability, decision, severity, recommended_action, reason)."""

# --- Multi-Agent Task Templates ---
MULTI_AGENT_TASK_SECURITY_RESEARCHER = """Analyze the following code for vulnerabilities:
```
{code}
```"""

MULTI_AGENT_TASK_CODE_AUTHOR = """The Security Researcher found:
{researcher_findings}
Code:
```
{code}
```
Please respond to each finding."""

MULTI_AGENT_TASK_MODERATOR = """Provide a neutral summary of this discussion:
Security Researcher findings:
{researcher_findings}
Code Author response:
{author_response}"""

MULTI_AGENT_TASK_REVIEW_BOARD = """Review and decide based on:
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






