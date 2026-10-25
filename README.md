# 🌱 Crop Recommendation System

A web-based Crop Recommendation System designed to help users identify suitable crops based on soil nutrient levels and environmental conditions using Machine Learning.

The project combines a user-friendly web interface with a Python Flask backend and an SQLite database to manage user accounts, crop predictions, and prediction history.

## ✨ Features

- 🌾 **Crop Prediction:** Recommend crops using soil and weather parameters.
- 🧪 **Soil Analysis Inputs:** Nitrogen (N), Phosphorus (P), Potassium (K), temperature, humidity, soil pH, and rainfall.
- 👤 **User Authentication:** Registration, login, and logout.
- 🤖 **Machine Learning:** Supports integration of a trained crop classification model.
- 📊 **Top-3 Recommendations:** Display the three most likely crops if supported by the integrated model.
- 🗂️ **Prediction History:** Save and view previous predictions for each authenticated user.
- 🗄️ **Database Management:** SQLite database for users and prediction records.
- 📱 **Responsive Interface:** HTML, CSS, and JavaScript frontend.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web server and API |
| Scikit-learn | Machine Learning |
| Pandas & NumPy | Data processing |
| Joblib / Pickle | Saving and loading the trained model |
| SQLite | Database |
| HTML5 | Webpage structure |
| CSS3 | Styling and responsive layout |
| JavaScript | Frontend interactions |

## 📥 Input Parameters

The system accepts the following inputs:

| Parameter | Description |
|---|---|
| N | Nitrogen content in soil |
| P | Phosphorus content in soil |
| K | Potassium content in soil |
| Temperature | Environmental temperature |
| Humidity | Relative humidity |
| pH | Soil acidity or alkalinity |
| Rainfall | Rainfall amount |

These parameters are passed to the prediction model in the same feature order used during training.

## 📂 Project Structure

```text
Crop-Recommendation-System/
│
├── app.py
├── requirements.txt
├── init_db.py
├── crop_model.pkl
├── Crop_recommendation.csv
├── README.md
├── .gitignore
│
└── static/
    ├── index.html
    ├── login.html
    ├── predict.html
    ├── result.html
    ├── history.html
    ├── about.html
    ├── css/
    └── js/
```

*Note: The exact folder structure may differ depending on the files in your project. The model and dataset files are included only if they exist in your repository.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
```

Replace the URL with your actual GitHub repository URL.

### 2. Navigate to the project directory

```bash
cd YOUR-REPOSITORY
```

### 3. Create a virtual environment

**Windows PowerShell:**

```powershell
py -m venv .venv
```

Activate it using:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the virtual environment's Python executable directly instead.

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

Ensure `requirements.txt` contains all packages required by your application and trained model.

### 5. Initialize the database

If your project includes `init_db.py`, run:

```bash
python init_db.py
```

If your Flask application initializes the database automatically, this step may not be necessary.

### 6. Start the application

```bash
python app.py
```

### 7. Open the website

Visit the following address in your browser:

```text
http://127.0.0.1:5000
```

Keep the terminal running while you use the website.

## 🤖 Machine Learning Workflow

The intended ML workflow is:

1. Load the crop recommendation dataset.
2. Separate the input features and target crop labels.
3. Split the data into training and testing sets.
4. Train and evaluate the selected classification algorithms.
5. Save the fitted model and any required preprocessing.
6. Load the saved model in the Flask backend.
7. Pass validated user inputs to the model.
8. Display the predicted crop and, where supported, additional recommendations.

The model must use the same feature order and preprocessing during training and inference.

**Important:** Actual predictions require a successfully trained and integrated model artifact. If the application still uses demonstration logic, its outputs should not be treated as real ML predictions.

## 🗄️ Database

SQLite is used to store application data, including:

- User account details and password hashes.
- Prediction input parameters.
- Predicted crop labels.
- Prediction timestamps.
- User-specific prediction history.

Passwords should never be stored as plain text. Prediction history should be accessible only to the authenticated user who owns the records.

For production deployment, use persistent storage or a suitable managed database so that records are not lost when the application restarts or is redeployed.

## 🔐 Security Considerations

- Store passwords using secure password hashing.
- Keep secret keys and credentials in environment variables.
- Validate inputs on the server.
- Use parameterized SQL queries.
- Protect authenticated API endpoints.
- Do not commit secrets, virtual environments, or private user data to GitHub.
- Load only trusted model artifacts.
- Use HTTPS and secure session settings in production.

## 🚀 Deployment

The Flask application can be deployed to a Python-compatible hosting platform, such as Render.

Before deploying:

1. Confirm that the application runs locally.
2. Confirm that the trained model loads successfully.
3. Add all required dependencies to `requirements.txt`.
4. Configure the production secret key.
5. Configure persistent database storage.
6. Set the appropriate production start command for the hosting platform.
7. Test authentication, prediction, and prediction history after deployment.

## 🔮 Future Improvements

- Integrate and validate the final trained ML model.
- Add confidence scores when statistically supported by the model.
- Improve crop recommendations using location-specific agricultural data.
- Add soil analysis and crop information.
- Improve the mobile experience.
- Deploy the application with persistent production storage.

## 🎓 Project Purpose

This project demonstrates the integration of Machine Learning, web development, backend APIs, and database management in an agricultural application.

It is intended as an educational project and should not replace professional agricultural advice or laboratory soil testing.

## 👨‍💻 Author

**Arind Dhakad**

B.Tech — Computer Science and Engineering

Jaypee University of Engineering & Technology, Guna

## 📄 License

Choose an appropriate open-source license for your project. If you want others to reuse and modify your code, consider adding an MIT License in a separate `LICENSE` file.
