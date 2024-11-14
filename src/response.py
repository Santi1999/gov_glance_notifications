import requests
import os
import json
from dotenv import load_dotenv
load_dotenv()

class RequestAPI:

    def __init__(self):
        self.api_key = os.environ.get('GOV_GLANCE_API_KEY')
        print(self.api_key)
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def send_request(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            return json.loads(response.content)
        except:
            print(response.status_code)
            print(f'something went wrong with the {url}')
            return None
        
    def request_recent(self, table, schema, hour_int: int):
        url  = f'https://api.govglance.org/posts/recent/notify?table_name={table}&schema_name={schema}&hour_interval={hour_int}'
        
        response = self.send_request(url)
        return response
    
    def request_representative_sponsor(self, hour_int: int):
        url  = f'https://api.govglance.org/posts/recent/notify/representatives?hour_interval={hour_int}' 

        response = self.send_request(url)
        return response
    
    def request_representative_vote(self, hour_int: int):
        url  = f'https://api.govglance.org/posts/recent/notify/representatives_votes?hour_interval={hour_int}'
        response = self.send_request(url)
        return response