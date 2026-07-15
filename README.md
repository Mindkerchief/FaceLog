# <img src="https://github.com/AHG-BSCS/FaceLog/blob/ab54d32cf391034d75df41502050832b38004424/app/static/image/icon.png" width="28" alt="Logo Thumbnail"> FaceLog ![facelog badge][facelog-badge]
A Windows application that can record attendance using facial recognition. This application provides basic tools to register user's face and record attendance. Registering new attendees, training models and checking attendance can be done through the app directly.

## Table of Contents
- [Features](#features)
- [Guidelines](#guidelines)
- [Installation](#installation)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features
### Main Features
![facial recognition][facial-recognition] &nbsp;
![face apturing][face-capturing]
- **Start Facial Recognition** - Start the real-time facial recognition to record the attendance.
- **Register User** - Capture images of the attendee's face for the system to recognize the face.

![chart][chart] &nbsp;
![attendance table][attendance-table]
- **Update Model** - Train the model using the captured faces dataset. This can take some time depending on the size of the dataset.
- **Analyze Model** - Generate a scatter plot chart in a 2D plane representing the current model data distribution.
- **View Attendance** - Opens the attendance table and displays the existing attendance from the Excel files.

### Additional Features
![password change][password-change] &nbsp;
![camera selector][camera-selector] &nbsp;
![attendance selector][attendance-selector]
- **Change Password** - Change the system's password to improve security.
- **Camera Selection** - Switch between available cameras connected to the device.
- **Attendance File Selection** - Switch between available attendance files.
- **Button Tooltips** - Helps user understand the button's functionality.
- **Dynamic Buttons** - Helps user identify the button and system state.
- **Protected Buttons** - Prevent sensitive actions from being executed without permission.

> [!IMPORTANT]
> The default password is `admin`.

> [!NOTE]
> The system performs facial recognition every 0.1 seconds to improve performance.
> It will recognize face at 30% probability but only record attendance if above 70% probability.

## Guidelines
### Dataset Capturing Guidelines
1. Keep the background plain without patterns, movements and other people.
2. It is recommended to take the face dataset capturing two times. One in a well-lit environment and another in a darker environment.
3. During capturing, try to move the attendees' heads at different angles slowly. Move from left to right and try to write the letter O using their head.
4. During capturing, try to mimic different common emotions, visible teeth and talking.
5. Capturing 50 face variations is not required but it would be ideal as long as the attendees are still comfortable during the process. At least providing 30 images can be acceptable but can produce less desirable results.

### Dataset Management Guidelines
1. Datasets are stored in the `faces` folder. Each attendee's name is inside the folder and the system uses the folder name as the attendee's name.
2. In case of capturing a dataset of the same attendees where there is a name conflict, you can temporarily add numbers to the attendee's name during registration and then move the images to the proper folder later.
3. In case of gathering datasets from external sources like social media and personal photos, you can move those images directly to the proper attendee's folder.
4. During training, the system automatically deletes datasets with no face or multiple faces.
5. Sometimes, patterns in the background can be recognized as faces and the program cannot differentiate the error, that is why [facefilter.py](facefilter.py) is created to manually review datasets, especially those which come from external sources.

> [!WARNING]
> Always have a backup of your dataset since training the model will delete invalid datasets.

## Installation
1. Download and install the latest version of [FaceLog][release-page].

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- **[LSPU-SPCC BSCS2A A.Y 2023-2024][lspu-spcc-bscs2a-ay-2023-2024]**: For contributing their faces dataset.
- **[css.gg][css-gg]**: For icons.
- **[flask_cors][flask-cors]**: For handling resource sharing between Python and JavaScript.
- **[waitress][waitress]**: For production-ready WSGI server.
- **[PyWebview][pywebview]**: For standalone web app wrapper.
- **[PyInstaller][pyinstaller]**: For building the app into executables.
- **[Inno Setup][inno-setup]**: For installer.
- **[facenet-pytorch][facenet-pytorch]**: For providing a pre-trained model for facial recognition.
- **[opencv-python][opencv-python]**: For image processing.
- **[scikit-learn][scikit-learn]**: For machine learning and statistical modeling.
- **[numpy][numpy]**: For handling different types of arrays.
- **[pandas][pandas]**: For data manipulation and analysis of Excel data.
- **[openpyxl][openpyxl]**: For reading and writing Excel files.
- **[matplotlib][matplotlib]**: For generating scatter-plot chart.
- **[cryptography][cryptography]**: For generating the key, encrypting and decrypting.

<!-- Reference -->
[facelog-badge]: https://img.shields.io/badge/WebApp-Realtime_Facial_Recognition_Attendance_System-6850A8

[facial-recognition]: https://github.com/Mindkerchief/FaceLog/assets/130748576/606640e0-acb8-41d1-8a3e-0dcda1857c30
[face-capturing]: https://github.com/Mindkerchief/FaceLog/assets/130748576/f9ac633e-32eb-4fda-91ff-2f9b12edf2db
[chart]: https://github.com/Mindkerchief/FaceLog/assets/130748576/02271d0b-b6ed-4a82-8cea-33832139055b
[attendance-table]: https://github.com/Mindkerchief/FaceLog/assets/130748576/5e7db092-882c-4ed5-8fc4-65eda360a82b
[password-change]: https://github.com/Mindkerchief/FaceLog/assets/130748576/e0f79d1c-c84c-4268-b7f7-1c5c5ff7248c
[camera-selector]: https://github.com/Mindkerchief/FaceLog/assets/130748576/54b4918b-64fb-4ddb-832d-23098450c6df
[attendance-selector]: https://github.com/Mindkerchief/FaceLog/assets/130748576/debc2548-9ce1-40b0-bfdb-b77e3800c627

[release-page]: https://github.com/AHG-BSCS/FaceLog/releases
[lspu-spcc-bscs2a-ay-2023-2024]: https://web.facebook.com/photo.php?fbid=626282756192961&set=a.626292752858628&type=3
[css-gg]: https://css.gg/
[flask-cors]: https://flask-cors.readthedocs.io/en/latest/api.html
[waitress]: https://docs.pylonsproject.org/projects/waitress/en/stable/index.html
[pywebview]: https://pywebview.flowrl.com/guide/
[pyinstaller]: https://pyinstaller.org/en/stable/
[inno-setup]: https://jrsoftware.org/ishelp/
[facenet-pytorch]: https://github.com/timesler/facenet-pytorch
[opencv-python]: https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html
[scikit-learn]: https://scikit-learn.org/0.21/documentation.html
[numpy]: https://numpy.org/doc/stable/index.html
[pandas]: https://pandas.pydata.org/docs/
[openpyxl]: https://openpyxl.readthedocs.io/en/stable/
[matplotlib]: https://matplotlib.org/stable/users/index
[cryptography]: https://cryptography.io/en/latest/
