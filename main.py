from fastapi import FastAPI, File, UploadFile
import cv2
import mediapipe as mp
import numpy as np
import shutil
import os
import tempfile

app = FastAPI()
mp_pose = mp.solutions.pose

# دالة حساب الزوايا الهندسية
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360-angle
        
    return angle

@app.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    # 1. حفظ الفيديو المؤقت عشان نقدر نقرأه
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        shutil.copyfileobj(file.file, temp_video)
        video_path = temp_video.name

    cap = cv2.VideoCapture(video_path)
    
    # متغيرات لتخزين أعمق نقطة وصل ليها اللاعب (أقل زاوية)
    left_min_angle = 180
    right_min_angle = 180
    frames_processed = 0

    # 2. تشغيل الذكاء الاصطناعي على الفيديو
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frames_processed += 1
            # تحويل الألوان عشان MediaPipe يفهمها
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)

            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                
                # النقاط المهمة: 23(Hips), 25(Knee), 27(Ankle) للرجل الشمال
                if lm[23].visibility > 0.5 and lm[25].visibility > 0.5 and lm[27].visibility > 0.5:
                    angle_l = calculate_angle(
                        [lm[23].x, lm[23].y], 
                        [lm[25].x, lm[25].y], 
                        [lm[27].x, lm[27].y]
                    )
                    if angle_l < left_min_angle:
                        left_min_angle = angle_l

                # النقاط المهمة: 24, 26, 28 للرجل اليمين
                if lm[24].visibility > 0.5 and lm[26].visibility > 0.5 and lm[28].visibility > 0.5:
                    angle_r = calculate_angle(
                        [lm[24].x, lm[24].y], 
                        [lm[26].x, lm[26].y], 
                        [lm[28].x, lm[28].y]
                    )
                    if angle_r < right_min_angle:
                        right_min_angle = angle_r

    cap.release()
    os.remove(video_path) # مسح الفيديو المؤقت

    # 3. الحسابات والمنطق الطبي (Business Logic)
    
    # المدى الحركي (ROM) - كل ما الرقم زاد كل ما النزولة كانت أعمق
    l_rom = 180 - left_min_angle
    r_rom = 180 - right_min_angle
    
    # تجنب القسمة على صفر أو أرقام وهمية
    if l_rom < 10: l_rom = 10
    if r_rom < 10: r_rom = 10

    # تحديد الرجل الأضعف ونسبة التماثل (LSI)
    if l_rom < r_rom:
        lsi = (l_rom / r_rom) * 100
        weak_leg = "اليسرى"
    else:
        lsi = (r_rom / l_rom) * 100
        weak_leg = "اليمنى"

    score = int(lsi)
    
    # 4. نظام الفرز الطبي (Triage Protocol)
    is_critical = False
    is_risk = False
    action_type = "NONE"
    diagnosis = ""
    advice = ""

    if score < 65:
        # المنطقة الحمراء: خطر حرج
        is_critical = True
        is_risk = True
        diagnosis = "CRITICAL ASYMMETRY (خطر حرج)"
        advice = f"تحذير: قدمك {weak_leg} بها عجز وظيفي حاد ({100-score}% فرق).\nيمنع التمرين لتجنب التمزق. يجب زيارة مختص."
        action_type = "DOCTOR"
        
    elif score < 90:
        # المنطقة الصفراء: خطر متوسط (يحتاج تمارين)
        is_risk = True
        diagnosis = "Functional Imbalance (عدم توازن وظيفي)"
        advice = f"رصدنا ضعف في القدم {weak_leg}. يمكن علاجه ببرنامج التقوية المخصص."
        action_type = "EXERCISE"
        
    else:
        # المنطقة الخضراء: سليم
        diagnosis = "Optimal Symmetry (تماثل ممتاز)"
        advice = "أداء عضلي متزن ومثالي. استمر على هذا المستوى."
        action_type = "NONE"

    # 5. إرجاع النتيجة للتطبيق
    return {
        "score": f"التماثل: {score}%",
        "diagnosis": diagnosis,
        "advice": advice,
        "is_risk": is_risk,
        "is_critical": is_critical,
        "action_type": action_type,
        "weak_leg": weak_leg
    }
