from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from llama_index.core import Document, VectorStoreIndex
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
import re

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env file")

genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
index = None

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,?!-]', '', text)
    return text.strip()

def scrape_website(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        content_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section'])

        text = ' '.join([clean_text(tag.get_text()) for tag in content_tags])
        documents = [Document(text=text)]
        return documents
        
    except requests.RequestException as e:
        raise ValueError(f"Error scraping website: {str(e)}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        global index
        embed_model = GeminiEmbedding(model_name="models/embedding-001")
        documents = scrape_website(url)
        
        index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
        
        return jsonify({'message': 'Website scraped and processed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/query', methods=['POST'])
def query():
    if not index:
        return jsonify({'error': 'Please scrape a website first'}), 400
    
    query_text = request.json.get('query')
    if not query_text:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        llm = Gemini(model_name="models/gemini-1.5-flash")
        query_engine = index.as_query_engine(llm=llm)
        response = query_engine.query(query_text)
        
        gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
        prompt = f"Based on this context: {response}, provide a clear and concise answer to: {query_text} based on the content of the scraped website. If the information is not in the context, respond with 'I'm sorry, but I cannot answer this question based on the content of the website.'"
        gemini_response = gemini_model.generate_content(prompt)
        
        return jsonify({'response': gemini_response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)