import json
import boto3
import requests
import json
from requests_aws4auth import AWS4Auth

esHost= 'https://search-restaurants-t47odz7xkfcfq6yayryjt6ylvi.us-east-1.es.amazonaws.com'
region = "us-east-1"
index = 'restaurant'

def getdatafromDBTable(table, key):
    print("getdatafromDBTable")
    response = table.get_item(Key={'Id':key}, TableName='yelp-restaurants')
    print("db response",response)
    name=response['Item']['Name']
    location=response['Item']['address']
    return '{} located at {}'.format(name,location)
    
def getRestaurantsfromES(cuisine):
    print("getRestaurantsfromES")
    service = "es"
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    # awsauth2 = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    url = esHost + '/' + index + '/_search'
    query = {"query": {"match": {"cuisine": cuisine }}}
    headers = { "Content-Type": "application/json" }
    res = requests.post(url, auth=awsauth, headers=headers, data=json.dumps(query))
    print("res1",res)
    res = res.text
    res = json.loads(res)
    print("res",res)
    res = res['hits']['hits']
    return res
    
def sendSESMail(message,email):
    print("sendSESMail")
    ses_client = boto3.client('ses', region_name=region)
    response = ses_client.send_email(
        Source='td2478@nyu.edu',
        Destination={
            'ToAddresses': [email]
        },
        ReplyToAddresses=['td2478@nyu.edu'],
        Message={
            'Subject': {
                'Data': 'NYU Dining Recommendation Bot',
                'Charset': 'utf-8'
            },
            'Body': {
                'Text': {
                    'Data': message,
                    'Charset': 'utf-8'
                },
                'Html': {
                    'Data': message,
                    'Charset': 'utf-8'
                }
            }
        }
    )
    
def lambda_handler(event, context):
    print("event",event)
    sqsUrl = "https://sqs.us-east-1.amazonaws.com/593489176864/DiningConceirge"
    sqs_client = boto3.client("sqs", region_name=region)
    response = sqs_client.receive_message(
        QueueUrl=sqsUrl,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=10,
        AttributeNames=['All'],
        MessageAttributeNames=[
        'All'
        ]
    )
    
    print("sqs response",response)
    numOfMessages = len(response.get('Messages', []))
    
    if numOfMessages > 0:
        for message in response.get("Messages", []):
            messageAttributes = json.loads(message['Body'])
            # read parameters from event
            print("testing",messageAttributes)
            name = messageAttributes['Name']
            cuisine = messageAttributes['Cuisine']
            date = messageAttributes['Date']
            time = messageAttributes['Time']
            location = messageAttributes['Location']
            numPeople = messageAttributes['NumberOfPeople']
            # phone = messageAttributes['PhoneNumber']['StringValue']
            email = messageAttributes['Email']
        
            # call elastisearch to find random restaurants with given cuisine type
            elastisearchResults = getRestaurantsfromES(cuisine)
            print("elastisearchResults",elastisearchResults)
            # call dynamodb to elicit extra info for each restaurant identified
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('yelp-restaurants')
            restaurantDetails=[]
            count = 0
            for i in elastisearchResults:
                count += 1
                rid = i['_id']
                rest=getdatafromDBTable(table, rid)
                rest = str(count) + ". " + rest
                restaurantDetails.append(rest)
                # limiting number of suggestions to 5
                if count == 5:
                    break
            
            # prepare response for user
            responseToUser = "Hello {}! Here are my {} restaurant suggestions for {} people, for {} at {}:<br> ".format(str(name),str(cuisine),str(numPeople),str(date),str(time)) 
            responseToUser += ",<br> ".join(restaurantDetails)
            responseToUser += ".<br> Enjoy your meal!"
        
            sendSESMail(responseToUser,email)
            sqs_client.delete_message(
                QueueUrl= sqsUrl,
                ReceiptHandle=message['ReceiptHandle']
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Notification sent successfully')
        }
    else:
         return {
            'statusCode': 200,
            'body': json.dumps('No messages present in SQS queue')
        }
