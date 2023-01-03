# Run Procedure
1. Follow guide at https://kyria.github.io/EsiPy/examples/sso_login_esipy/ on getting set up with SSO/API keys
2. Create a data/secrets.yaml file with the following structure:
- client_id: 
- secret_key:
- callback_url: 
- scopes: [...]
- refresh_token: 
3. Refresh token can be obtained by running refresh_auth.py, then copying the refresh token from the URL
4. Run get_orders.py
5. Run find_arbitrage.py

![sample output](media/output.png)