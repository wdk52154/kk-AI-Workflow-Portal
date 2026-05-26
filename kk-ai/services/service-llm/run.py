#!/usr/bin/env python3
"""Development entry point for service-llm."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9001,
        reload=True,
        log_level="info",
    )
