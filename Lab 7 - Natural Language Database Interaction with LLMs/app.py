from flask import Flask, render_template, request, session, redirect, url_for
import google.generativeai as genai
import mysql.connector
from configure import get_db_connection
import re

app = Flask(__name__)
app.secret_key = "secret_key"  

def get_sql_from_nlp(nlp_query):
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    schema_info = """
    Database: EMPLOYEE_NEW

    Tables:
    1. EMPLOYEE (EMPLOYEE_ID INT PRIMARY KEY, LNAME VARCHAR(20), FNAME VARCHAR(20), POSITIONID INT, 
       SUPERVISOR_ID INT, HIRE_DATE DATE, SALARY INT, COMISSION INT, EMPLOYEE_NAME VARCHAR(50))
    2. POSITION (POSITIONID INT PRIMARY KEY, POSDESC VARCHAR(50))
    3. DEPENDENT (DEPENDENTID INT PRIMARY KEY, EMPLOYEEID INT, DEPENDENT_NAME VARCHAR(50), 
       DEPDOB DATE, RELATION VARCHAR(20))

    Relationships:
    - EMPLOYEE.POSITIONID → POSITION.POSITIONID (Foreign Key)
    - EMPLOYEE.SUPERVISOR_ID → EMPLOYEE.EMPLOYEE_ID (Foreign Key)
    - DEPENDENT.EMPLOYEEID → EMPLOYEE.EMPLOYEE_ID (Foreign Key)
    """

    prompt = f"{schema_info}\n\nGenerate an SQL query for this request: {nlp_query}."
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_natural_language_response(query, sql_result, sql_query):
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    User Query: {query}
    SQL Query Used: {sql_query}
    SQL Result: {sql_result}
    
    Convert this into a natural language response that directly answers the user's question.
    Keep it concise, conversational, and easy to understand.
    """
    
    response = model.generate_content(prompt)
    return response.text.strip()

def execute_query(sql_query):
    clean_query = re.sub(r"``````|``|<|>|sql|`", "", sql_query).strip()
    clean_query = clean_query.replace("\n", " ").replace("\t", " ")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print("Cleaned Query:", clean_query)  
        cursor.execute(clean_query)
        if clean_query.strip().lower().startswith("select"):
            return cursor.fetchall()
        else:
            conn.commit()
            return "Query executed successfully"
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()
        conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        session.clear()
    if "chat_history" not in session:
        session["chat_history"] = []
    
    if request.method == "POST":
        query = request.form["query"]
        sql_query = get_sql_from_nlp(query)
        results = execute_query(sql_query)

        if results and not isinstance(results, str) and len(results) > 0:
            nl_response = generate_natural_language_response(query, results, sql_query)
        elif isinstance(results, str) and "Error" in results:
            nl_response = f"I encountered an error: {results}"
        else:
            nl_response = "I couldn't find any information related to your query."
        session["chat_history"].append({"query": query, "answer": nl_response})
        session.modified = True
        
    return render_template("index.html", chat_history=session["chat_history"])

if __name__ == "__main__":
    app.run(debug=True)