#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth, AuthBase
import sys
import os
from time import sleep

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

# Configure here or provide credentials via environment variables
# URL to your cPanel login
CPANEL_URI = os.environ.get("CPANEL_DNS_CPANEL_URI", "https://cpanel.example.com:2083")

# cPanel login credentials
CPANEL_AUTH_USERNAME = os.environ.get("CPANEL_DNS_CPANEL_AUTH_USERNAME", "username")
CPANEL_AUTH_PASSWORD = os.environ.get("CPANEL_DNS_CPANEL_AUTH_PASSWORD", "password")
# If CPANEL_AUTH_PASSWORD is a cPanel API token, set this to "token".
CPANEL_AUTH_METHOD = os.environ.get("CPANEL_DNS_CPANEL_AUTH_METHOD", "password")

# Adjust based on the performance of your DNS cluster
CPANEL_BIND_DELAY = int(os.environ.get("CPANEL_DNS_CPANEL_DELAY", "15"))

# Optional for installation: Certbot configuration directory (if not the default)
CERTBOT_CONFIG_DIR = os.environ.get("CPANEL_DNS_INSTALL_CERTBOT_CONFIG_DIR", "/etc/letsencrypt")


class APITokenAuth(AuthBase):

    def __init__(self, username, api_token):
        self.username = username
        self.api_token = api_token

    def __call__(self, r):
        r.headers["Authorization"] = "cpanel {}:{}".format(self.username, self.api_token)
        return r


def cpanel_post(url, data):
    auth_cls = APITokenAuth if CPANEL_AUTH_METHOD == "token" else HTTPBasicAuth
    resp = requests.post(url, data=data, auth=auth_cls(CPANEL_AUTH_USERNAME, CPANEL_AUTH_PASSWORD))
    resp.raise_for_status()
    return resp.json()


def cpapi2_request(module, function, data=None):
    params = {
        "cpanel_jsonapi_user": CPANEL_AUTH_USERNAME,
        "cpanel_jsonapi_apiversion": "2",
        "cpanel_jsonapi_module": module,
        "cpanel_jsonapi_func": function,
    }
    url = "{}/json-api/cpanel?{}".format(CPANEL_URI, urlencode(params))

    return cpanel_post(url, data)


def cpuapi_request(module, function, data=None):
    url = f"{CPANEL_URI}/execute/{module}/{function}"
    return cpanel_post(url, data)


def normalize_fqdn(fqdn):
    fqdn = fqdn.lower()
    if fqdn[-1:] != ".":
        fqdn = fqdn + "."
    return fqdn


def find_zone_for_name(domain):
    resp = cpapi2_request("ZoneEdit", "fetchzones")
    zones = resp["cpanelresult"]["data"][0]["zones"]

    # fetchzones doesn't have a trailing . on its zones
    if domain[-1:] == ".":
        domain = domain[:-1]

    domain_split = domain.split(".")
    found = None
    while len(domain_split) > 0:
        search = ".".join(domain_split)
        if search in zones:
            found = search
            break
        domain_split = domain_split[1:]

    return found


def list_records(zone):
    resp = cpapi2_request("ZoneEdit", "fetchzone_records", {"domain": zone})
    return resp["cpanelresult"]["data"]


def create_record(domain, txt_value):
    to_add = normalize_fqdn("_acme-challenge.{}".format(domain))
    print("Creating {} TXT: {}".format(to_add, txt_value))
    zone = find_zone_for_name(domain)
    create_params = {
        "domain": zone,
        "name": to_add,
        "type": "TXT",
        "txtdata": txt_value,
    }
    cpapi2_request("ZoneEdit", "add_zone_record", create_params)

    print(
        "Will sleep {} seconds to wait for DNS cluster to reload".format(
            CPANEL_BIND_DELAY
        )
    )
    sleep(CPANEL_BIND_DELAY)


def remove_record(domain, txt_value):
    to_remove = normalize_fqdn("_acme-challenge.{}".format(domain))
    zone = find_zone_for_name(to_remove)
    print("Removing {} TXT: {}".format(to_remove, txt_value))
    recs = list_records(zone)

    found = list(
        filter(
            lambda rec: "name" in rec
            and rec["name"] == to_remove
            and "type" in rec
            and rec["type"] == "TXT"
            and rec["txtdata"] == txt_value,
            recs,
        )
    )

    if len(found) == 0:
        print("Could not find record to remove: {}/{}".format(to_remove, txt_value))
        return

    delete_params = {"domain": zone, "line": found[0]["line"]}
    cpapi2_request("ZoneEdit", "remove_zone_record", delete_params)


def get_certbot_file_contents(domain, filename):
    path = os.path.join(CERTBOT_CONFIG_DIR, f"live/{domain}/{filename}")
    with open(path) as f:
        return f.read()


def install_certificate(domain):
    data = {
        "domain": domain,
        "cert": get_certbot_file_contents(domain, "cert.pem"),
        "key": get_certbot_file_contents(domain, "privkey.pem"),
        "cabundle": get_certbot_file_contents(domain, "chain.pem"),
    }

    req = cpuapi_request("SSL", "install_ssl", data)
    print(req["messages"])


def clean_renewed_domains(domains):
    # We need to grab a clean, unified list of domains
    # to install SSL on - CPanel usually manages multiple
    # subdomains like [mail/ftp/www/*].example.com and
    # example.com under a single "example.com" entity.

    # Certbot gets us a list of domains for which all
    # certs were renewed, so let's automate the most
    # common case cleanly from environment variables.
    # For certs manually provisioned outside of these,
    # users need to specify target CPanel domains on
    # the hook's command line.
    clean_domains = set()

    # By default they're space-delimited:
    for domain in domains.split(' '):
        domain = domain.strip()

        if domain.startswith('www.'):
            domain = domain[4:]

        if domain.startswith('*.'):
            domain = domain[2:]

        if len(domain) < 3:  # Whitespace entry?
            continue

        clean_domains.add(domain)

    return list(clean_domains)


if __name__ == "__main__":
    act = sys.argv[1]

    if act == "create":
        create_record(os.environ["CERTBOT_DOMAIN"], os.environ["CERTBOT_VALIDATION"])
    elif act == "delete":
        remove_record(os.environ["CERTBOT_DOMAIN"], os.environ["CERTBOT_VALIDATION"])
    elif act == "install":
        if len(sys.argv) >= 3:
            # Don't clean domains here:
            domains = sys.argv[2:]
        elif "RENEWED_DOMAINS" in os.environ:
            domains = clean_renewed_domains(os.environ["RENEWED_DOMAINS"])
        else:
            exit("Deployment usage: cpanel-dns.py install <DOMAIN>")

        for domain in domains:
            print(f"Installing certificates for CPanel domain: {domain}")
            install_certificate(domain)
    else:
        print("Unknown action: {}".format(act))
        exit(1)
