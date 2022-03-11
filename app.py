#!/usr/bin/python3

import socket
import requests
import json
import re
import random
from datetime import date
from zipfile import ZipFile
# from multiprocessing import Pool

from os import getenv
from dotenv import load_dotenv
load_dotenv()


IPLOCATE_API_KEY = getenv("IPLOCATE_API_KEY")
USER_AGENT = getenv("USER_AGENT")

# download nord vpn server archive
session = requests.Session()
session.headers.update({'User-Agent': USER_AGENT})
ovpn_archive = session.get("https://downloads.nordcdn.com/configs/archives/servers/ovpn.zip")

# write archive to disk
with open('ovpn.zip', 'wb+') as nordvpn_archive:
  nordvpn_archive.write(ovpn_archive.content)

# import VPN's by name
with ZipFile('ovpn.zip', 'r') as nord_in:
    vpns = nord_in.namelist()

# regex TCP
regex = re.compile(r'^ovpn_udp')
ovpn_tcp = []
ovpn_tcp = [i for i in vpns if not regex.match(i)]

# regex for US
regex = re.compile(r'^ovpn_tcp/us[0-9]')
us_tcp = []
us_tcp = [i for i in ovpn_tcp if regex.match(i)]

# ratelimiting constraints
random.shuffle(us_tcp)
vpns = us_tcp[:960]

# parse data
vpn_data = []
for i in vpns:
    # get name
    vpn_name = re.sub(r'^ovpn_tcp/','', i)
    vpn_name = re.sub(r'.tcp.ovpn$','', vpn_name)

    # get ip
    vpn_ip = ''
    try:
        vpn_ip = socket.gethostbyname(vpn_name)
    except Exception as exc:
        pass

    # query api 
    params = (
        ('apiKey', IPLOCATE_API_KEY),
        ('ip', vpn_ip),
        ('fields', 'city,state_prov')
    )
    try:
        r = requests.get('https://api.ipgeolocation.io/ipgeo', params=params, timeout=4)
        if r.status_code != 200:
            city = str(r.status)
            state = str(r.status)
        else:
            r = r.json()
            city = r.get('city')
            state = r.get('state_prov')
    except Exception as exc:
        pass

    data = {
        "name": vpn_name,
        "ip": vpn_ip,
        "type": "TCP",
        "city": city,
        "state": state
    }

    vpn_data.append(data)


# close requests session
session.close()

# write to file
with open('vpns.json', 'w', encoding='utf-8') as vpns_out:
    json.dump(vpn_data, vpns_out, ensure_ascii=False, indent=2)

# write date to file
todays_date = date.today().isoformat()
with open('last_updated.txt', 'w') as date_open:
    date_open.write(todays_date)
