from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def home():
    return {"message: HELLO"}

@app.get('/test')
def status():
    return {"Status : OK"}

