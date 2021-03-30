import os
import boto3
import simplejson
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import simplejson

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
        
    response = {"statusCode": str(200), 
                    "valid": True,                 
                    "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": '*'
                            }
                }
                
    return response