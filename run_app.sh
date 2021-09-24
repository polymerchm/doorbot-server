#!/bin/bash
uwsgi \
    --http-socket :5000 \
    --module app:app
