
import os
import sys

# Ensure project root is on sys.path so `import models` works when running from subdirs/IDEs.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from user_interface.ui import launch_app

if __name__ == "__main__":
    launch_app()
