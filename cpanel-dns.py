#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth
from urllib import urlencode
import sys
import os
import string
from time import sleep

# Configure here
# URL to your cPanel login
CPANEL_URI = "https://cpanel.example.com:2083"
# Normal cPanel login credentials
CPANEL_AUTH = HTTPBasicAuth("username", "password")
# Adjust based on the performance of your DNS cluster
CPANEL_BIND_DELAY = 15


def cpapi2_request(module, function, data=None):
    params = {
        "cpanel_jsonapi_user": CPANEL_AUTH.username,
        "cpanel_jsonapi_apiversion": "2",
        "cpanel_jsonapi_module": module,
        "cpanel_jsonapi_func": function
    }
    url = "{}/json-api/cpanel?{}".format(CPANEL_URI, urlencode(params))

    resp = requests.post(url, data=data, auth=CPANEL_AUTH)
    resp.raise_for_status()

    as_json = resp.json()
    return as_json


def normalize_fqdn(fqdn):
    fqdn = string.lower(fqdn)
    if fqdn[-1:] != '.':
        fqdn = fqdn + '.'
    return fqdn


def find_zone_for_name(domain):
    resp = cpapi2_request("ZoneEdit", "fetchzones")
    zones = resp['cpanelresult']['data'][0]['zones']

    # fetchzones doesn't have a trailing . on its zones
    if domain[-1:] == '.':
        domain = domain[:-1]

    domain_split = domain.split('.')
    found = None
    while len(domain_split) > 0:
        search = string.join(domain_split, ".")
        if search in zones:
            found = search
            break
        domain_split = domain_split[1:]

    return found


def list_records(zone):
    resp = cpapi2_request("ZoneEdit", "fetchzone_records", {'domain': zone})
    return resp['cpanelresult']['data']


def create_record(domain, txt_value):
    to_add = normalize_fqdn('_acme-challenge.{}'.format(domain))
    print("Creating {} TXT: {}".format(to_add, txt_value))
    zone = find_zone_for_name(domain)
    create_params = {'domain': zone, 'name': to_add, 'type': 'TXT',
                     'txtdata': txt_value}
    cpapi2_request("ZoneEdit", "add_zone_record", create_params)

    print("Will sleep {} seconds to wait for DNS cluster to reload".
          format(CPANEL_BIND_DELAY))
    sleep(CPANEL_BIND_DELAY)


def remove_record(domain, txt_value):
    to_remove = normalize_fqdn("_acme-challenge.{}".format(domain))
    zone = find_zone_for_name(to_remove)
    print "Removing {} TXT: {}".format(to_remove, txt_value)
    recs = list_records(zone)

    found = filter(
        lambda rec:
            'name' in rec and rec['name'] == to_remove and
            'type' in rec and rec['type'] == 'TXT' and
            rec['txtdata'] == txt_value,
        recs)

    if len(found) == 0:
        print("Could not find record to remove: {}/{}".
              format(to_remove, txt_value))
        return

    delete_params = {'domain': zone, 'line': found[0]['line']}
    cpapi2_request("ZoneEdit", "remove_zone_record", delete_params)


act = sys.argv[1]

if act == "create":
    create_record(os.environ["CERTBOT_DOMAIN"],
                  os.environ["CERTBOT_VALIDATION"])
elif act == "delete":
    remove_record(os.environ["CERTBOT_DOMAIN"],
                  os.environ["CERTBOT_VALIDATION"])
else:
    print("Unknown action: {}".format(act))
    exit(1)
