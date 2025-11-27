from fastapi import FastAPI

app = FastAPI(title="Veriply API")

@app.get("/")
async def root():
    return {"message": "Hello from Veriply API"}
