# Dining-Concierge
A serverless, microservice driven, Dining Concierge chatbot that sends you restaurant suggestions given a set of preferences that you provide the chatbot with through conversation.

Frontend  url - http://frontend2-dining-concierge.s3-website-us-east-1.amazonaws.com/

Commands used:

For bulk load in elastic search:
curl -u master_username:master_password -X PUT "<ES_URL>/restaurant?pretty"

curl -XPUT -u 'master_username:master_password' '<ES_URL>/restaurant/_bulk?pretty' --data-binary @Restaurants_bulk_load_data.json -H 'Content-Type: application/json'
