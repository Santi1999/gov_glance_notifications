from response import RequestAPI
from notify import InitFirebaseApp, SendNotification


InitFirebaseApp()

topic_urls = []
data = RequestAPI().request_representative_vote(2)
print(data)
if data['results']:
    for item in data['results'][:1]:
        bill_title = item['title']
        vote_result = item['vote_result']
        vote_question = item['vote_question']
        roll_call_number = item['roll_call_number']
        for vote_record in item['votes'][:1]:
            role = vote_record['role']
            vote = vote_record['vote']
            bio_guide_id = vote_record['name_id']
            print(bio_guide_id)
            legislator_name = vote_record['legislator_name']
            name_unaccented = vote_record['name_unaccented']
            party_abbreviation = vote_record['party_abbreviation']
            state_abbreviation = vote_record['state_abbreviation']

            notification_message = f"""\n{legislator_name} ({state_abbreviation}) Voted '{vote}' for: \n'{bill_title}'"""
            print(notification_message)
            notification_title = f'{bio_guide_id}News'
            meta_data_notif = {
                'topic': 'legislative', 
                'table': 'all_member_votes', 
                'schema': 'united_states_of_america', 
                'item_id': str(roll_call_number)
                }
            SendNotification().notification_push(notifcation_title=notification_title, notification_message=notification_message, data= (meta_data_notif))
