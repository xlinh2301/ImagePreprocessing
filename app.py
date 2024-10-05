import os
import cv2
import numpy as np
import pickle
import random
import tempfile
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from werkzeug.utils import secure_filename
from config import PATH_TO_DATASET, PATH_TO_DATASET_SEG
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn gốc
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/seg", StaticFiles(directory=PATH_TO_DATASET_SEG), name="seg")
templates = Jinja2Templates(directory="templates")

def load_features(pkl_file):
    with open(pkl_file, 'rb') as f:
        return pickle.load(f)

def cal_Hist(image_path):
    img = cv2.imread(image_path)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    channels = cv2.split(img)
    clahe_channels = [clahe.apply(channel) for channel in channels]
    hist_b = cv2.calcHist([clahe_channels[0]], [0], None, [256], [0, 256])
    hist_g = cv2.calcHist([clahe_channels[1]], [0], None, [256], [0, 256])
    hist_r = cv2.calcHist([clahe_channels[2]], [0], None, [256], [0, 256])
    cv2.normalize(hist_b, hist_b)
    cv2.normalize(hist_g, hist_g)
    cv2.normalize(hist_r, hist_r)
    hist_combined = np.concatenate((hist_b, hist_g, hist_r)).flatten()
    return hist_combined

def compare_Hist(hist1, hist2, method=cv2.HISTCMP_CORREL):
    return cv2.compareHist(hist1, hist2, method)

def find_similar_images(hist_input, features):
    results = []
    for img_path, hist_feature in features:
        if hist_feature.shape != hist_input.shape:
            print(f"Skipping comparison for {img_path} due to size mismatch.")
            continue
        comparison_result = compare_Hist(hist_feature, hist_input)
        img_path = img_path.split('/')[1:]
        img_path = os.path.join(PATH_TO_DATASET, *img_path)
        info = {
            "img_path": img_path,
            "comparison_result": comparison_result
        }
        results.append(info)
    sorted_results = sorted(results, key=lambda x: x['comparison_result'], reverse=True)
    # print(sorted_results[0])
    return sorted_results[:10]

# @app.get("/", response_class=HTMLResponse)  
# async def index(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    if file.filename == '':
        return RedirectResponse(url="/", status_code=303)
    if file:
        print("file:", file)
        filename = secure_filename(file.filename)
        print("file name:", filename)

        image_data = await file.read()

        # Sử dụng tệp tin tạm thời
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
            # print("temp_file_path:", temp_file_path)
        try:
            feature = load_features('features.pkl')
            hist_input = cal_Hist(temp_file_path)
            # print("hist_input:", hist_input)
            sorted_results = find_similar_images(hist_input, feature)
            # return templates.TemplateResponse("results.html", {"request": request, "input_image": temp_file_path, "results": sorted_results[:10]})
            return sorted_results
        finally:
            # Xóa tệp tin tạm thời sau khi xử lý
            os.remove(temp_file_path)

    return RedirectResponse(url="/", status_code=303)

# @app.post("/upload", response_class=HTMLResponse)
# async def upload(request: Request, file: UploadFile = File(...)):
#     if file.filename == '':
#         return RedirectResponse(url="/", status_code=303)
#     if file:
#         filename = secure_filename(file.filename)
#         filepath = os.path.join("static/uploads", filename)
#         with open(filepath, "wb") as buffer:
#             buffer.write(file.file.read())
#         feature = load_features('features.pkl')
#         hist_input = cal_Hist(filepath)
#         sorted_results = find_similar_images(hist_input, feature)
#         return templates.TemplateResponse("results.html", {"request": request, "input_image": filepath, "results": sorted_results[:10]})
#     return RedirectResponse(url="/", status_code=303)
