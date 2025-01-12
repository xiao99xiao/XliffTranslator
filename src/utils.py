import sys
from datetime import datetime

def log(message: str, error: bool = False, component: str = "GENERAL"):
    """Utility function for consistent logging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = f"[{timestamp}] [{component}] {message}"
    
    if error:
        print(output, file=sys.stderr, flush=True)
    else:
        print(output, flush=True) 