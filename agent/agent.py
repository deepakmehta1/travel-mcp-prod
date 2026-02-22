from app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    from app.config import load_settings

    settings = load_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)
