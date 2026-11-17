from kbws.main import app

# For local dev, i.e.: python kbws
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)