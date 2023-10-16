import json
import boto3
import datetime


def lambda_handler(event, context):
    print("lf0 event",event)
    requestmsg = ''
    body =  json.loads(event['body'])
    for msg in body['messages']:
        requestmsg = requestmsg + msg['unstructured']['text']
    
    print("request message",requestmsg)
    client = boto3.client('lex-runtime')
    bot_response = client.post_text(botName='DiningConceirge_chatbot', botAlias='ALIAS_ONE', userId='test', inputText= requestmsg)
    print("bot response",bot_response)

    return {
        'headers':{
                    "Access-Control-Allow-Origin" : "*"
        },
        'body':json.dumps({'messages':[
            {
            "type":'unstructured',
            "unstructured":{
                    'id': "1",
                    'text': bot_response['message'],
                    'timestamp': str(datetime.datetime.now().timestamp())
                }
            }
        ]}
        )
        }
