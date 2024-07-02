import requests
import pandas as pd
import ta
import hmac
import hashlib
import base64
import time
from config import api_key, api_secret, api_passphrase

# key API
api_key = api_key
api_secret = api_secret
passphrase = api_passphrase

# Base URL for requests
base_url = 'https://api.bitget.com'

def get_indicator() -> dict:

    # Function for creating a signature
    def create_signature(api_secret, timestamp, method, request_path, query_string, body):
        message = f'{timestamp}{method}{request_path}{query_string}{body}'
        hmac_key = hmac.new(api_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        signature = base64.b64encode(hmac_key).decode()
        return signature

    # Function for getting a list of trading pairs
    def get_symbols():
        timestamp = str(int(time.time() * 1000))
        method = 'GET'
        request_path = '/api/spot/v1/public/products'
        query_string = ''
        body = ''
        
        signature = create_signature(api_secret, timestamp, method, request_path, query_string, body)
        
        headers = {
            'ACCESS-KEY': api_key,
            'ACCESS-SIGN': signature,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(base_url + request_path, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.text}")
        
        data = response.json()
        return data

    # Function to get historical candle data
    def get_candles(symbol, period, limit):
        timestamp = str(int(time.time() * 1000))
        method = 'GET'
        request_path = f'/api/spot/v1/market/candles'
        query_string = f'?symbol={symbol}&period={period}&limit={limit}'
        body = ''
        
        signature = create_signature(api_secret, timestamp, method, request_path, query_string, body)
        
        headers = {
            'ACCESS-KEY': api_key,
            'ACCESS-SIGN': signature,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(base_url + request_path + query_string, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.text}")
        
        data = response.json()
        return data

    # Function for calculating RSI and CCI
    def calculate_indicators(df):
        # RSI calculation on 5 minute candles
        df['RSI_5m'] = ta.momentum.RSIIndicator(df['close'], window=5).rsi()
        
        # RSI calculation on 30 minute candles
        df['RSI_30m'] = ta.momentum.RSIIndicator(df['close'], window=30).rsi()
        
        # Calculation of CCI on 60 minute candles
        df['CCI_60m'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close'], window=60).cci()
        
        return df

    # Obtaining data on candles for the found symbol
    try:
        # Getting a list of trading pairs
        symbols_response = get_symbols()

        # Find the desired symbol
        symbol = None
        for product in symbols_response['data']:
            if 'XAU' in product['symbol'] and 'USDT' in product['symbol']:
                symbol = product['symbol']
                break

        if not symbol:
            raise ValueError("Symbol not found.")

        # Getting candles for each period
        period_5m = '5min'
        period_30m = '30min'
        period_60m = '1h'

        limit = 100

        candles_5m = get_candles(symbol, period_5m, limit)
        candles_30m = get_candles(symbol, period_30m, limit)
        candles_60m = get_candles(symbol, period_60m, limit)

        # Converting data to DataFrame (if the data format is correct)
        if candles_5m.get('data') and candles_30m.get('data') and candles_60m.get('data'):
            df_5m = pd.DataFrame(candles_5m['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_5m['timestamp'] = pd.to_datetime(df_5m['timestamp'], unit='ms')
            df_5m.set_index('timestamp', inplace=True)

            df_30m = pd.DataFrame(candles_30m['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_30m['timestamp'] = pd.to_datetime(df_30m['timestamp'], unit='ms')
            df_30m.set_index('timestamp', inplace=True)

            df_60m = pd.DataFrame(candles_60m['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_60m['timestamp'] = pd.to_datetime(df_60m['timestamp'], unit='ms')
            df_60m.set_index('timestamp', inplace=True)

            # Converting prices to numbers
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            df_5m[numeric_columns] = df_5m[numeric_columns].astype(float)
            df_30m[numeric_columns] = df_30m[numeric_columns].astype(float)
            df_60m[numeric_columns] = df_60m[numeric_columns].astype(float)

            # Calculation of indicators
            df_5m = calculate_indicators(df_5m)
            df_30m = calculate_indicators(df_30m)
            df_60m = calculate_indicators(df_60m)

            # Displays the latest RSI and CCI values
            rsi_5m = df_5m['RSI_5m'].iloc[-1]
            rsi_30m = df_30m['RSI_30m'].iloc[-1]
            cci_60m = df_60m['CCI_60m'].iloc[-1]

            def convert_to_int(value, name):
                try:
                    return int(value)
                except ValueError:
                    print(f"Ошибка преобразования {name}: {value}")
                    return None

            rsi_5m_int = convert_to_int(rsi_5m, 'RSI_5m')
            rsi_30m_int = convert_to_int(rsi_30m, 'RSI_30m')
            cci_60m_int = convert_to_int(cci_60m, 'CCI_60m')

            data = {
                'Symbol': symbol,
                'RSI_5m': rsi_5m_int,
                'RSI_30m': rsi_30m_int,
                'CCI_60m': cci_60m_int
            }

        else:
            print("Ошибка при получении данных. Пожалуйста, проверьте формат ответа API.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    
    return data