import json
import os
import sys
import logging
import struct
from decimal import Decimal
sys.path.insert(0, F"{os.environ['LAMBDA_TASK_ROOT']}/{os.environ['DIR_NAME']}")
import boto3
import botocore
from boto3.dynamodb.conditions import Key
sys.path.append("/opt")
import numpy as np
import simplejson
from io import BytesIO

dynamodb = boto3.resource('dynamodb')
lf = boto3.client('lambda')

def _get_response(status_code, body):
    return { 'statusCode': status_code, 'body': body }

def lambda_handler(event, context):
    """
    Funcion que maneja el envio de un mensaje 1 a 1. 
    """

    connections = dynamodb.Table(os.environ['TABLE_NAME'])

    """Variables"""
    data = json.loads(json.loads(event['body'])['data'])

    """Data to make the connection"""

    domain_name = event.get('requestContext',{}).get('domainName')
    actual_user_id = event.get('requestContext',{}).get('connectionId')
    stage = event.get('requestContext',{}).get('stage')

    if (domain_name and stage) is None:
        return _get_response(400, 'Bad Request')



    """----------"""
    print("model"+ str(int(data["SPI"])))
    s3 = boto3.resource("s3")
    with BytesIO() as weights:
        s3.Bucket(os.environ['MODEL_BUCKET']).download_fileobj("mod"+ str(int(data["SPI"])) + ".npy", weights)
        weights.seek(0)
        model = np.load(weights, allow_pickle=True)

    index_po, values_po, index_pre, values_pre, index_pebles, values_pebles = model

    potencia = values_po[0]
    presion = values_pre[0]
    pebles = values_pebles[0]

    #data = {'velocidad': 2, 'porcSolido':3, 'finos':4, 'gruesos':5, 'medios':6,'agua':7, 'tph':8}
    for i_po,v_po in zip(index_po[1:], values_po[1:]):
        temp_i = i_po.split("_")
        potencia += v_po*data[temp_i[0]]**int(temp_i[-1]) if len(temp_i)>1 else v_po*data[temp_i[0]]

    for i_pre, v_pre in zip(index_pre[1:], values_pre[1:]):
        temp_p = i_pre.split("_")
        presion += v_pre*data[temp_p[0]]**int(temp_p[-1]) if len(temp_p)>1 else v_pre*data[temp_p[0]] 

    for i_peb, v_peb in zip(index_pebles[1:], values_pebles[1:]):
        temp_pe = i_peb.split("_")
        pebles += v_peb*data[temp_pe[0]]**int(temp_pe[-1]) if len(temp_pe)>1 else v_peb*data[temp_pe[0]] 


    porcSolido = Decimal(100*(data["tph"]/(data["tph"]+data["agua"])))


    apigw_management = boto3.client('apigatewaymanagementapi', endpoint_url=F"https://{domain_name}/{stage}")
    try:
        apigw_management.post_to_connection(ConnectionId = actual_user_id, Data = simplejson.dumps({ 
            "potencia": Decimal(potencia), 
            "presion": Decimal(presion),
            "aguaAnterior": Decimal(data["agua"]),
            "porcSolidoAnterior": Decimal(data["porcSolido"]),
            "velocidad": Decimal(data["velocidad"]),
            "porcSolido": porcSolido,
            "finos": Decimal(100-data["gruesos"]-data["medios"]),
            "gruesos": Decimal(data["gruesos"]),
            "medios": Decimal(data["medios"]),
            "agua": Decimal((100*data["tph"]/porcSolido - data["tph"])) if porcSolido != data["porcSolidoAnterior"] else data["agua"],
            "tph": Decimal(data["tph"]),
            "pebbles": Decimal(pebles),
            "porcPotencia": Decimal((potencia/24735)*100),
            "porcPresion": Decimal((presion/7103.11)*100),
            "porcPebbles": Decimal((pebles/1467)*100),
            "MUAgua": Decimal(data["agua"]/data["tph"]),
            "EEspecifica": Decimal(potencia/data["tph"]),
            "SPI": Decimal(data["SPI"])}))
        return _get_response(200, 'Ok')
    except botocore.exceptions.ClientError as e:
            return _get_response(500, 'Something Went Wrong')
