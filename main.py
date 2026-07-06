import sys
import os
from src.gui_app import start_integrated_app

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    start_integrated_app()