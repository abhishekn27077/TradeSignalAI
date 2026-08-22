import requests
import json

def test_backtest():
    print('Testing Backtest Engine...')
    try:
        response = requests.post('http://localhost:8000/api/v1/backtest/run', json={
            'symbol': 'EURUSD',
            'timeframe': 'D1',
            'strategy': 'OTCConfluenceStrategy',
            'capital': 10000.0
        })
        if response.status_code == 200:
            data = response.json()
            print("Response:", json.dumps(data, indent=2))
        else:
            print('Request failed with status:', response.status_code)
            print(response.text)
    except Exception as e:
        print('Error:', e)

test_backtest()
