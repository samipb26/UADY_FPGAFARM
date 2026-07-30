import os
import random

# ==========================================
# CONFIGURATION
# ==========================================
# The directory where you want the fake files generated
OUTPUT_DIR = r"C:\Users\samip\OneDrive\Documents\UADY_AI_AGENT\AI_TESTING\test_reports\mock_data"
NUM_FILES_TO_GENERATE = 100

# ==========================================
# GENERATION LOGIC
# ==========================================
def generate_mock_reports():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    families = [
        "Cyclone V", "Cyclone V", "Cyclone V",  # Weighted to appear more often
        "Agilex", "Agilex", 
        "Stratix 10", "Arria II", "Unknown"     # Edge cases for your fallback logic
    ]

    print(f"Generating {NUM_FILES_TO_GENERATE} synthetic reports in {OUTPUT_DIR}...")

    for i in range(1, NUM_FILES_TO_GENERATE + 1):
        # 1. Randomize the metrics
        family = random.choice(families)
        
        # Create a mix of light, heavy, and edge-case resource usage
        alms = random.randint(1000, 60000)
        dsps = random.randint(0, 200)
        pins = random.randint(50, 400)
        
        # Add realistic comma formatting (e.g., 34000 -> 34,000)
        alms_str = f"{alms:,}"
        dsps_str = f"{dsps:,}"
        
        # 2. Construct the file content to match Quartus formats
        # We use semicolons to match your updated parsing regex
        file_content = f"""Flow Summary
-------------------------------------------------------
Flow Status ; Successful - Wed Jun 12 12:00:00 2026
Quartus Prime Version ; 22.1std.0 Build 915 10/25/2022 SC Lite Edition
Revision Name ; mock_project_{i}
Top-level Entity Name ; main_module
Family ; {family}
Device ; 5CSEMA5F31C6
Timing Models ; Final
Logic utilization (in ALMs) ; {alms_str} / 32,070 ( {min(100, int((alms/32070)*100))}% )
Total DSP Blocks ; {dsps_str} / 87 ( {min(100, int((dsps/87)*100))}% )
Total pins ; {pins} / 457 ( {int((pins/457)*100)}% )
"""
        
        # 3. Save the file
        filename = f"synthetic_test_{i:03d}_{family.replace(' ', '').lower()}.flow.rpt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w') as f:
            f.write(file_content)

    print("✅ Generation complete!")

if __name__ == "__main__":
    generate_mock_reports()