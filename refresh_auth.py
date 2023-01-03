import json

import yaml
from esipy import EsiApp
from esipy import EsiClient
from esipy import EsiSecurity


with open('data/secrets.yaml', 'r') as f:
    db = yaml.safe_load(f)

user_agent = {
    'User-Agent': 'trade-apex/py3.10'
}

app = EsiApp().get_latest_swagger

# replace the redirect_uri, client_id and secret_key values
# with the values you get from the STEP 1 !
security = EsiSecurity(
    redirect_uri=db['callback_url'],
    client_id=db['client_id'],
    secret_key=db['secret_key'],
    headers=user_agent,
)

# and the client object, replace the header user agent value with something reliable !
client = EsiClient(
    retry_requests=True,
    headers=user_agent,
    security=security
)

print(security.get_auth_uri(state='SomeRandomGeneratedState', scopes=db['scopes']))
code = input()
tokens = security.auth(code)
print(tokens)