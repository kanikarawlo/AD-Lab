# app.py
from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
import yfinance as yf
from tensorflow.keras.models import load_model
from tensorflow.keras.losses import MeanSquaredError
import joblib
from datetime import datetime, timedelta

app = Flask(__name__)

# Dictionary to store model file names
STOCKS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']

# def load_models(stock):
#     """Load models for a specific stock"""
#     lstm_model = load_model(f'models/{stock}_lstm_model.h5')
#     linear_model = joblib.load(f'models/{stock}_linear_model.pkl')
#     scaler = joblib.load(f'models/{stock}_scaler.pkl')
#     return lstm_model, linear_model, scaler


def load_models(stock):
    """Load models for a specific stock"""
    lstm_model = load_model(f'models/{stock}_lstm_model.h5', custom_objects={'mse': MeanSquaredError()})
    linear_model = joblib.load(f'models/{stock}_linear_model.pkl')
    scaler = joblib.load(f'models/{stock}_scaler.pkl')
    return lstm_model, linear_model, scaler


def prepare_data(data, lookback=60):
    """Prepare data for prediction"""
    X = []
    for i in range(lookback, len(data)):
        X.append(data[i-lookback:i])
    return np.array(X)

@app.route('/')
def home():
    return render_template('index.html', stocks=STOCKS)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        stock = request.json['stock']
        model_type = request.json['model_type']
        
        # Fetch latest data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=100)  # Get 100 days of data
        df = yf.download(stock, start=start_date, end=end_date)
        
        if df.empty:
            return jsonify({'error': 'No data found for the given stock'})
        
        # Load models
        lstm_model, linear_model, scaler = load_models(stock)
        
        # Prepare data
        data = df['Close'].values.reshape(-1, 1)
        scaled_data = scaler.transform(data)
        X = prepare_data(scaled_data)
        
        predictions = {}
        historical = df['Close'].tolist()
        dates = [d.strftime('%Y-%m-%d') for d in df.index]
        
        if model_type in ['lstm', 'comparison']:
            lstm_pred = lstm_model.predict(X)
            lstm_pred = scaler.inverse_transform(lstm_pred)
            predictions['lstm'] = lstm_pred.reshape(-1).tolist()
            
        if model_type in ['linear', 'comparison']:
            X_2d = X.reshape(X.shape[0], -1)
            linear_pred = linear_model.predict(X_2d)
            linear_pred = scaler.inverse_transform(linear_pred.reshape(-1, 1))
            predictions['linear'] = linear_pred.reshape(-1).tolist()
        
        return jsonify({
            'dates': dates[60:],  # Remove first 60 days (lookback period)
            'historical': historical[60:],
            'predictions': predictions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)