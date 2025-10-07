import requests
from notify import InitFirebaseApp, SendNotification
from response import RequestAPI
from firebase_admin import messaging
import json

InitFirebaseApp()

with open('notify_tables/test.json', 'r') as outfile:
    json_data =  json.load(outfile)

print(json_data)
topic_urls = []
for item in json_data:
    # data =  RequestAPI().request_recent(item['table'], item['schema'], 2)
    print(item)
    if item == None:
        continue
    if item.get('results'):
        list_items_ = item['results']
        recent = list_items_[0]
        recent_value_id = recent['id']
        message_body = SendNotification(item['topic']).message(list_items=list_items_, recent_value=recent['description'])
        print(message_body)

        meta_data_notif = {
            'topic': item['topic'], 
            'table': recent['table_source_name'], 
            'schema': recent['country_schema'], 
            'item_id': str(recent_value_id)}
        
        SendNotification(item['topic']).notification_push('test', 'Test Notification', str(message_body), data= (meta_data_notif))
