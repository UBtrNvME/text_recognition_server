import uvicorn
from fastapi import FastAPI, File, UploadFile

from app.services import ctpn
from app.utils import image as imagelib

app = FastAPI()


@app.get("/")
def index():
    pass


@app.post("/recognise")
async def recognise_text(image: UploadFile = File(...)):
    ndarray = await imagelib.to_nddarray(image.file)
    return ctpn.detect(ndarray)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
