# certbot-cpanel-dns-auth-hook

This is an "auth hook" for Certbot that enables you to perform DNS-01 authentication.

It is suitable when you want to use Certbot to issue an e.g. wildcard certificate, but your domain's DNS is hosted in cPanel.

All it requires is that you have cPanel login credentials, and that your cPanel account has the ability to set TXT records.

The script can optionally install the issued certificate on a selected domain via the cPanel API.

## Usage

These instructions assume you are on a shell as the `root` user.

The hook has one dependency, the  `requests` python package. If you installed Certbot from your distro packages, you will probably need to
install something like `python-requests`/`python2-requests`/`python3-requests`.

1. Download `cpanel-dns.py` somewhere onto your server. In this example, we will use `/etc/letsencrypt/cpanel-dns.py` as the location.
2. `chmod 0700 /etc/letsencrypt/cpanel-dns.py && chown root:root /etc/letsencrypt/cpanel-dns.py`
3. Modify the configuration section of `/etc/letsencrypt/cpanel-dns.py` :

```python
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

# Optional for installation: Domain to install the received certificate for
CPANEL_TARGET_DOMAIN = os.environ.get("CPANEL_DNS_INSTALL_TARGET_DOMAIN", "example.com")

# Optional for installation: Certbot configuration directory (if not the default)
CERTBOT_CONFIG_DIR = os.environ.get("CPANEL_DNS_INSTALL_CERTBOT_CONFIG_DIR", "/etc/letsencrypt")
```

4. Try to issue a certificate now.

```bash
certbot certonly --manual \
--manual-auth-hook "/etc/letsencrypt/cpanel-dns.py create" \
--manual-cleanup-hook "/etc/letsencrypt/cpanel-dns.py delete" \
-d "*.my.domain.example.com" -d "*.example.com" \
--preferred-challenges dns-01
```

If this succeeds, so should automatic renewal.

5. Optionally, install the certificate:

```bash
/etc/letsencrypt/cpanel-dns.py install
```


## Testing (for developers)
There is a basic tox integration test in place. To run it, pass the details of your cPanel server using environment variables when calling `tox`, e.g.:

    CPANEL_DNS_CPANEL_DELAY=1 CERTBOT_DOMAIN=example.com CPANEL_DNS_CPANEL_URI=https://cpanel.example.com:2083 CPANEL_DNS_CPANEL_AUTH_USERNAME=exampleuser CPANEL_DNS_CPANEL_AUTH_PASSWORD=examplepassword tox

## License

Copyright 2018 Alex Zorin

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.