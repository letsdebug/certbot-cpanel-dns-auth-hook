# certbot-cpanel-dns-auth-hook

This is an "auth hook" for Certbot that enables you to perform DNS-01 authentication.

It is suitable when you want to use Certbot to issue an e.g. wildcard certificate, but your domain's DNS is hosted in cPanel.

All it requires is that you have cPanel login credentials, and that your cPanel account has the ability to set TXT records.

## Usage

These instructions assume you are on a shell as the `root` user.

1. Download `cpanel-dns.py` somewhere onto your server. In this example, we will use `/etc/letsencrypt/cpanel-dns.py` as the location.
2. `chmod 0700 /etc/letsencrypt/cpanel-dns.py && chown root:root /etc/letsencrypt/cpanel-dns.py`
3. Modify the configuration section of `/etc/letsencrypt/cpanel-dns.py` :

```python
# Configure here
# URL to your cPanel login
CPANEL_URI = "https://cpanel.my-server.com:2083"
# Normal cPanel login credentials
CPANEL_AUTH = HTTPBasicAuth("username", "password")
# Adjust based on the performance of your DNS cluster.
CPANEL_BIND_DELAY = 15
```

4. Try issue a certificate now.

```bash
certbot certonly --manual \
--manual-auth-hook "/etc/letsencrypt/cpanel-dns.py create" \
--manual-cleanup-hook "/etc/letsencrypt/cpanel-dns.py delete" \
-d "*.my.domain.example.com" -d "*.example.com" \
--preferred-challenges dns-01
```
5. If this succeeds, so should automatic renewal.

## License

Copyright 2018 Alex Zorin

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.