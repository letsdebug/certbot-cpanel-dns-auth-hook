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
# If you don't have a trusted certificate on :2083
CPANEL_INSECURE_VERIFY = False
# Adjust based on the performance of your DNS cluster.
CPANEL_BIND_DELAY = 15
```

4. Try issue a certificate now.

```bash
certbot certonly --manual \
--manual-auth-hook "/etc/letsencrypt/cpanel-dns.py create" \
--manual-cleanup-hook "/etc/letsencrypt/cpanel-dns.py delete" \
-d "*.my.domain.example.com" -d "*.example.com"
```
5. If this succeeds, so should automatic renewal.