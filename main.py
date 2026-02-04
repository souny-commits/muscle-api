from fastapi import FastAPI, File, UploadFile
import cv2
import mediapipe as mp
import numpy as np
import shutil
import os
import tempfile

app = FastAPI()
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    a = np.array(a); b = np.array(b); c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    if angle > 180.0: angle = 360-angle
    return angle

@app.post("/analyze")
async def analyze_muscle(file: UploadFile = File(...)):
    # حفظ الفيديو مؤقتاً
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        shutil.copyfileobj(file.file, temp_video)
        path = temp_video.name

    cap = cv2.VideoCapture(path)
    
    # متغيرات لتخزين أقصى نزول (عمق السكوات)
    left_min_angle = 180
    right_min_angle = 180
    
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                
                # قياس الرجل الشمال (نقاط 23, 25, 27)
                # نتأكد إن النقاط واضحة (>0.5 visibility)
                if lm[23].visibility > 0.5 and lm[25].visibility > 0.5 and lm[27].visibility > 0.5:
                    l_angle = calculate_angle(
                        [lm[23].x, lm[23].y], [lm[25].x, lm[25].y], [lm[27].x, lm[27].y])
                    if l_angle < left_min_angle: left_min_angle = l_angle

                # قياس الرجل اليمين (نقاط 24, 26, 28)
                if lm[24].visibility > 0.5 and lm[26].visibility > 0.5 and lm[28].visibility > 0.5:
                    r_angle = calculate_angle(
                        [lm[24].x, lm[24].y], [lm[26].x, lm[26].y], [lm[28].x, lm[28].y])
                    if r_angle < right_min_angle: right_min_angle = r_angle

    cap.release()
    os.remove(path)

    # الحسابات (LSI Logic)
    l_rom = 180 - left_min_angle
    r_rom = 180 - right_min_angle
    
    # تجنب الأصفار لو الفيديو ملوش علاقة
    if l_rom < 5: l_rom = 5 
    if r_rom < 5: r_rom = 5

    # حساب النسبة
    if l_rom < r_rom:
        lsi = (l_rom / r_rom) * 100
        weak_leg = "اليسرى"
    else:
        lsi = (r_rom / l_rom) * 100
        weak_leg = "اليمنى"

    # النتيجة النهائية
    is_risk = False
    advice = "عضلاتك متوازنة وممتازة ✅"
    
    if lsi < 85:
        is_risk = True
        advice = f"تحذير ⚠️: قدمك {weak_leg} أضعف بنسبة كبيرة ({int(100-lsi)}%). خطر إصابة عضلية!"

    return {
        "score": f"التماثل: {int(lsi)}%",
        "advice": advice,
        "is_risk": is_risk,
        "weak_leg": weak_leg
    }
