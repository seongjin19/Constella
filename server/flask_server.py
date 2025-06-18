from flask import Flask, request, jsonify
import torch
from PIL import Image
import io

app = Flask(__name__)

# 모델 로드 (path는 실제 위치)
model = torch.hub.load('ultralytics/yolov5', 'custom', path='model/best.pt', force_reload=True)
model.conf = 0.35
model.iou  = 0.45

print("▶ Available classes:", model.names)

@app.route("/detect", methods=["POST"])
def detect():
    # 1) 요청된 클래스 이름들
    requested = request.form.getlist("classes")  # ['orion','ursa_major']
    print("▶ Requested classes:", requested)

    # 2) 해당 이름들의 인덱스
    class_indices = [idx for idx, name in model.names.items() if name in requested]
    print("▶ Class indices:", class_indices)

    # 3) 이미지 로드
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    img_bytes = request.files["image"].read()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # 4) 추론 (전체 클래스)
    results = model(img)
    raw = results.xyxy[0].tolist()
    print("▶ Raw detections (before filtering):", raw)

    # 5) 필터링
    detections = []
    for *box, conf, cls_idx in raw:
        print(f"   - candidate box={box}, conf={conf:.3f}, cls_idx={cls_idx}")
        if conf >= model.conf and int(cls_idx) in class_indices:
            detections.append({
                "class": model.names[int(cls_idx)],
                "confidence": float(conf),
                "bbox": [float(round(x, 1)) for x in box]
            })
    print("▶ Filtered detections:", detections)

    return jsonify({"detections": detections})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)