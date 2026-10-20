from flask import Flask
from common.jad_support import install
from services.incidents.routes import bp


def create_app(overrides=None):
    return install(Flask(__name__), bp, 'Incidents', overrides)


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5003)
