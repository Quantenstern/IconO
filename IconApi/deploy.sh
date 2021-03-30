#!/bin/bash

: "${STACK_NAME:=$1}"
: "${S3_BUCKET:=$2}"
: "${FILEPATH:=$3}"
: "${BRANCH:=$4}"



if [[ -z ${STACK_NAME} ]] ; then
  echo "No stackname was provided."
  echo "Use: sh deploy.sh <STACK_NAME> <S3_BUCKET>"
  exit 2
fi

if [[ -z ${S3_BUCKET} ]] ; then
  echo "No S3 bucket defined, using icon-cf-template"
  S3_BUCKET="icon-cf-template"
fi

if [ ${BRANCH} == main ];
then
	sed 's/Stage=STAGE_NAME/Stage=main/' ${FILEPATH}/parameters.properties.template > ${FILEPATH}/parameters.properties
elif [ ${BRANCH} == develop ];
then
	sed 's/Stage=STAGE_NAME/Stage=develop/' ${FILEPATH}/parameters.properties.template > ${FILEPATH}/parameters.properties
elif [ ${BRANCH} == staging ];
then
	sed 's/Stage=STAGE_NAME/Stage=stage/' ${FILEPATH}/parameters.properties.template > ${FILEPATH}/parameters.properties
fi

FILENAME=$(echo $RANDOM.${STACK_NAME} | openssl dgst -sha1 | sed 's/^.* //')
BUCKET="s3://$S3_BUCKET/$STACK_NAME/$FILENAME"

echo ${BUCKET}
echo ${FILENAME}
cat ${FILEPATH}/parameters.properties

sam build --template-file ${FILEPATH}/template.yaml && sam package --output-template-file ${FILEPATH}/packaged.yaml --s3-bucket ${S3_BUCKET} \
 && sam deploy --template-file ${FILEPATH}/packaged.yaml --capabilities CAPABILITY_NAMED_IAM --stack-name ${STACK_NAME} --parameter-overrides $(cat ${FILEPATH}/parameters.properties)
