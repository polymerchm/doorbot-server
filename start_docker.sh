#!/bin/bash
NAME=$1
CONTAINER_NAME=$2

# If there's an existing instance, stop it
RUN_COUNT=`docker ps | grep ${CONTAINER_NAME} | wc -l`
echo "${NAME} run count: ${RUN_COUNT}"

if [ ${RUN_COUNT} -gt 0 ]
then
    echo "Stopping ${NAME}"
    docker stop ${CONTAINER_NAME}
    docker container prune -f
fi

echo "Starting ${NAME}"
docker run \
    -p 5000:5000 \
    -d --name=${CONTAINER_NAME} \
    docker.shop.thebodgery.org/${NAME}
