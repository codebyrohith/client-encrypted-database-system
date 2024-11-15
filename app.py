from fastapi import FastAPI
from routes import app as routes_app

app = FastAPI(title="Legal Firm Secure Database System")

# Include the routes
app.include_router(routes_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)