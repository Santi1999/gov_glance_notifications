from notify import InitFirebaseApp, SendNotification
from response import RequestAPI

InitFirebaseApp()
topic_urls = []

data = RequestAPI().request_representative_sponsor(hour_int=2)
print(data)
for item in data['results'][:1]:
    if data['results']:
        for item in data['results']:
            bill_title = item['title']
            bill_id = item['id']
            if item['members']:
                for rep in item['members']:
                    print(rep)
                    party = rep['party']
                    state = rep['state']
                    chamber = rep['chamber']
                    member_name = rep['name'][0]['authority-fnf']
                    role = rep['role']
                    bio_guide_id = rep['bioGuideId']
                    notification_title = f'{bio_guide_id}News'

                    notification_message = f"""\n{member_name} ({state}) {role.title()}ed \n'{bill_title}'
                    """
                    meta_data_notif = {
                        'topic': 'legislative', 
                        'table': 'congressional_bills', 
                        'schema': 'united_states_of_america', 
                        'item_id': str(bill_id)}
                    print(notification_message)
                    SendNotification().notification_push(notifcation_title=notification_title, body=notification_message,data=meta_data_notif)
