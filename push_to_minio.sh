# User Minio Vars
URL=$1
USERNAME=$2
PASSWORD=$3
BUCKET=$4
FILE_PATH=$5
FILE_NAME=$(basename $FILE_PATH)
OBJ_PATH="/${BUCKET}/${FILE_NAME}"

# Static Vars
DATE=$(date -R --utc)
CONTENT_TYPE='application/octet-stream'
SIG_STRING="PUT\n\n${CONTENT_TYPE}\n${DATE}\n${OBJ_PATH}"
SIGNATURE=`echo -en ${SIG_STRING} | openssl sha1 -hmac ${PASSWORD} -binary | base64`

curl -X PUT -T "${FILE_PATH}" \
    -H "Host: $URL" \
    -H "Date: ${DATE}" \
    -H "Content-Type: ${CONTENT_TYPE}" \
    -H "Authorization: AWS ${USERNAME}:${SIGNATURE}" \
    http://$URL${OBJ_PATH}