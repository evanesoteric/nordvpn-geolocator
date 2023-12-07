#!/usr/bin/python3

import requests
import json
import re
import random
from datetime import date
from zipfile import ZipFile
import multiprocessing
import socket
import logging

# Environment variable management
from os import getenv
from dotenv import load_dotenv
load_dotenv()

# Set up basic logging to STDOUT
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Environment variables
IPGEOLOCATE_API_KEY = getenv("IPGEOLOCATE_API_KEY")
DEV_USER_AGENT = getenv("DEV_USER_AGENT")

def download_file():
    """Download and save the VPN configuration archive."""
    try:
        with requests.Session() as session:
            session.headers.update({'User-Agent': DEV_USER_AGENT})
            ovpn_archive = session.get("https://downloads.nordcdn.com/configs/archives/servers/ovpn.zip")
            ovpn_archive.raise_for_status()
            with open('ovpn.zip', 'wb') as nordvpn_archive:
                nordvpn_archive.write(ovpn_archive.content)
        logging.info("VPN configuration archive downloaded successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download VPN configuration archive: {e}")
        raise

def process_vpn(vpn, error_dict):
    """Process individual VPN entries from the archive."""
    data = {"name": "", "ip": "", "type": "TCP", "city": "", "state": ""}
    try:
        # Extract the VPN name from the file name
        vpn_name = re.sub(r'^ovpn_tcp/', '', vpn)
        vpn_name = re.sub(r'.tcp.ovpn$', '', vpn_name)
        data["name"] = vpn_name

        # Resolve the IP address of the VPN
        vpn_ip = socket.gethostbyname(vpn_name)
        data["ip"] = vpn_ip

        # Make a request to the geolocation API
        with requests.Session() as session:
            params = (('apiKey', IPGEOLOCATE_API_KEY), ('ip', vpn_ip), ('fields', 'city,state_prov'))
            response = session.get('https://api.ipgeolocation.io/ipgeo', params=params)
            response.raise_for_status()  # Will raise an HTTPError if the response was an HTTP error
            r = response.json()
            data["city"] = r.get('city')
            data["state"] = r.get('state_prov')

        logging.info(f"Processed VPN: {vpn_name}")

    except socket.gaierror:
        # Log a warning if DNS lookup fails
        logging.warning(f"DNS lookup failed for VPN: {vpn_name}")

    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors, especially the 429 Too Many Requests
        if e.response.status_code == 429:
            error_dict['http_429_errors'] += 1
            logging.error(f"429 Too Many Requests error for VPN: {vpn_name}. Total occurrences: {error_dict['http_429_errors']}")
            if error_dict['http_429_errors'] > 3:
                raise Exception("Exceeded rate limit errors")
        else:
            logging.error(f"API request failed for VPN: {vpn_name}, Error: {e}")

    except Exception as e:
        # Log any other unexpected errors
        logging.error(f"Unexpected error occurred while processing VPN: {vpn_name}, Error: {e}")

    return data

def main():
    """Main function to process VPN configurations."""
    download_file()

    manager = multiprocessing.Manager()
    error_dict = manager.dict(http_429_errors=0)

    try:
        with ZipFile('ovpn.zip', 'r') as nord_in:
            vpns = nord_in.namelist()
    except FileNotFoundError:
        logging.error("VPN configuration archive not found. Exiting.")
        return
    except Exception as e:
        logging.error(f"Error opening VPN configuration archive: {e}")
        return

    regex_tcp = re.compile(r'^ovpn_udp')
    ovpn_tcp = [i for i in vpns if not regex_tcp.match(i)]
    regex_us = re.compile(r'^ovpn_tcp/us[0-9]')
    us_tcp = [i for i in ovpn_tcp if regex_us.match(i)]
    random.shuffle(us_tcp)
    vpns = us_tcp[:960]

    try:
        with multiprocessing.Pool(processes=3) as pool:
            vpn_data = pool.starmap(process_vpn, [(vpn, error_dict) for vpn in vpns])

        if error_dict['http_429_errors'] > 3:
            logging.error("Exceeded maximum allowed rate limit errors. Exiting.")
            return

    except Exception as e:
        logging.error(f"Script stopped due to error: {e}")
        return

    with open('vpns.json', 'w', encoding='utf-8') as F:
        json.dump(vpn_data, F, ensure_ascii=False, indent=2)

    todays_date = date.today().isoformat()
    with open('last_updated.txt', 'w') as F:
        F.write(todays_date)

    logging.info(f"Total VPNs processed: {len(vpn_data)}")

if __name__ == '__main__':
    main()
