from flask import Flask, request, render_template, redirect, url_for, flash, session
import numpy as np
import pickle
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from feature import FeatureExtraction  # Assuming FeatureExtraction is defined in feature.py

# Load the model
file = open("model.pkl", "rb")
gbc = pickle.load(file)
file.close()

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for session management and flash messages

# User data file path
USER_DATA_FILE = 'users.json'

# Email configurations
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_FROM = 'daminmain@gmail.com'
EMAIL_PASSWORD = 'kpqtxqskedcykwjz'
EMAIL_TO = 'bashith67@gmail.com'

# Helper function to load user data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Helper function to save user data
def save_user_data(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Function to send email
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, EMAIL_TO, text)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", str(e))

@app.route("/", methods=["GET", "POST"])
def landing():
    return render_template("landing.html")

@app.route("/index", methods=["GET", "POST"])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        url = request.form["url"]
        obj = FeatureExtraction(url)
        x = np.array(obj.getFeaturesList()).reshape(1, 30) 

        y_pred = gbc.predict(x)[0]
        y_pro_phishing = gbc.predict_proba(x)[0, 0]
        y_pro_non_phishing = gbc.predict_proba(x)[0, 1]

        if y_pred == 1:
            pred = "It is {0:.2f}% unsafe to go ".format(y_pro_phishing * 100)
        else:
            pred = "It is {0:.2f}% safe to go ".format(y_pro_non_phishing * 100)

        # Send email with prediction result
        subject = "Phishing Prediction Result for {}".format(url)
        body = "Prediction: {}\nURL: {}".format(pred, url)
        send_email(subject, body)

        return render_template('index.html', xx=round(y_pro_non_phishing, 2), url=url)

    return render_template("index.html", xx=-1)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        users = load_user_data()
        if username in users:
            flash("Username already exists!")
            return redirect(url_for('register'))

        users[username] = {'email': email, 'password': password}
        save_user_data(users)
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        users = load_user_data()
        if username not in users or users[username]['password'] != password:
            flash("Invalid username or password!")
            return redirect(url_for('login'))

        session['username'] = username
        flash("Login successful!")
        return redirect(url_for('index'))  # Redirect to index page after successful login

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, port=7000)
