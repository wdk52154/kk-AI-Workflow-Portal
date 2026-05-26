#!/usr/bin/env python3
"""Development entry point for service-rag."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9002,
        reload=True,
        log_level="info",
    )
