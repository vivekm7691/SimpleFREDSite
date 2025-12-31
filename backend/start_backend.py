"""
Startup script for the backend with explicit logging configuration.
"""
import uvicorn
import sys

if __name__ == "__main__":
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    print("="*60)
    print("STARTING BACKEND SERVER")
    print("="*60)
    print("Logging should appear below for all requests...")
    print("="*60)
    sys.stdout.flush()
    
    # Configure uvicorn to show all logs
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Override any existing config
    )
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,  # Enable access logs - this should show request logs
        use_colors=False,  # Disable colors to avoid terminal issues
    )

