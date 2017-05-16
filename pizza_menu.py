from __future__ import print_function

import boto3
import json

print('Loading function')

def respond(err, res=None):
    return {
      
        'statusCode': '400' if err else '200',
        'body': err.message if err else (res),
 
        'headers': {
            'Content-Type': 'application/json',
        }
    
}

def get_result(err, res=None):
    return "200 OK"

def update(x):
    body={}
    key={}
    expression_name={}
    expression_value = {}
    item = x.get('Key')
    key["menu_id"]=item['menu_id']
    UpdateQuery='SET '
    body["Key"] = key
    if("store_name" in item):
        expression_name["#store"]="store_name"
        expression_value[":Store"]=item.get("store_name")
        UpdateQuery  = UpdateQuery + "#store=:Store"
        UpdateQuery = UpdateQuery + ","
    if("selection" in item):
        expression_name["#selection"]="selection"
        expression_value[":Selection"]=item.get("selection")
        UpdateQuery  = UpdateQuery + "#selection=:Selection"
        UpdateQuery = UpdateQuery + ","
    if("size" in item):
        expression_name["#size"]="size"
        expression_value[":Size"]=item.get("size")
        UpdateQuery  = UpdateQuery + "#size = :Size"
        UpdateQuery = UpdateQuery + ","
    if("price" in item):
        expression_name["#price"]="price"
        expression_value[":Price"]=item.get("price")
        UpdateQuery  = UpdateQuery + "#price = :Price"
        UpdateQuery = UpdateQuery + ","
    if("store_hours" in item):
        expression_name["#store_hours"]="store_hours"
        expression_value[":Store_hours"]=item.get("store_hours")
        UpdateQuery  = UpdateQuery + "#store_hours = :Store_hours"
        UpdateQuery = UpdateQuery + ","
        
    body["ExpressionAttributeNames"]=expression_name
    body["ExpressionAttributeValues"]= expression_value
    body["TableName"]="pizza"
    UpdateQuery=UpdateQuery[:-1]
    #UpdateExpression = 'SET #store = :Store, #selection = :Selection, #size = :Size, #price = :Price, #store_hours = :Store_hours'
    body["UpdateExpression"]=UpdateQuery
    #print(UpdateQuery)
    print(body['UpdateExpression'])
    return body

    
def lambda_handler(event, context):
    '''Demonstrates a simple HTTP endpoint using API Gateway. You have full
    access to the request and response payload, including headers and
    status code.

    To scan a DynamoDB table, make a GET request with the TableName as a
    query string parameter. To put, update, or delete an item, make a POST,
    PUT, or DELETE request respectively, passing in the payload to the
    DynamoDB API as a JSON body.
    '''
    #print("Received event: " + json.dumps(event, indent=2))

    operations = {
        'DELETE': lambda dynamo, x: dynamo.delete_item(**x),
        'GET': lambda dynamo, x: dynamo.get_item(**x),
        'POST': lambda dynamo, x: dynamo.put_item(**x),
        'PUT': lambda dynamo, x: dynamo.update_item(**update(x)),
    }

    operation = event['Operations']
    #print(event['payload']['Item']['menu_id'])
    if operation =='GET':
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('pizza')
        return respond(None,operations[operation](table, event['payload']))['body']['Item']
    
    if operation == 'PUT':
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('pizza')
        response=get_result(None, operations[operation](table,event['payload']))
        return response
                
    elif operation in operations:
        #payload = event['payload'] if operation == 'GET' else json.loads(event['Item'])
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('pizza')
        #dynamo = boto3.resource('dynamodb').Table(payload['pizza'])
        response=get_result(None, operations[operation](table, event['payload']))
        return response
    else:
        return respond(ValueError('Unsupported method "{}"'.format(operation)))
