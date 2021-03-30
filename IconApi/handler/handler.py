import os
import boto3
import simplejson
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import simplejson

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    if 'plot' in event['queryStringParameters'] and 'temporality' in event['queryStringParameters']:
        
        table = dynamodb.Table(os.environ['TABLE_NAME'])
        supervisor_id = '123'
        
        turnos = table.get_item(Key={'operatorHandler': supervisor_id, 'value': 'turnos'})
        
        
        if event['queryStringParameters']['plot'] == 'False':
            response = []
            
            for turno in turnos['Item']['lista'].split(","):
                q_response = table.query(KeyConditionExpression=Key('operatorHandler').eq(supervisor_id + "_" +turno))['Items']
            
                t_response = {'cee': 0, 'pebbles': 0, 'velocidad': 0 , 'porcSolido': 0, 'agua' : 0, 'tph' : 0, 'potencia' : 0 , 'MUAgua' : 0, 'presion': 0 }
                
                for item in q_response:
                    for key in t_response.keys():
                        t_response[key] += float(item[key])/len(q_response)
                        
                t_response['turno'] = turno
                
                response.append(t_response)
            status = 200
            response = simplejson.dumps(response)   
        elif event['queryStringParameters']['plot'] == 'True':
            response = {}
            
            variables = {'pebbles':400, 'MUAgua': 40, 'cee': 40, 'velocidad': 9, 'porcSolido': 40,'agua': 2900,'tph':7500, 'potencia': 24000, 'presion': 6500}
            for turno in turnos['Item']['lista'].split(","):
                t_list = []
                q_response = table.query(KeyConditionExpression=Key('operatorHandler').eq(supervisor_id + "_" +turno))['Items']
                persona = {}
                for item in q_response:
                    if item['value'] == '0':
                        nombre ='Berni'
                        if nombre not in persona:
                            persona[nombre] = [0,0]
                    elif item['value'] == '1':
                        nombre ='Matias'
                        if nombre not in persona:
                            persona[nombre] = [0,0]
                    elif item['value'] == '2':
                        nombre ='Pablo'
                        if nombre not in persona:
                            persona[nombre] = [0,0]
                    elif item['value'] == '3':
                        nombre ='Vito'
                        if nombre not in persona:
                            persona[nombre] = [0,0]
                    elif item['value'] == '4':
                        nombre ='Cristobal'
                        if nombre not in persona:
                            persona[nombre] = [0,0]
                    persona[nombre][1] +=1
                    for key in variables.keys():
                        persona[nombre][0] += (100*float(item[key])/variables[key])/len(variables.keys())
        
                response= [{'name': a, 'value' :persona[a][0]/persona[a][1]} for a in persona]
            status = 200
            response = simplejson.dumps(response)
        
        else:
            status = 400
            response = 'Bad Request'
                
        
    else:  
        status = 400
        response = 'Bad Request'
        
    response = {"statusCode": str(status), 
                    "body": response,                 
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers",
                    "X-Requested-With": "*"}
                }
                
    return response