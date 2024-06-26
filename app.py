import os
import io
import cv2
import time
import datetime
import random
import torch
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
from threading import Thread
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from sklearn.preprocessing import LabelEncoder
from cryptography.fernet import Fernet
from facenet_pytorch import InceptionResnetV1
from flask import Flask, render_template, Response, request, jsonify, send_file
from waitress import serve

app = Flask(__name__)
camera = None
camera_mode = None
camera_index = 0

# Load face recognition models
svm_model = None
label_encoder = None
facenet_model = InceptionResnetV1(pretrained='vggface2').eval()

# Create the attendance folder and file
ATTENDANCE_FOLDER = os.path.join('attendance', datetime.date.today().strftime('%m%d%Y'))
last_save_attendance = time.time()

os.makedirs('attendance', exist_ok=True)
if not os.path.exists(f'{ATTENDANCE_FOLDER}.xlsx'):
    attendance = pd.DataFrame(columns=['Name', 'Time', 'Probability'])
else:
    attendance = pd.read_excel(f'{ATTENDANCE_FOLDER}.xlsx')

def generate_key():
    key = Fernet.generate_key()
    with open('passkey/secret.key', 'wb') as key_file:
        key_file.write(key)
    return key

def load_key():
    os.makedirs('passkey', exist_ok=True)
    if not os.path.exists('passkey/secret.key'):
        key = generate_key()
        return key
    else:
        return open('passkey/secret.key', 'rb').read()
    
# Prepare the key and password
key = load_key()
cipher_suite = Fernet(key)
PASSWORD_FILE = 'passkey/encrypt.lock'

# Initialize with a default password if the file doesn't exist
if not os.path.exists(PASSWORD_FILE):
    with open(PASSWORD_FILE, 'wb') as file:
        encrypted_password = cipher_suite.encrypt(b'admin')  # Default password: 'admin'
        file.write(encrypted_password)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load_models')
def load_models():
    global svm_model
    global label_encoder
    
    if os.path.exists('models/svm_model.pkl') and os.path.exists('models/label_encoder.pkl') and os.path.exists('models/features.npy') and os.path.exists('models/labels.npy'):
        svm_model = joblib.load('models/svm_model.pkl')
        label_encoder = joblib.load('models/label_encoder.pkl')
    else:
        return jsonify({"error": "Models Missing"}), 401
    return jsonify({"message": "Models Loaded"}), 200

@app.route('/face_recognition', methods=['GET'])
def face_recognition():
    global camera
    global camera_mode

    if svm_model is None or label_encoder is None:
        return jsonify({"error": "Models Missing"}), 401
    if camera is None:
        camera = VideoCamera()
        camera_mode = 'recognition'
    return Response(generate_frame(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/face_capturing', methods=['GET'])
def face_capturing():
    global camera
    global camera_mode
    
    if camera is None:
        camera = VideoCamera()
        camera_mode = 'capture'
    return Response(generate_frame(camera), mimetype='multipart/x-mixed-replace; boundary=frame')
        
@app.route('/stop_feed')
def stop_feed():
    global camera
    global camera_mode
    global attendance

    if camera is not None:
        camera.__del__()
        camera = None
        camera_mode = None

    # Save the attendance to an Excel file
    if not attendance.empty:
        attendance = attendance.sort_values(by='Name')
        attendance.to_excel(f'{ATTENDANCE_FOLDER}.xlsx', index=False)
    return 'Webcam stopped'

@app.route('/capture_images', methods=['POST'])
def capture_images():
    global camera
    global camera_mode

    user_name = request.json.get('user_name')
    user_folder = os.path.join('faces', user_name)
    if not user_name:
        return jsonify({"error": "Username is required"}), 401
    
    if os.path.exists(user_folder):
        return jsonify({"error": "Username already exist"}), 401
    else:
        os.makedirs(user_folder, exist_ok=True)

    # Capture images
    count = 0
    image_number = 1
    while count < 50:
        if camera is None:
            break
        # Increment the image number if the file already exists
        while os.path.exists(os.path.join(user_folder, f'{image_number}.jpg')):
            image_number += 1
            
        frame = camera.capture_frame()
        file_path = os.path.join(user_folder, f'{image_number}.jpg')
        cv2.imwrite(file_path, frame)
        count += 1
        image_number += 1
        cv2.waitKey(800)

    return jsonify({"message": f"Captured {count} images"}), 200

@app.route('/training')
def training():
    global svm_model
    global label_encoder
    faces_dir = 'faces'
    image_count = 0
    face_count = 0
    no_face = 0
    multiple_face = 0
    X = []
    y = []

    os.makedirs('models', exist_ok=True)

    if not os.path.exists(faces_dir):
        return jsonify({"error": "No faces found"}), 401

    for person_name in os.listdir(faces_dir):
        person_dir = os.path.join(faces_dir, person_name)
        if not os.path.isdir(person_dir):
            continue
        for image_name in os.listdir(person_dir):
            image_path = os.path.join(person_dir, image_name)
            image = cv2.imread(image_path)
            if image is None:
                continue
            gray_frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(64, 64))
            
            # Check if the image has no face or multiple faces
            if len(faces) == 0:
                os.remove(image_path)
                no_face += 1
                continue
            elif len(faces) > 1:
                os.remove(image_path)
                multiple_face += 1
                continue
            
            for (x, z, w, h) in faces:
                face_img = image[z:z+h, x:x+w]
                features = extract_features(face_img)
                face_count += 1
                break
            X.append(features)
            y.append(person_name)
            image_count += 1

    X = np.array(X)
    y = np.array(y)

    # Save features and labels
    np.save('models/features.npy', X)
    np.save('models/labels.npy', y)
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    # Train SVM model
    svm_model = SVC(kernel='linear', probability=True)
    svm_model.fit(X, y_encoded)

    # Save model and label encoder
    joblib.dump(svm_model, 'models/svm_model.pkl')
    joblib.dump(label_encoder, 'models/label_encoder.pkl')

    # Get the unique classes from the SVM model
    unique_classes = svm_model.classes_
    num_classes = len(unique_classes)

    # Print the results
    print("Model Saved")
    print(f"Unique faces: {num_classes}")
    print(f"Image processed: {image_count}")
    print(f"Faces saved: {face_count}")
    print(f"No face: {no_face}")
    print(f"Multiple face: {multiple_face}")

    for i, class_label in enumerate(unique_classes):
        decoded_label = label_encoder.inverse_transform([class_label])[0]
        print(f"Class {i}: {decoded_label}")
    return jsonify({"message" : f"Registered Faces: {num_classes}"})
    
@app.route('/analyze_model', methods=['GET'])
def analyze_model():
    global label_encoder
    data = np.load('models/features.npy')
    labels = np.load('models/labels.npy')

    # Perform PCA to reduce to 2 dimensions for visualization
    pca = PCA(n_components=2)
    transformed_data = pca.fit_transform(data)
    
    # Plot the data points and decision boundaries
    plt.figure(figsize=(10, 8))
    random_color = generate_random_color()
    name_index = 0
    plt.scatter(transformed_data[0, 0], transformed_data[0, 1], label=label_encoder.inverse_transform([name_index])[0], c=random_color)
    
    for i in range(len(labels)):
        if labels[i] != label_encoder.inverse_transform([name_index])[0]:
            random_color = generate_random_color()
            name_index += 1
            plt.scatter(transformed_data[i, 0], transformed_data[i, 1], label=label_encoder.inverse_transform([name_index])[0], c=random_color)
        else:
            plt.scatter(transformed_data[i, 0], transformed_data[i, 1], c=random_color)
    
    # Set the plot properties
    plt.xlim(transformed_data[:, 0].min() - 0.1, transformed_data[:, 0].max() + 0.3)
    plt.ylim(transformed_data[:, 1].min() - 0.1, transformed_data[:, 1].max() + 0.1)
    plt.grid(True)
    plt.legend()
    plt.xlabel('PCA Component X')
    plt.ylabel('PCA Component Y')
    plt.title('FaceLog SVM Model Scatter Plot')
    
    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    
    return send_file(img, mimetype='image/png')

@app.route('/read_attendance')
def read_attendance_today():
    global ATTENDANCE_FOLDER
    if not os.path.exists(f'{ATTENDANCE_FOLDER}.xlsx'):
        return jsonify({"error": "No attendance for today"}), 401
    
    df = pd.read_excel(f'{ATTENDANCE_FOLDER}.xlsx')
    data = df.to_dict(orient='records')
    return jsonify(data)

@app.route('/list_attendance_files', methods=['GET'])
def list_attendance_files():
    attendance_files = [f for f in os.listdir('attendance') if f.endswith('.xlsx')]
    return jsonify(attendance_files)

@app.route('/read_attendance/<filename>', methods=['GET'])
def read_attendance(filename):
    attendance_file_path = os.path.join('attendance', filename)
    if not os.path.exists(attendance_file_path):
        return jsonify({"error": "File not found"}), 404

    df = pd.read_excel(attendance_file_path)
    data = df.to_dict(orient='records')
    return jsonify(data)

@app.route('/verify_password', methods=['POST'])
def verify_password():
    data = request.json
    password = data.get('password')
    
    encrypted_password = read_password()
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    
    if password == decrypted_password:
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'failure'}), 401

@app.route('/update_password', methods=['POST'])
def update_password():
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    encrypted_password = read_password()
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    
    if current_password == decrypted_password:
        new_encrypted_password = cipher_suite.encrypt(new_password.encode('utf-8'))
        write_password(new_encrypted_password)
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'failure'}), 401

@app.route('/list_cameras', methods=['GET'])
def get_cameras():
    cameras = list_cameras()
    return jsonify(cameras)

@app.route('/change_camera/<cameraIndex>', methods=['GET'])
def change_camera(cameraIndex):
    global camera_index
    camera_index = int(cameraIndex)
    return jsonify({"message": "Camera change."}), 200

class VideoCamera:
    # Threading for video capture and processing
    global attendance
    global camera
    global camera_index

    def __init__(self):
        self.video = cv2.VideoCapture(camera_index)
        self.grabbed, self.frame = self.video.read()
        self.last_recognition_time = time.time()
        self.running = True
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while self.running:
            self.grabbed, self.frame = self.video.read()

    def get_frame(self):
        frame = self.frame.copy()
        frame = cv2.flip(frame, 1)
        current_time = time.time()

        # Perform face recognition every 0.1 seconds
        if current_time - self.last_recognition_time >= 0.1:
            if camera_mode == 'recognition':
                frame = recognize_faces(frame)
                self.last_recognition_time = current_time
        
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def capture_frame(self):
        return self.frame.copy()
    
    def __del__(self):
        self.running = False
        self.video.release()

def list_cameras():
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            arr.append(index)
        cap.release()
        index += 1
    return arr

def generate_frame(camera):
    while camera.running:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        
def recognize_faces(frame):
    global attendance
    global ATTENDANCE_FOLDER
    global last_save_attendance
    current_time = time.time()

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(64, 64))

    for (x, y, w, h) in faces:
        face_img = frame[y:y+h, x:x+w]
        features = extract_features(face_img)

        prediction = svm_model.predict([features])
        proba = svm_model.predict_proba([features]).max()
        proba = round(proba, 2)
        person = label_encoder.inverse_transform(prediction)[0]

        if proba > 0.3:
            # Check if the person already exists in the DataFrame
            existing_record = attendance[attendance['Name'] == person]
            if existing_record.empty:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
                text = f'{person} ({proba})'
                cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                text = f'{person} ({proba})'
                cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                # If the person exists and the new probability is higher, update the record
                if proba > existing_record['Probability'].values[0]:
                    attendance.loc[existing_record.index, 'Probability'] = proba

            # If the person doesn't exist, append the new record
            if proba > 0.7 and existing_record.empty:
                attendance_time = datetime.datetime.now().strftime("%I:%M:%S %p")
                attendance = attendance._append({'Name': person, 'Time': attendance_time, 'Probability': proba}, ignore_index=True)

    # Save the Attendance every 10 seconds
    if current_time - last_save_attendance >= 10:
        if not attendance.empty:
            attendance = attendance.sort_values(by='Name')
            attendance.to_excel(f'{ATTENDANCE_FOLDER}.xlsx', index=False)
            last_save_attendance = current_time
    return frame

def extract_features(image):
    if len(image.shape) == 2 or image.shape[2] == 1:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    image = cv2.resize(image, (160, 160))
    image = (image / 255.0 - 0.5) * 2.0
    image = torch.tensor(image, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
    with torch.no_grad():
        features = facenet_model(image).cpu().numpy().flatten()
    return features

def generate_random_color():
    r = random.randint(0, 200)
    g = random.randint(0, 200)
    b = random.randint(0, 200)
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def read_password():
    with open(PASSWORD_FILE, 'rb') as file:
        return file.read()

def write_password(encrypted_password):
    with open(PASSWORD_FILE, 'wb') as file:
        file.write(encrypted_password)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=3000, debug=False)