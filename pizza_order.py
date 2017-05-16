from __future__ import print_function
import boto3
import json
import datetime
from time import gmtime, strftime

print('Loading function')

def respond(err,customer_name, res=None):
    return {
       # 'res' : res
      #'Message' : 'Hi ' + customer_name + ' ,  please choose one of the selection:  1. Cheese, 2. Pepperoni, 3.Vegetable'

        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
 
        'headers': {
            'Content-Type': 'application/json',
            
        },
    }


def final_price_menu(choices,option,menu):
    menu_price=None
    if(choices =="size"):
        price = menu["price"]
        sizes = menu["size"]
        menu_price=None
        menu_price = "$"+price[int(option)-1]
    return menu_price


def possibilities(choices,menu):
        options = menu[choices]
        i =1;
        choice=""
        for option in options:
            option_iter = str(i)+")"+option
            choice = choice +" "+option_iter
            if i!=len(options):
                choice = choice +","
            i=i+1;
        return choice    


def get_result(order,menu):
    sequence=[]
    if "series" in menu:
        sequence = menu["series"];
    else:
        sequence = ["selection","size"]
    choices ="";
    choices ="finished"
    if "orders" in order:
        orderM = order ["orders"]
        for seq in sequence:
            if( seq not in   orderM):
                choices =seq;
                break;
    menu_price=""
    if(choices != "finished"):
            options = possibilities(choices,menu)
    else:
        price =menu["price"]
        sizes = menu["size"]
        if("orders" in order):
            orders = order["orders"]
            menu_price = orders["costs"]
    query=""
    customer_name =order["customer_name"]
    if(choices =="selection"):
        query="Hi "+customer_name+", please choose one of these selection:"
        response = query +" "+ options;
    elif(choices=="size"):
        query ="Which size do you want?"
        response = query +" "+ options;
    elif(choices == "finished"):
        response ="Your order costs "+menu_price+". We will email you when the order is ready. Thank you!"
    return response;

def store_name(order,menu,inputs):
    final_value = None
    sequence=[]
    if "series" in menu:
        sequence = menu["series"];
    else:
        sequence = ["selection","size"]
    choices ="";
    choices ="finished"
    if "orders" in order:
        orderM = order ["orders"]
        for seq in sequence:
            if(seq not in orderM):
                choices =seq;
                break;
    menu_price =final_price_menu(choices,inputs,menu)
    
    if(choices != "finished"):
        order_id =order["order_id"]
        options = menu[choices]
        toAdd = options[int(inputs)-1]
        final_value= {}
        final_value["TableName"] ="order"
        key ={}
        key["order_id"]=order_id
        final_value["Key"] =key
        attribute_names = {}
        attribute_names["#SV"]=choices
        update_expression = "set orders.#SV= :V"
        attribute_values = {}
        attribute_values[":V"]=toAdd

        if(menu_price is not None):
            update_expression =update_expression + ", orders.#Costs = :C"
            print("price **** "+menu_price)
            attribute_names["#Costs"]="costs"
            attribute_values[":C"]=menu_price
            
        final_value["ReturnValues"] ="NONE"
        final_value["UpdateExpression"]=update_expression
        final_value["ExpressionAttributeValues"]=attribute_values
        final_value["ExpressionAttributeNames"]=attribute_names

    return final_value;
    
def lambda_handler(event, context):
    operation =event["Operations"]
    operations = {
        'DELETE': lambda dynamo, x: dynamo.delete_item(**x),
        'GET': lambda dynamo, x: dynamo.get_item( **x),
        'POST': lambda dynamo, x: dynamo.put_item(**x),
        'PUT': lambda dynamo, x: dynamo.update_item(**x),
    }

    '''
    if operation =='GET':
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('order')
        return respond(None,operations[operation](table, event['payload']))['body']['Item']
    
    if operation == 'PUT':
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('order')
        return respond(None, operations[operation](table,event['payload']))
                
    elif operation in operations:
        #payload = event['payload'] if operation == 'GET' else json.loads(event['Item'])
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('order')
        #dynamo = boto3.resource('dynamodb').Table(payload['pizza'])
        return respond(None,event['payload']['Item']['customer_name'], operations[operation](table, event['payload']))
    else:
        return respond(ValueError('Unsupported method "{}"'.format(operation)))
    '''
    
    if (operation=="PUT"):
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table("order")
        payload =event.get("payload");
        order_id = event["payload"]["Item"]["order_id"]
        inputs = payload["Item"]["input"]
        orderPayload = {"Key":{ "order_id":order_id}}
        order_response = operations["GET"](table,orderPayload)
        order_result =  order_response['Item']

        menu_id =order_result["menu_id"]
        print ("Menu_ID " +menu_id)
        menuPayload = {"Key":{ "menu_id":menu_id}}
        menu = dynamodb.Table("pizza")
        pizza_response = operations["GET"](menu,menuPayload)
        print("Received event: " + json.dumps(pizza_response, indent=2))
        menu_result =  pizza_response['Item']
        store= store_name(order_result,menu_result,inputs)
        if store !=None:
            response = operations[operation](table,store)

    elif(operation=="POST"):
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table("order")
        payload = event.get('payload')
        item = payload["Item"]
        orders ={}
        order_time =strftime("%m-%d-%y@%H:%M:%S", gmtime())
        orders["order_time"] =order_time
        orders["costs"] ="0"
        item["orders"]= orders
        item["order_status"] ="Processing"
        response = operations[operation](table,event.get('payload'))

    if (operation == "GET" or operation == "DELETE") :
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table("order")
        payload =event.get("payload");
        response = operations[operation](table,event.get('payload'))
        meta_data = response['ResponseMetadata']

    '''
    if operation =='GET':
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('order')
        return respond(None,operations[operation](table, event['payload']))['body']['Item']
    '''

    if (operation == "PUT" or operation == "POST"):
        if operation == "PUT":
            dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
            table = dynamodb.Table("order")
            payload =event.get("payload");
    
            order_id = event["payload"]["Item"]["order_id"]
            inputs = payload["Item"]["input"]
        else:
            dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
            table = dynamodb.Table("order")
            payload =event.get("payload");
    
            item = payload["Item"]
            order_id = item["order_id"]
            inputs = "Initial"
        orderPayload = {"Key":{ "order_id":order_id}}
        order_response = operations["GET"](table,orderPayload)
        order_result =  order_response['Item']
        menu_id =order_result["menu_id"]
        menuPayload = {"Key":{ "menu_id":menu_id}}
        menu = dynamodb.Table("pizza")
        pizza_response = operations["GET"](menu,menuPayload)
        menu_result =  pizza_response['Item']
        response= get_result(order_result,menu_result)

    elif operation =='GET':
        response =  response['Item']
    else:
        if meta_data['statuscode'] ==200:
            response ="OK"
        else:
            response="ERROR"


    return response