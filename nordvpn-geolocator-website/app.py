# -*- coding: utf-8 -*-

# imports
import datetime, json, requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# setup loggig
import logging
logger = logging.getLogger(__name__)

# initialize app
app = Flask(__name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

# inits
CORS(app)

# api
@app.route('/api/vpns')
def get_vpns():
    try:
        with open('static/vpns.json') as f:
            vpns = json.load(f)
        
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        return jsonify(vpns[offset:offset+limit])
    except Exception as e:
        logger.error(f"Error in get_vpns: {e}")
        return jsonify({"error": "Unable to fetch VPN data"}), 500

# routes
@app.route('/')
def index():
    git_link = "https://gitlab.com/evanesoteric/nordvpn-geolocator"

    with open('static/last_updated.txt') as file:
        last_updated = file.readline().strip()

    return render_template('index.html', git_link=git_link, last_updated=last_updated)

if __name__ == '__main__':
    app.run()
