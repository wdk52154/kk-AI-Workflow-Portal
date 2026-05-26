#!/usr/bin/env python3
"""Development entry point for service-memory."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9003,
        reload=True,
        log_level="info",
    )
