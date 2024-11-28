from google_auth_oauthlib.flow import InstalledAppFlow

# Carregue o arquivo JSON com suas credenciais
flow = InstalledAppFlow.from_client_secrets_file(
    'credenciais.json.json',
    scopes=['https://www.googleapis.com/auth/adwords']
)

credentials = flow.run_local_server(port=0)
print("Refresh Token:", credentials.refresh_token)
