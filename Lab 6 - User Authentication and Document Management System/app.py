import os
import random
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_NAME")
app.config['MYSQL_PORT'] = int(os.getenv("DB_PORT"))

mysql = MySQL(app)

def generate_marks_and_grade():
    marks = random.randint(0, 100)
    if marks >= 90:
        grade = "O"
    elif marks >= 80:
        grade = "E"
    elif marks >= 70:
        grade = "A"
    elif marks >= 60:
        grade = "B"
    elif marks >= 50: 
        grade = "C"
    elif marks >= 40:
        grade = "D" 
    else:
        grade = "F"
    return marks, grade

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        full_name = request.form["full_name"]
        email = request.form["email"]
        contact_no = request.form["contact_no"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))

        if not all([username, full_name, email, contact_no, password]):
            flash("All fields are required!", "danger")
            return redirect(url_for("register"))
            
        if "@" not in email or "." not in email:
            flash("Please enter a valid email address!", "danger")
            return redirect(url_for("register"))
            
        if len(password) < 8:
            flash("Password must be at least 8 characters long!", "danger")
            return redirect(url_for("register"))

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        
        try:
            cursor.execute("INSERT INTO users(username, full_name, email, contact_no, password) VALUES (%s, %s, %s, %s, %s)", 
                           (username, full_name, email, contact_no, hashed_password))
            mysql.connection.commit()
            print("step 1 done")
            
            cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
            user_id = cursor.fetchone()[0]  

            marks, grade = generate_marks_and_grade()
            
            cursor.execute("INSERT INTO grades (user_id, marks, grade) VALUES (%s, %s, %s)", (user_id, marks, grade))
            mysql.connection.commit()

            flash("Registration successful! Please log in.", "success")
        except Exception as e:
            print(f"Database error: {e}")
            flash("Registration failed.", "danger")
            mysql.connection.rollback()
        finally:
            cursor.close()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"].encode("utf-8")  

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("SELECT id, username, password FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            
            if user:
                stored_hashed_password = user[2].encode("utf-8")  
                
                if bcrypt.checkpw(password, stored_hashed_password):
                    session["user_id"] = user[0]
                    session["username"] = user[1]
                    return redirect(url_for("dashboard"))
                else:
                    flash("Invalid credentials, please try again.", "danger")
            else:
                flash("Invalid credentials, please try again.", "danger")
        except Exception as e:
            print(f"Login error: {e}")
            flash("An error occurred. Please try again later.", "danger")
        finally:
            cursor.close()

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id=%s", (session["user_id"],))
        user = cursor.fetchone()

        cursor.execute("SELECT marks, grade FROM grades WHERE user_id=%s", (session["user_id"],))
        grade_data = cursor.fetchone()
        
        return render_template("dashboard.html", user=user, grade_data=grade_data)
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash("An error occurred while loading your data.", "danger")
        return redirect(url_for("login"))
    finally:
        cursor.close()

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
