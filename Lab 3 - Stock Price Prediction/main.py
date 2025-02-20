import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import joblib
from datetime import datetime, timedelta

def fetch_data(symbol='AAPL', start_date='2015-01-01', end_date=None):
    """
    Fetch historical stock data using yfinance
    """
    if end_date is None:
        end_date = datetime.now()

    df = yf.download(symbol, start=start_date, end=end_date)
    return df

def prepare_data(data, lookback=60):
    """
    Prepare data for time series prediction
    """
    X, y = [], []
    for i in range(lookback, len(data)):
        X.append(data[i-lookback:i])
        y.append(data[i])
    return np.array(X), np.array(y)

def create_lstm_model(lookback):
    """
    Create and compile LSTM model
    """
    model = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=(lookback, 1)),
        Dropout(0.2),
        LSTM(units=50, return_sequences=True),
        Dropout(0.2),
        LSTM(units=50),
        Dropout(0.2),
        Dense(units=1)
    ])

    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    return model

def train_models(symbol='AAPL', lookback=60):
    """
    Train both Linear Regression and LSTM models
    """
    df = fetch_data(symbol)

    # Use closing prices
    data = df['Close'].values.reshape(-1, 1)

    # Scale the data
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)

    # Prepare data for training
    X, y = prepare_data(scaled_data, lookback)

    # Split into train and test sets
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    # Reshape data for Linear Regression
    X_train_2d = X_train.reshape(X_train.shape[0], -1)
    X_test_2d = X_test.reshape(X_test.shape[0], -1)

    # Train Linear Regression model
    lr_model = LinearRegression()
    lr_model.fit(X_train_2d, y_train)

    # Train LSTM model
    lstm_model = create_lstm_model(lookback)
    lstm_model.fit(
        X_train,
        y_train,
        epochs=50,
        batch_size=32,
        validation_split=0.1,
        verbose=1
    )

    # Make predictions
    lr_pred = lr_model.predict(X_test_2d)
    lstm_pred = lstm_model.predict(X_test)

    # Inverse transform predictions
    lr_pred = scaler.inverse_transform(lr_pred.reshape(-1, 1))
    lstm_pred = scaler.inverse_transform(lstm_pred)
    y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

    # Calculate metrics
    lr_mse = mean_squared_error(y_test_actual, lr_pred)
    lr_r2 = r2_score(y_test_actual, lr_pred)

    lstm_mse = mean_squared_error(y_test_actual, lstm_pred)
    lstm_r2 = r2_score(y_test_actual, lstm_pred)

    print("\nLinear Regression Metrics:")
    print(f"MSE: {lr_mse:.2f}")
    print(f"R2 Score: {lr_r2:.2f}")

    print("\nLSTM Metrics:")
    print(f"MSE: {lstm_mse:.2f}")
    print(f"R2 Score: {lstm_r2:.2f}")

    # Save models and scaler
    lstm_model.save('models/lstm_model.h5')
    joblib.dump(lr_model, 'models/linear_model.pkl')
    joblib.dump(scaler, 'models/scaler.pkl')

    return {
        'lr_metrics': {'mse': lr_mse, 'r2': lr_r2},
        'lstm_metrics': {'mse': lstm_mse, 'r2': lstm_r2},
        'test_predictions': {
            'actual': y_test_actual,
            'lr_pred': lr_pred,
            'lstm_pred': lstm_pred
        }
    }

def plot_results(results):
    """
    Plot actual vs predicted values
    """
    import matplotlib.pyplot as plt

    actual = results['test_predictions']['actual']
    lr_pred = results['test_predictions']['lr_pred']
    lstm_pred = results['test_predictions']['lstm_pred']

    plt.figure(figsize=(12, 6))
    plt.plot(actual, label='Actual')
    plt.plot(lr_pred, label='Linear Regression')
    plt.plot(lstm_pred, label='LSTM')
    plt.title('Stock Price Prediction')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    # Train models for Apple stock
    results = train_models('AAPL')

    # Plot results
    plot_results(results)