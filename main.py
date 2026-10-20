import os
import sys
import argparse
import uvicorn
from backend.app import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="National University AI Assistant Server")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "5005")), help="Port to run the server on")
    parser.add_argument("--host", type=str, default=os.getenv("HOST", "0.0.0.0"), help="Host to bind the server to")
    parser.add_argument("--reload", action="store_true", default=os.getenv("RELOAD", "false").lower() in ("true", "1", "yes"), help="Enable auto-reload")
    
    args, unknown = parser.parse_known_args()
    if unknown and unknown[0].isdigit():
        port = int(unknown[0])
    else:
        port = args.port
    host = args.host
    reload_enabled = args.reload

    print(f"Starting National University AI Assistant on http://{host}:{port}")
    
    if reload_enabled:
        uvicorn.run(
            "backend.app:app",
            host=host,
            port=port,
            reload=True,
            reload_dirs=["backend", "static"],
            reload_includes=["*.py", "*.html", "*.js", "*.css"]
        )
    else:
        uvicorn.run(app, host=host, port=port)