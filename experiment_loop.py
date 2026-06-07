import subprocess
import sys

python_script = "run_experiment.py"

goal_run_count = 44
current_run_count = 1

while current_run_count <= goal_run_count:
    print("Running the run: ", current_run_count)
    result = subprocess.run([sys.executable, python_script, 'chinook', 'llama', str(1), str(current_run_count)])

    if result.returncode == 0:
        print("Succesfully ran the count number: ", current_run_count)
        current_run_count += 1
    else:
        print("Failed to run this run, trying again!")
