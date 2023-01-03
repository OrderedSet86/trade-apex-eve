import yaml
from esipy import EsiApp
from esipy import EsiClient
from esipy import EsiSecurity


class Connection:
    def __init__(self):
        self.app = None
        self.client = None

    def startup(self):
        with open('data/secrets.yaml', 'r') as f:
            db = yaml.safe_load(f)

        user_agent = {
            'User-Agent': 'trade-apex/py3.10'
        }

        self.app = EsiApp().get_latest_swagger

        security = EsiSecurity(
            redirect_uri=db['callback_url'],
            client_id=db['client_id'],
            secret_key=db['secret_key'],
            headers=user_agent,
        )

        self.client = EsiClient(
            retry_requests=True,
            headers=user_agent,
            security=security
        )

        security.update_token({
            'access_token': '',  # leave this empty
            'expires_in': -1,  # seconds until expiry, so we force refresh anyway
            'refresh_token': db['refresh_token'],
        })
        security.refresh()
    
    def qq(self, route, **kwargs):
        if self.client is None:
            self.startup()
        return self.client.request(self.app.op[route](**kwargs)).data


if __name__ == '__main__':
    conn = Connection()