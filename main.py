from fastapi import FastAPI, Response, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import numpy as np
import cv2
from typing import List

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://prepro2.informatics.buu.ac.th:8065",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    model = YOLO("bestver17.pt")
except Exception as e:
    print(f"Error loading model: {e}")

def draw_lines_between_circles(frame, circles):
    sorted_circles = sorted(circles, key=lambda c: c[1])
    angle_A = angle_B = 0
    if len(sorted_circles) >= 2:
        for i in range(len(sorted_circles) - 1):
            cv2.line(frame, sorted_circles[i], sorted_circles[i + 1], (0, 255, 0), 2)
    if len(sorted_circles) >= 3:
        center_x = frame.shape[1] // 2
        center_y = sorted_circles[1][1]
        cv2.line(frame, (center_x, center_y), (0, center_y), (0, 255, 0), 2)
        cv2.line(frame, (center_x, center_y), (frame.shape[1], center_y), (0, 255, 0), 2)
        angle_1_2 = np.arctan2(sorted_circles[0][1] - sorted_circles[1][1], sorted_circles[0][0] - sorted_circles[1][0]) * 180 / np.pi
        angle_2_3 = np.arctan2(sorted_circles[1][1] - sorted_circles[2][1], sorted_circles[1][0] - sorted_circles[2][0]) * 180 / np.pi
        if angle_1_2 > 90:
            angle_A = 180 - angle_1_2
        elif angle_1_2 < -90:
            angle_A = 180 - (-angle_1_2)
        else:
            angle_A = angle_1_2
        if angle_2_3 > 90:
            angle_B = 180 - angle_2_3
        elif angle_2_3 < -90:
            angle_B = 180 - (-angle_2_3)
        else:
            angle_B = -angle_2_3
        angle_A = abs(angle_A)
        angle_B = abs(angle_B)
        midpoint_1_2 = ((sorted_circles[0][0] + sorted_circles[1][0]) // 2, (sorted_circles[0][1] + sorted_circles[1][1]) // 2)
        midpoint_2_3 = ((sorted_circles[1][0] + sorted_circles[2][0]) // 2, (sorted_circles[1][1] + sorted_circles[2][1]) // 2)
        font_scale = 0.5
        cv2.putText(frame, f"CVA : {round(angle_A, 2)} degrees", midpoint_1_2, cv2.FONT_HERSHEY_SIMPLEX, font_scale, (127, 0, 255), 1)
        cv2.putText(frame, f"FSP : {round(angle_B, 2)} degrees", midpoint_2_3, cv2.FONT_HERSHEY_SIMPLEX, font_scale, (127, 0, 255), 1)
    return angle_A, angle_B

@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    results = model(frame)
    detections = results[0].boxes
    circle_centers = []
    for detection in detections:
        if detection.cls == 0:
            x1, y1, x2, y2 = map(int, detection.xyxy[0])
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            circle_centers.append((center_x, center_y))
    annotated_frame = results[0].plot()
    cva = f'0 degrees'
    fsp = f'0 degrees'
    if len(circle_centers) == 3:
        cva, fsp = draw_lines_between_circles(annotated_frame, circle_centers)
    
    _, img_encoded = cv2.imencode('.jpg', annotated_frame)
    headers = {
        'CVA': str(round(cva, 2)),
        'FSP': str(round(fsp, 2)),
    }
    
    return Response(content=img_encoded.tobytes(), media_type="image/jpeg", headers=headers)
