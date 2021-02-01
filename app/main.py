from fastapi import FastAPI, File, UploadFile

app = FastAPI()


@app.get("/")
def index():
    pass


@app.post("/recognise")
async def recognise_text(image: UploadFile = File(...)):
    return {"image": image.filename}
