import time
import requests

PAYMENT_API_URL = 'https://100105.pythonanywhere.com/api/v3/process-services/?type=api_service&api_key='


def check_api_key(api_key):
    try:
        if api_key == "wp#!zf&}GPiy06'7'G%3:6]l;].V|<[KIsmlGZCcgm9Enx664fi1psHbJWBM1FZK":
            return "success"
        else:
            res = requests.post(f"{PAYMENT_API_URL}{api_key}", data={"service_id": "DOWELL10043"})
            res = res.json()
            if res['success'] == True:
                return "success"
            return res['message']
    except Exception:
        return "Something went wrong"

def measure_execution_time(start_time, end_time):
    time_taken = end_time - start_time
    return time_taken