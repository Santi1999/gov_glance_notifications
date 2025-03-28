import requests
import os
import json
from dotenv import load_dotenv
load_dotenv()

class RequestAPI:

    def __init__(self):
        self.api_key = os.environ.get('GOV_GLANCE_API_KEY')
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def send_request(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            return json.loads(response.content)
        except:
            print(response.status_code)
            print(f'something went wrong with the {url}')
            return None
    
    def delete_request(self, url, data):
        try:
            response = requests.delete(url, headers=self.headers, data=(data))
            print(response.status_code)
            print(response.content)
            return 
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
    
    def request_notifications(self):
        url = f'https://api.govglance.org/posts/recent/notification'
        response = self.send_request(url)
        return response
    
    def delete_ports_bulk(self, post_data):
        delete_request = self.delete_request('https://api.govglance.org/posts/bulk', post_data)
        return delete_request
    
        """
        Send a DELETE request to delete posts in bulk
        
        Args:
            api_url (str): The API endpoint URL
            auth_token (str): Authorization token
            post_data (list): List of post objects to delete
            
        Returns:
            response: The API response
        """
        # url = "https://api.govglance.org/posts/bulk"
        
        # # Convert the post data to JSON
        # json_data = json.dumps(post_data)
        
        # # Send the DELETE request
        # response = requests.delete(url, headers=self.headers, data=json_data)

        # print(response)
        # return response