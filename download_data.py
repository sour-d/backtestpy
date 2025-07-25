import sys
from utils.data_manager import run_download_process

if __name__ == "__main__":
    # Check for a '--force' argument
    force = "--force" in [arg.lower() for arg in sys.argv]
    run_download_process(force_download=force)
