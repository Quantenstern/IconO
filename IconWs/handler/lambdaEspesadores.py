# -*- coding: utf-8 -*-
"""
Created on Tue Jan 12 16:50:59 2021

author: AMS
"""

import json
import os
import sys
import logging
import struct
#sys.path.insert(0, F"{os.environ['LAMBDA_TASK_ROOT']}/{os.environ['DIR_NAME']}")
import boto3
import botocore
import simplejson 
from boto3.dynamodb.conditions import Key
sys.path.append("/opt")
import numpy as np
from io import BytesIO
from keras.models import load_model

dynamodb = boto3.resource('dynamodb')
lf = boto3.client('lambda')

def _get_response(status_code, body):
    return { 'statusCode': status_code, 'body': body }


def scale_data(data):
    max = np.array([6.00000000e+01, 6.00000000e+00, 8.53436398e+01, 1.00464465e+04,
       6.95910833e+03, 3.45833333e+01, 4.48950750e+01])
    min = np.array([4.20143084e+01, 3.28003142e-01, 2.51325000e+01, 1.09432696e+03,
       8.09741951e+02, 7.04840000e+00, 2.00100000e+01])
    data_scaled = (data-min)/(max-min)
    return data_scaled
def re_scale (data):
    max = np.array([6.00000000e+01, 6.00000000e+00, 8.53436398e+01, 1.00464465e+04,
       6.95910833e+03, 3.45833333e+01, 4.48950750e+01])
    min = np.array([4.20143084e+01, 3.28003142e-01, 2.51325000e+01, 1.09432696e+03,
       8.09741951e+02, 7.04840000e+00, 2.00100000e+01])
    data_re_scaled = data*(max-min)+min
    return data_re_scaled

def transform_data(data):
    data_numpy = np.array([data["solidodescarga"],data["nivelaguaalara"],data["torque"],
    data["alimentacionpulpa7"],data["descargapulpa7"], data["floculante"], data["porcSolidocajon"]])
    return data_numpy
    
def data_split(data):
    data_torque = data[2:]
    data_agua = data[[1,3,4,5,6]]
    data_solido = data[[0,3,4,5,6]]
    return data_torque,data_agua, data_solido
    
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
    #print("model"+ str(int(data["SPI"])))
    s3 = boto3.resource("s3")
    with BytesIO() as weights:
        s3.Bucket(os.environ['MODEL_BUCKET']).download_fileobj("models-espesadores/N_clara.h5", weights)
        weights.seek(0)
        model_Nagua = load_model(weights)
    with BytesIO() as weights:
        s3.Bucket(os.environ['MODEL_BUCKET']).download_fileobj("models-espesadores/descarga_solido", weights)
        weights.seek(0)
        model_Dsolido = load_model(weights)
    with BytesIO() as weights:
        s3.Bucket(os.environ['MODEL_BUCKET']).download_fileobj("models-espesadores/descarga_torque", weights)
        weights.seek(0)
        model_torque = load_model(weights)
    data = transform_data(data)
    data_scaled = scale_data(data)
    data_torque, data_agua, data_solido = data_split(data_scaled)
    torque = model_torque.predict(data_torque.reshape((1,1,-1)))
    agua = model_torque.predict(data_agua.reshape((1,1,-1)))
    solido = model_torque.predict(data_solido.reshape((1,1,-1)))
    salida = np.array([solido[0][0], agua[0][0], torque[0][0]], data_scaled[3],data_scaled[4],data_scaled[5],data_scaled[6])
    salida_rescaled = re_scale(salida)

    apigw_management = boto3.client('apigatewaymanagementapi', endpoint_url=F"https://{domain_name}/{stage}")
    try:
        apigw_management.post_to_connection(ConnectionId = actual_user_id, Data = simplejson.dumps({ 
            "alimentacionpulpa7": salida_rescaled[3], 
            "descargapulpa7": salida_rescaled[4],
            "porcSolidocajon": salida_rescaled[6],
            "floculante7": salida_rescaled[5],
            "torque": salida_rescaled[2],
            "nivelaguaalara": salida_rescaled[1],
            "solidodescarga": salida_rescaled[0]
            }))

        return _get_response(200, 'Ok')
    except botocore.exceptions.ClientError as e:
            return _get_response(500, 'Something Went Wrong')