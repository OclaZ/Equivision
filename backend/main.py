from fastapi import FastAPI

app = FastAPI(title="EquiVision API")

@app.get("/")
def read_root():
    return {"message": "Welcome to EquiVision API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
