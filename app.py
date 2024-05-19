from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import pickle
from sklearn.svm import SVC

app = Flask(__name__)
CORS(app)

# Load pre-trained SVM model (create this model separately)
with open('models/svm_model.pkl', 'rb') as f:
    svm_model = pickle.load(f)

with open('models/label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    # Registration logic to save user faces and update SVM model
    return jsonify({"status": "success"})

@app.route('/recognize', methods=['POST'])
def recognize():
    data = request.files['image'].read()
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    results = []
    for (x, y, w, h) in faces:
        face_img = gray_img[y:y+h, x:x+w]
        resized_face = cv2.resize(face_img, (64, 64))
        features = extract_features(resized_face)
        prediction = svm_model.predict([features])
        person = label_encoder.inverse_transform(prediction)[0]

        print(f"Recognized: {person}")
        
        results.append({
            'name': person,
            'box': [int(x), int(y), int(w), int(h)]
        })

    return jsonify(results)

def extract_features(image):
    # Extract features from the image (e.g., using HOG)
    winSize = (64, 64)
    blockSize = (16, 16)
    blockStride = (8, 8)
    cellSize = (8, 8)
    nbins = 9
    hog = cv2.HOGDescriptor(winSize, blockSize, blockStride, cellSize, nbins)
    features = hog.compute(image).flatten()
    return features

if __name__ == '__main__':
    app.run(debug=True)