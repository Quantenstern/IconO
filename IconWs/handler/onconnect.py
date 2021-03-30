import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')
lf = boto3.client('lambda')

def _get_response(status_code, body):
    if not isinstance(body, str):
        body = json.dumps(body)
    return {"statusCode": status_code, "body": body}

def lambda_handler(event, context):
    """
    Esta funcion controla el handshake y la desconexion del ws. Luego registra en un dynamoDB las sesiones de los usuario, 
    todo con el fin de lograr luego una comunicacion 1 a 1. 
    -------
    _get_response : dict
        Contiene el formato de respuesta de api
    """       
    connectionID = event["requestContext"].get("connectionId")
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    if event["requestContext"]["eventType"] == "CONNECT":
        response = lf.invoke(FunctionName = os.environ['HANDLER_ARN'],
            InvocationType = "RequestResponse",
            Payload = json.dumps({"token": event['queryStringParameters']['token']}))
        data = json.loads(response['Payload'].read())["body"]
        if response['StatusCode'] == 200:
            table.put_item(Item={'tableId': connectionID, 'tableValue': data})
            return _get_response(200, "Connect successful")
        else:
            return _get_response(403, "Forbidden")
    elif event["requestContext"]["eventType"] == "DISCONNECT":
        #response = table.get_item(Key={'tableId':connectionID})
        #table.delete_item(Key={'tableId':response['Item']['tableValue']})
        table.delete_item(Key={'tableId':connectionID})
        return _get_response(200, "Disconnect successful.")
    else:
        return _get_response(500, "Unrecognized eventType.")