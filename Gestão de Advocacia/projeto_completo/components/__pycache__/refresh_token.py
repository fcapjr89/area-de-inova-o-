from google_auth_oauthlib.flow import InstalledAppFlow

def generate_refresh_token():
    client_id = "259180084504-6171jcoc0a862rhe5u0traemc318tvr9.apps.googleusercontent.com"
    client_secret = "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"
    scopes = ["https://www.googleapis.com/auth/adwords"]  # Escopo para o Google Ads API
    
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        },
        scopes=scopes
    )
    
    credentials = flow.run_local_server(port=8080)
    print("Refresh Token:", credentials.refresh_token)

if __name__ == "__main__":
    generate_refresh_token()
