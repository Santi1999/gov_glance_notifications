import requests
from notify import InitFirebaseApp, SendNotification
from response import RequestAPI
from firebase_admin import messaging
import json

InitFirebaseApp()

with open('notify_tables/items.json', 'r') as outfile:
    json_data =  json.load(outfile)

print(json_data)
topic_urls = []
for item in json_data:
    data =  RequestAPI().request_recent(item['table'], item['schema'], 2)
    print(data)
    if data == None:
        continue
    if data['results']:
        print(item['table'])
        recent = data['results'][0]
        recent_value_id = recent['id']
        message_body = SendNotification().message(list_items=data['results'], recent_value=recent)
        print(message_body)

        meta_data_notif = {
            'topic': item['topic'], 
            'table': item['table'], 
            'schema': item['schema'], 
            'item_id': str(recent_value_id)}
        
        SendNotification().notification_push('test', 'Test Notification', str(message_body), data= (meta_data_notif))
