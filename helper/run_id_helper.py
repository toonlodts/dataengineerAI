from pathlib import Path

def get_run_id():
    path = Path("helper/run_id.txt")

    content = path.read_text()
    current = int(content)
    print(current)

    new_value = current + 1
    path.write_text(str(new_value))

    return "run_"+str(current)