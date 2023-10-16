import json
import random
import decimal 
import boto3
import logging
import datetime
from datetime import date,timedelta
import dateutil.parser
import time
import os
import math
import re


queue_url = 'https://sqs.us-east-1.amazonaws.com/593489176864/DiningConceirge'
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

def checkEmail(email):
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']
    
def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None:
            return slots[slotName]
        #else:
            #return intent_request['currentIntent']['slotDetails'][slotName]['originalValue']
    else:
        return None    

def get_session_attributes(intent_request):
    if 'sessionAttributes' in intent_request:
        return intent_request['sessionAttributes']
    return {}

def close(intent_request, session_attributes, fulfillment_state, message):
    print("close")
    return {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close',
                'fulfillmentState': fulfillment_state,
                'message': message,
            }
    }

def sendmsgtosqs(intent_request):
    
    print("Sending the data to sqs queue")
    sqs = boto3.client('sqs')
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody = json.dumps(intent_request['currentIntent']['slots'])
    )

def buildValidationMessage(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot
        }
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def delegate(session_attributes,slots):
    print("delegate")
    return {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Delegate',
                'slots': slots
            }
    }

def validateSlots(location,cuisineType,date,time,numPeople,name,email):
    print("validateSlots")
    locs = ['nyc','manhattan','new york','brooklyn','new jersey']
    if location is not None and location.lower() not in locs:
        return buildValidationMessage(False,
                                       'location',
                                       'We are not supporting services in {}. Please enter neighborhood in Manhattan'.format(location))
    
    cuisines=['indian','mexican','japanese','french','cafes','italian']
    if cuisineType is not None and cuisineType.lower() not in cuisines:
        return buildValidationMessage(False,
                                       'cuisine',
                                       'We are not supporting services for {} food. Please choose among Indian, Mexican, Japanese, French, Cafes, and Italian'.format(cuisineType))
    
    if date is not None:
        if not isValidDate(date):
            return buildValidationMessage(False, 'date', 'Invalid date! Sample input format: Today')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return buildValidationMessage(False, 'date', 'The day has already passed ;)  Please enter a valid date.')
    if numPeople is not None:
        if int(numPeople) <=0 or int(numPeople)>10:
            return buildValidationMessage(False,'peopleCount',"We can only accommodate 0-10 people! Please enter again.")
    if time is not None:
        if len(time) != 5:
            return buildValidationMessage(False, 'time', "Invalid time! Enter in proper format(eg 02:00 PM)")
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() == datetime.date.today():
            if (int(time[0:2])<=(datetime.datetime.now().hour)):
                return buildValidationMessage(False, 'time', "Invalid time! Enter Time after the present time")
        for i in range(len(time)):
            if i == 2:
                if time[i] != ":":
                    return buildValidationMessage(False, 'time', "Invalid time! Enter in proper format(eg 02:00 PM)")
            else:
                if not time[i].isalnum():
                    return buildValidationMessage(False, 'time', "Invalid time!Enter in proper format(eg 02:00 PM)")

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            return buildValidationMessage(False, 'time', "Invalid time!")
    
    if email is not None:
        if not checkEmail(email):
            return buildValidationMessage(False, 'phoneNumber', "Please enter a valid Email address!")
            
            
    return buildValidationMessage(True, None, None)

def isValidDate(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False
        
def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan') 

def elicitSlot(session_attributes, intent_name, slots, slot_to_elicit, message):
    print("elicitSlot")
    return {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit,
                'intentName' : intent_name,
                'slots':slots,
                'message':[message],
                },
            'recentIntentSummaryView':{
                    'name': intent_name,
                    'slots': slots
                }
            
            
    }
    
def DiningSuggestionsIntent(intent_request):
    print("inside DiningSuggestionsIntent")
    session_attributes = get_session_attributes(intent_request)
    location = get_slot(intent_request,"Location")
    cuisineType = get_slot(intent_request, 'Cuisine')
    date = get_slot(intent_request, 'Date')
    time = get_slot(intent_request, 'Time')
    numPeople = get_slot(intent_request, 'NumberOfPeople')
    name = get_slot(intent_request, 'Name')
    email = get_slot(intent_request, 'Email')
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        slots = get_slots(intent_request)
        validationResultForSlots = validateSlots(location,cuisineType,date,time,numPeople,name,email)
        
        if not validationResultForSlots['isValid']:
                slots[validationResultForSlots['violatedSlot']] = None
                print(validationResultForSlots['violatedSlot'])
                return elicitSlot(session_attributes,
                                        intent_request['interpretations'][0]['intent']['name'],
                                        slots,
                                        validationResultForSlots['violatedSlot'],
                                        validationResultForSlots['message'])
    
        return delegate(session_attributes, get_slots(intent_request))
   
    sendmsgtosqs(intent_request)
    return close(intent_request, 
                    session_attributes,
                    'Fulfilled',
                    {'contentType': 'PlainText',
                    'content': 'Thank you! You will receive recommendations to your Email: {} in some time. Have a good day'.format(email)}) 

def GreetingIntent(intent_request):
    print("inside GreetingIntent")
    session_attributes = get_session_attributes(intent_request)
    message =  {
            'contentType': 'PlainText',
            'content': "Hi! How Can I Help you?"
        }
    return elicitIntent(session_attributes, message)   
    
def ThankYouIntent(intent_request):
    print("inside ThankYouInten")
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    return close(
        intent_request,
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Happy to help. Have a great day!'
        }
    )
    
def elicitIntent(session_attributes, message):
    print("elicitIntent")
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitIntent',
            }
        },
        'messages': message
    }
    
def dispatch(intent_request):
    print("dispatch")
    response = None
    print(intent_request)
    intent_name = intent_request['currentIntent']['name']
    if intent_name == 'DiningSuggestionsIntent':
        return DiningSuggestionsIntent(intent_request)
    elif intent_name == 'ThankYouIntent':
        return ThankYouIntent(intent_request)
    elif intent_name == 'GreetingIntent':
        return GreetingIntent(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')

def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    response = dispatch(event)
    print("response",response)
    return response