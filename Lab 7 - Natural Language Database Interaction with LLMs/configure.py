import mysql.connector
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="gemini_api_key")

# MySQL Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Password",
        database="EMPLOYEE_NEW"
    )
