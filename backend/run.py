"""
Application Startup Script
Quick way to run the FastAPI application with uvicorn
"""
import uvicorn
import os

if __name__ == "__main__":
    # Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    RELOAD = os.getenv("RELOAD", "True").lower() == "true"
    
    print("=" * 60)
    print("🚀 Starting FairClaim Backend Server")
    print("=" * 60)
    print(f"🌐 Host: {HOST}")
    print(f"🔌 Port: {PORT}")
    print(f"🔄 Auto-reload: {RELOAD}")
    print(f"📚 API Docs: http://localhost:{PORT}/docs")
    print(f"📖 ReDoc: http://localhost:{PORT}/redoc")
    print("=" * 60)
    
    uvicorn.run(
        "app.main.app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level="info",
        access_log=True
    )
