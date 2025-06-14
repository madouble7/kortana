import subprocess


def run_and_capture_output(command):
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
        )
        output = []
        for line in iter(process.stdout.readline, ""):
            print(line, end="")
            output.append(line)
        process.stdout.close()
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(
                return_code, command, output="\n".join(output)
            )
        return "\n".join(output)
    except subprocess.CalledProcessError as e:
        print(f"Error during execution: {e}")
        print(f"Output:\n{e.output}")
        return e.output
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return str(e)


if __name__ == "__main__":
    command_to_run = "python -m src.kortana.core.brain --autonomous"
    print(f"Executing: {command_to_run}")
    full_output = run_and_capture_output(command_to_run)
    with open("autonomous_run_output.txt", "w") as f:
        f.write(full_output)
    print("\nKORTANA_AUTONOMOUS_CAPTURE_COMPLETE")
