import os
import json
import time
import matplotlib.pyplot as plt
import ollama
import csv


# ==========================================
# 1. CONFIGURATION & SETUP
# ==========================================
RPT_DIRECTORY = r"C:\Users\samip\OneDrive\Documents\UADY_AI_AGENT\AI_TESTING\test_reports\mock_data"  
MODEL_NAME = "qwen2.5:7b"

# Our explicit mappings based on your project files
EXPECTED_OUTPUTS = {
    "agilex_heavy_core.flow.rpt": "Agilex 10",
    "alm_annihilator.flow.rpt": "Agilex 10",
    "alm_ram_killer.flow.rpt": "Agilex 10",
    "full_adder.flow.rpt": "DE-SoC",
    "project_clockdiv.flow.rpt": "DE-SoC",
    "project1_logicgates.flow.rpt": "DE-SoC",
    "project2_pushsegments.flow.rpt": "DE-SoC",
    "project3_segmentsdecoder.flow.rpt": "DE-SoC",
    "project5_digitcount.flow.rpt": "DE-SoC",
    "project6_servocontroller.flow.rpt": "DE-SoC",
    "project7_laboratory.flow.rpt": "DE-SoC",
    "project8_keypadh.flow.rpt": "DE-SoC",
    "project9_calc.flow.rpt": "DE-SoC"
}

SYSTEM_PROMPT = """
You are an automated routing agent for an FPGA farm.
You will receive JSON data containing the target "family" and resource metrics for a compiled hardware task.

Routing Rules:
1. Supported families: "Cyclone V", "Agilex 7", and "Unknown".
2. DE-SoC physical limits: Maximum 32,000 ALMs and Maximum 80 DSP blocks. 
3. If the family is "Cyclone V": You MUST assign "DE-SoC". (If resources exceed Rule 2 limits, return "Error").
4. If the family is "Agilex 7": You MUST assign "Agilex 10". NEVER assign "DE-SoC" to an Agilex 7 project, as the hardware is incompatible. 
   - Efficiency Coach: If the resources (total_alms and dsp_blocks) are BOTH below the DE-SoC limits, append this exact warning to your reasoning: "This design only uses [X] ALMs and [Y] DSPs. It could theoretically be recompiled for a DE-SoC board to save Agilex resources."
5. If the family is "Unknown": If total_alms > 32000 or dsp_blocks > 80, assign "Agilex 10". Otherwise, assign "DE-SoC".

Output your routing decision strictly 
in JSON format using this exact schema, 
with no additional text: 
{"assigned_architecture": "Agilex 10" | 
"DE-SoC" | "Error", "reasoning": "brief explanation"}
"""



# ==========================================
# 2. PARSING LOGIC (Updated for Synthetic Data)
# ==========================================
def parse_flow_rpt(filepath):
    """
    Parses a local Quartus .flow.rpt file using string splitting on semicolons.
    Updated to capture 2-part synthetic data format.
    """
    task_data = {
        "task_id": os.path.basename(filepath),
        "family": "Unknown",
        "total_alms": 0,
        "dsp_blocks": 0
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                if "Family" in line:
                    parts = line.split(";")
                    # The mock data splits into 2 parts, so we grab index 1
                    if len(parts) >= 2: 
                        task_data["family"] = parts[1].strip()
                        
                # Added 'Logic utilization' to catch the mock data ALMs string
                elif "Total ALMs" in line or "Total logic elements" in line or "Logic utilization" in line:
                    parts = line.split(";")
                    if len(parts) >= 2:
                        val = parts[1].strip()
                        # Handle formats like "34,000 / 32,070" and remove commas
                        val_cleaned = val.split('/')[0].strip().replace(',', '')
                        try:
                            task_data["total_alms"] = int(val_cleaned)
                        except ValueError:
                            pass
                            
                elif "Total DSP Blocks" in line or "DSP Blocks" in line:
                    parts = line.split(";")
                    if len(parts) >= 2:
                        val = parts[1].strip()
                        val_cleaned = val.split('/')[0].strip().replace(',', '')
                        try:
                            task_data["dsp_blocks"] = int(val_cleaned)
                        except ValueError:
                            pass
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        
    return task_data

# ==========================================
# 3. DIRECT OLLAMA INFERENCE
# ==========================================
def query_local_ollama(task_data):
    """
    Queries your local Ollama instance directly without an intermediate server.
    """
    try:
        task_json_str = json.dumps(task_data)
        response = ollama.chat(
            model=MODEL_NAME, 
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': task_json_str}
            ],
            format='json',
            options={'temperature': 0.0} # Keep choices as deterministic as possible
        )
        
        # Parse output from model string response
        raw_content = response['message']['content']
        parsed_response = json.loads(raw_content)
        return parsed_response.get("assigned_architecture", "Error")
        
    except Exception as e:
        print(f"  [ERROR] Ollama extraction failed for {task_data['task_id']}: {e}")
        return "Error"

# ==========================================
# 4. BENCHMARK EXECUTION LOOP
# ==========================================
def run_benchmark():
    if not os.path.exists(RPT_DIRECTORY):
        os.makedirs(RPT_DIRECTORY)
        print(f"Created '{RPT_DIRECTORY}' directory. Place your .flow.rpt files inside and rerun.")
        return None

    test_files = [f for f in os.listdir(RPT_DIRECTORY) if f.endswith('.flow.rpt')]
    if not test_files:
        print(f"No .flow.rpt files discovered in '{RPT_DIRECTORY}'.")
        return None

    # Added "error_category" to the dictionary
    results = {
        "files": [], "family": [], "alms": [], "dsps": [],
        "ground_truth": [], "ai_routing": [], 
        "response_times": [], "accuracies": [], "error_category": []
    }
    
    print(f"Found {len(test_files)} testing profiles. Prompting model: '{MODEL_NAME}'...\n")

    for filename in test_files:
        filepath = os.path.join(RPT_DIRECTORY, filename)
        
        parsed_metrics = parse_flow_rpt(filepath)
        family = parsed_metrics["family"]
        alms = parsed_metrics["total_alms"]
        dsps = parsed_metrics["dsp_blocks"]

        # Ground Truth Rules
        if family not in ["Cyclone V", "Agilex", "Unknown"]:
            correct_architecture = "Error"
        elif "Cyclone V" in family:
            if alms > 32000 or dsps > 80: correct_architecture = "Error" 
            else: correct_architecture = "DE-SoC"
        elif "Agilex" in family:
            # NEW: Added limit check for Agilex (Max 87 DSPs)
            if dsps > 87: correct_architecture = "Error"
            else: correct_architecture = "Agilex 10"
        else: # "Unknown"
            if dsps > 87: correct_architecture = "Error" # Catches tasks too big for Agilex
            elif alms > 32000 or dsps > 80: correct_architecture = "Agilex 10"
            else: correct_architecture = "DE-SoC"
        
        start_time = time.perf_counter()
        ai_architecture = query_local_ollama(parsed_metrics)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000
        is_accurate = 1.0 if ai_architecture == correct_architecture else 0.0
        
        # --- NEW: ERROR CATEGORIZATION LOGIC ---
        if is_accurate == 1.0:
            error_cat = "Correct"
        elif correct_architecture == "Error" and ai_architecture != "Error":
            error_cat = "Failed to Reject" # AI allowed a bad task through
        elif correct_architecture != "Error" and ai_architecture == "Error":
            error_cat = "False Rejection"  # AI blocked a valid task
        elif correct_architecture in ["Agilex 10", "DE-SoC"] and ai_architecture in ["Agilex 10", "DE-SoC"]:
            error_cat = "Wrong Board"      # AI flipped the valid boards
        else:
            error_cat = "Syntax/Format Error" # AI outputted garbage text
            
        # Record keeping
        results["files"].append(filename)
        results["family"].append(family)
        results["alms"].append(alms)
        results["dsps"].append(dsps)
        results["ground_truth"].append(correct_architecture)
        results["ai_routing"].append(ai_architecture)
        results["response_times"].append(latency_ms)
        results["accuracies"].append(is_accurate)
        results["error_category"].append(error_cat) # Save the category
        
        status = "✅ PASS" if is_accurate else f"❌ FAIL ({error_cat})"
        print(f"[{status}] {filename} | {latency_ms:.0f}ms")

    return results

# ==========================================
# 5. CSV EXPORT
# ==========================================
def export_to_csv(results):
    import csv
    csv_filename = os.path.join(RPT_DIRECTORY, "benchmark_results.csv")
    
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Added Error Type to headers
        writer.writerow(["Filename", "Parsed Family", "Parsed ALMs", "Parsed DSPs", 
                         "Ground Truth", "AI Decision", "Latency (ms)", "Pass/Fail", "Error Type"])
        
        for i in range(len(results["files"])):
            pass_fail = "PASS" if results["accuracies"][i] == 1.0 else "FAIL"
            writer.writerow([
                results["files"][i], results["family"][i], results["alms"][i], 
                results["dsps"][i], results["ground_truth"][i], results["ai_routing"][i], 
                round(results["response_times"][i], 2), pass_fail, results["error_category"][i]
            ])
            
    print(f"\n📊 Raw data successfully exported to: {csv_filename}")

# ==========================================
# 6. MATPLOTLIB VISUALIZATION (OVERHAULED)
# ==========================================
def generate_performance_chart(results):
    latencies = results["response_times"]
    accuracies = results["accuracies"]
    error_cats = results["error_category"]
    test_sequence = list(range(1, len(latencies) + 1))

    avg_latency = sum(latencies) / len(latencies)
    total_accuracy = (sum(accuracies) / len(accuracies)) * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle(f"Agent Benchmark: {MODEL_NAME} | Accuracy: {total_accuracy:.1f}% | Avg Latency: {avg_latency:.0f}ms", 
                 fontsize=14, fontweight='bold', y=0.98)

    # --- Subplot 1: Differentiated Scatter Plot ---
    # Define our visual markers for each category
    markers = {
        "Correct": {"color": "tab:green", "marker": "o", "size": 50, "label": "Correct Route"},
        "Failed to Reject": {"color": "tab:orange", "marker": "^", "size": 80, "label": "Failed to Reject (Over Limit)"},
        "False Rejection": {"color": "tab:purple", "marker": "v", "size": 80, "label": "False Rejection (Valid Task)"},
        "Wrong Board": {"color": "tab:red", "marker": "X", "size": 80, "label": "Wrong Board Assigned"},
        "Syntax/Format Error": {"color": "black", "marker": "*", "size": 90, "label": "Syntax/Format Error"}
    }

    # Plot each category separately
    for category, style in markers.items():
        x_vals = [i for i, cat in zip(test_sequence, error_cats) if cat == category]
        y_vals = [lat for lat, cat in zip(latencies, error_cats) if cat == category]
        
        # Only add to legend if the error actually occurred
        if x_vals: 
            # Add black edges to standard shapes to make them pop out more
            edge = 'black' if style["marker"] in ['o', '^', 'v'] else None
            ax1.scatter(x_vals, y_vals, color=style["color"], marker=style["marker"], 
                        s=style["size"], label=style["label"], alpha=0.8, edgecolors=edge)

    ax1.set_title("Response Time & Error Classification", fontweight='bold')
    ax1.set_xlabel("Test Sequence Number")
    ax1.set_ylabel("Inference Latency (ms)")
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # Move legend outside the plot area slightly so it doesn't cover data points
    ax1.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=9, framealpha=0.9)

    # --- Subplot 2: Latency Distribution (Histogram) ---
    ax2.hist(latencies, bins=15, color='tab:blue', edgecolor='black', alpha=0.7)
    ax2.set_title("Distribution of Response Times", fontweight='bold')
    ax2.set_xlabel("Latency Ranges (ms)")
    ax2.set_ylabel("Frequency (Number of Tests)")
    ax2.grid(True, linestyle='--', alpha=0.6, axis='y')

    plt.tight_layout(rect=[0, 0, 1, 0.95]) 
    plt.show()

# ==========================================
# MAIN EXECUTION ENTRYPOINT
# ==========================================
if __name__ == "__main__":
    benchmark_data = run_benchmark()
    if benchmark_data:
        export_to_csv(benchmark_data)
        generate_performance_chart(benchmark_data)