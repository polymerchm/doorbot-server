#!/bin/bash
uwsgi \
    --http-socket :5002 \
    --module app:app
