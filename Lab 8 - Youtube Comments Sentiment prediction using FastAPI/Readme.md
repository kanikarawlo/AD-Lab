# Sentiment Prediction API using FastAPI  
This project is a Sentiment Prediction API that analyzes YouTube comments and classifies them as positive, negative, or neutral using Natural Language Processing (NLP). It is implemented using FastAPI and integrates with the YouTube Data API.  

## 1. Setup and Installation: 
Run the following command to install the necessary Python packages:  
```pip install fastapi uvicorn nltk google-api-python-client requests pydantic```  
## 2. Get YouTube API Key:  
a. Create a Google Cloud Account if you don't have one.  
b. Go to Google Cloud Console → Click on Create a Project.  
c. Enable YouTube Data API v3 for your project.  
d. Generate an API Key:  
Go to Credentials -> Click Create Credentials -> API Key.  
Copy the generated API Key for later use.
## 3. Steps to Run the API using Terminal  
3.1 Download the script or clone the repository using: 
```git clone "https://github.com/kanikarawlo/AD-Lab.git"```  
3.2 Navigate to the project directory.  
3.3 Create a .env file and replace YOUTUBE_API_KEY in the script with your generated API Key.  
3.4 Start the API server:  
```uvicorn filename:app --reload```
3.5 Once the server is running, access the interactive API documentation at:  
```http://127.0.0.1:8000/docs```


