from response import RequestAPI
from notify import InitFirebaseApp, SendFcmMessage
import json

InitFirebaseApp()

# We are going to pull from the api all the values from the notifications table
def send_notification_(json_payload):
    if json_payload:
        # Here we are going to send the notification
        for item in json_payload:
                # We have two item in the hashmap. Topic and results.
            topic = item['topic']
            notification_items = item['results']

            # we need to clean results to enure that there are no empty values.
            cleaned = []
            for result in notification_items:
                # initialize a dict
                result_clean = {}
                # look through all key value pairs
                for key, value in result.items():
                    # If not none then we are storing the value as a string
                    if value is not None:  # Skip null values
                        result_clean[key] = str(value)  # Convert to string
                    else:
                        # all null/none values will be changed into a string
                        result_clean[key] = str(value)
                cleaned.append(result_clean)

            # assign new notification items to cleaner notification items
            notification_items = cleaned
            item['results'] = json.dumps(notification_items)
            # initialize the notification push topic
            push_topic = topic.lower()+"News"
            # Initialize the notification body
            print(len(notification_items))
            if len(notification_items) == 1:
                single_notification = notification_items[0]
                meta_data_notif = {
                            'topic': single_notification['topic'], 
                            'table': single_notification['table_source_name'], 
                            'schema': single_notification['country_schema'], 
                            'item_id': str(single_notification['table_id'])}
                
                notify = SendFcmMessage(
                    length_of_values=len(notification_items), 
                    notification_title=f'{topic.upper()} NEWS', 
                    body=notification_items[0]['title'],
                    image=notification_items[0]['image_url'] if notification_items[0]['image_url'] else 'None' or 'null', 
                    topic=push_topic, 
                    data=meta_data_notif,
                )
                # print(notify)
                (notify.send_notification())
            elif len(notification_items) > 1:
                notify = SendFcmMessage(
                    length_of_values=len(notification_items), 
                    notification_title=f'{topic.upper()} NEWS', 
                    body=notification_items[0]['title'],
                    image=notification_items[0]['image_url'] if notification_items[0]['image_url'] else 'None' or 'null', 
                    topic=push_topic, 
                    data=item,
                    ending_note=f' - Read More'
                )
                (notify.send_notification())
        return json_payload
    else:
        print('No data to send')

if __name__ == "__main__":
    '''Here we are going to perform operations on the database'''
# else:
    init_gov_glance_api = RequestAPI()
    data = init_gov_glance_api.request_notifications()
    print(data)
    # data = []

    # after the notification runs we need to store in a variable and then delete in the database
    data_to_delete = send_notification_(data)
    if data_to_delete:
        for topic in data_to_delete:
            print(data_to_delete)
            # iterate through the data to send notification
            if data_to_delete:
                init_gov_glance_api.delete_ports_bulk(topic['results'])
    else:
        print('No data to delete')