#!/usr/bin/env python3

from flask import Flask, render_template
from flask_caching import Cache
import time
import secrets

random_secret_key = secrets.token_urlsafe(128)
app.config.update(
    DEBUG=False,
    SECRET_KEY=random_secret_key
)

cache = Cache(app, config={
    'CACHE_TYPE': 'simple'
})


@app.route('/')
@cache.cached()
def index():
    pass

