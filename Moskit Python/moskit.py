import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import numpy as np
from datetime import datetime
import time

# Função para formatar a data no formato DD/MM/AAAA
def format_date(date_str):
    if not date_str or date_str == 'Sem data':
        return 'Sem data'
    
    try:
        date_obj = datetime.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')
        return date_obj.strftime('%d/%m/%Y')
    except ValueError:
        return 'Data inválida'

# Função para buscar fases (stages)
def fetch_moskit_stages(api_key):
    url = 'https://api.moskitcrm.com/v2/stages'
    headers = {'apikey': api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar fases: {e}")
        return []

# Função para buscar negócios (deals) com controle de paginação e retry em caso de erro 429 (Too Many Requests)
def fetch_moskit_deals(api_key, start=0):
    url = 'https://api.moskitcrm.com/v2/deals'
    headers = {'apikey': api_key}
    params = {'quantity': 50, 'start': start}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Monitorar os headers de limite de requisição
        remaining_requests_second = response.headers.get('X-RateLimit-Remaining-Second', 6)
        remaining_requests_minute = response.headers.get('X-RateLimit-Remaining-Minute', 240)
        print(f"Requisições restantes neste segundo: {remaining_requests_second}")
        print(f"Requisições restantes neste minuto: {remaining_requests_minute}")
        
        return data if isinstance(data, list) else data.get('deals', [])
    except requests.exceptions.RequestException as e:
        if response.status_code == 429:  # Código 429 significa "Too Many Requests"
            print("Limite de requisições atingido. Aguardando para re-tentar...")
            time.sleep(1)  # Aguardar 1 segundo antes de tentar novamente
            return fetch_moskit_deals(api_key, start)  # Retry após espera
        else:
            print(f"Erro ao buscar negócios: {e}")
            return []

# Função para buscar usuários (responsáveis)
def fetch_moskit_users(api_key):
    url = 'https://api.moskitcrm.com/v2/users'
    headers = {'apikey': api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar usuários: {e}")
        return []

# Função para buscar produtos
def fetch_moskit_products(api_key):
    url = 'https://api.moskitcrm.com/v2/products'
    headers = {
        'Accept': 'application/json',
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar produtos: {e}")
        return []

# Função para tratar valores fora do alcance permitido
def sanitize_data(data):
    for row in data:
        for key, value in row.items():
            if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                row[key] = None  # Substituir valores inválidos por None
    return data

# Função para enviar dados ao Google Sheets
def send_to_google_sheets(data, creds_file, sheet_id):
    # Definir o escopo de permissões
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Autenticação com o arquivo de credenciais usando google-auth
    creds = Credentials.from_service_account_file(creds_file, scopes=scope)
    client = gspread.authorize(creds)
    
    # Abrir a planilha pelo ID da planilha e o nome da aba (sheet)
    sheet = client.open_by_key(sheet_id).worksheet('Sheet1')
    
    # Tratar dados antes de enviá-los
    sanitized_data = sanitize_data(data)
    
    # Transformar a lista de dicionários em DataFrame do Pandas
    df = pd.DataFrame(sanitized_data)
    
    # Transformar DataFrame em lista para Google Sheets
    sheet_data = [df.columns.values.tolist()] + df.fillna(0).values.tolist()  # Substituir NaN e vazios por 0
    
    # Limpar a planilha antes de inserir novos dados
    sheet.clear()
    
    # Inserir os dados na planilha (na primeira linha)
    sheet.insert_rows(sheet_data, 1)

# Função para extrair os dados de negócios e formatar para Google Sheets, incluindo status, produtos, dores do lead e origem
def extract_deals(deals, stages, users, products):
    extracted_data = []
    
    # Criar dicionário de fases, usuários e produtos para fácil acesso
    stages_dict = {stage['id']: stage['name'] for stage in stages}
    users_dict = {user['id']: user['name'] for user in users}
    products_dict = {product['id']: product['name'] for product in products}
    
    # Iterar sobre cada negócio (deal)
    for deal in deals:
        stage_name = stages_dict.get(deal.get('stage', {}).get('id'), 'Desconhecido')
        responsible_name = users_dict.get(deal.get('responsible', {}).get('id'), 'Desconhecido')

        # Usar o campo "status" para verificar o estado do negócio
        status = deal.get('status', 'OPEN')  # Pega o status do campo da API

        # Substituir os valores de status pela nomenclatura adequada
        if status == 'WON':
            status = 'Ganho'
        elif status == 'LOST':
            status = 'Perdido'
        else:
            status = 'Em andamento'

        # Se não houver produtos, dores do lead ou origem, substituir por "0"
        product_names = ', '.join([products_dict.get(product['product']['id'], '0') for product in deal.get('dealProducts', [])]) or '0'
        lead_pain = '0'
        lead_origin = '0'
        for custom_field in deal.get('entityCustomFields', []):
            if custom_field['id'] == "CF_AE5mpEijC3xW2DO3":  # ID correspondente ao campo de "Dores do Lead"
                lead_pain = custom_field.get('textValue', '0')
            if custom_field['id'] == "CF_nrLDXoiWiaZ5BmOa":  # ID correspondente ao campo "Origem"
                lead_origin = custom_field.get('options', ['0'])[0]  # Extraindo a primeira opção, se houver

        # Formatar as datas de criação e de fechamento
        creation_date = format_date(deal.get('dateCreated', 'Sem data'))
        closing_date = format_date(deal.get('closeDate', 'Sem data'))

        # Organizar os dados para cada negócio
        extracted_data.append({
            'Nome do Negócio': deal.get('name', 'Sem nome'),
            'Valor': deal.get('price', 0) / 100,  # Valor em centavos convertido para reais
            'Responsável': responsible_name,
            'Fase': stage_name,
            'Status': status,  # Adicionando o status do negócio
            'Produtos': product_names,
            'Dor do Lead': lead_pain,
            'Origem': lead_origin,
            'Data de Criação': creation_date,
            'Data de Fechamento': closing_date
        })
    
    return extracted_data

# Chave da API Moskit e arquivo de credenciais do Google
moskit_api_key = '5832bc39-ea60-4229-9ed6-a6e4d1fd96b8'  # Substitua pela sua chave correta  
google_creds_file = 'moskit-437500-584bca7cfbb1.json'  # Arquivo JSON de credenciais do Google
google_sheet_id = '19r7nsDDDoyFqu6uchuk-aPWBlvjsMywKWri3z8Ddrbw'  # ID da sua planilha Google

# Executando o fluxo completo
if __name__ == "__main__":
    all_data = []
    stages = fetch_moskit_stages(moskit_api_key)
    users = fetch_moskit_users(moskit_api_key)
    products = fetch_moskit_products(moskit_api_key)
    start = 0
    while True:
        deals = fetch_moskit_deals(moskit_api_key, start)
        if not deals:
            break
        extracted_data = extract_deals(deals, stages, users, products)
        all_data.extend(extracted_data)
        print(f"Negócios extraídos nesta página: {len(extracted_data)}")
        start += 50  # Atualizar o índice inicial para a próxima página
        if len(deals) < 50:
            break
    send_to_google_sheets(all_data, google_creds_file, google_sheet_id)
    print("Dados enviados ao Google Sheets com sucesso!")
