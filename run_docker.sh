#!/bin/bash
docker run \
    -p 5000:5000 \
    -p 5432:5432 \
    docker.shop.thebodgery.org/doorbot:main-latest
