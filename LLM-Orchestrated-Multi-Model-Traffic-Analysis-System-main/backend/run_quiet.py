#!/usr/bin/env python
"""
Ultra-Quiet Django runserver - minimal output
"""
import os
import sys
import subprocess
import warnings
import logging
import time

# Suppress ALL Python warnings
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Suppress Django logging completely
logging.disable(logging.CRITICAL)

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traffic_analysis.settings')

if __name__ == '__main__':
    # Default to 0.0.0.0:8000 if no arguments provided
    args = sys.argv[1:] if len(sys.argv) > 1 else ['0.0.0.0:8000']
    
    # Extract host and port for display
    host_port = args[0] if args else '0.0.0.0:8000'
    
    print("🚀 Starting backend server...")
    
    try:
        # Set environment variables to suppress Django output
        env = os.environ.copy()
        env.update({
            'PYTHONWARNINGS': 'ignore',
            'DJANGO_SETTINGS_MODULE': 'traffic_analysis.settings',
            'PYTHONUNBUFFERED': '0',  # Buffer output
            'DJANGO_LOG_LEVEL': 'ERROR'
        })
        
        # Start the process with minimal output
        cmd = [sys.executable, 'manage.py', 'runserver', '--noreload'] + args
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,  # Suppress stdout completely
            stderr=subprocess.PIPE,     # Capture stderr for errors only
            universal_newlines=True,
            env=env,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Give the server a moment to start
        time.sleep(2)
        
        # Check if process is still running (server started successfully)
        if process.poll() is None:
            print(f"✅ Server running at http://{host_port}")
            print("   Press Ctrl+C to stop")
        
        # Wait for the process and only show errors
        try:
            stderr_output = process.communicate()[1]
            if stderr_output and 'error' in stderr_output.lower():
                print(f"❌ Error: {stderr_output}")
        except:
            # Process was terminated normally
            pass
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)