import requests
import gspread
from google.oauth2.service_account import Credentials

# Defina a chave API do Pipefy e o ID do Pipe que deseja acessar
print("Iniciando a execução do código...")
pipefy_api_key = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3Mjg0MTIxNDEsImp0aSI6ImZlNTZlZWJiLWFhNGYtNGU3OC04Y2YyLTBmZTU3ZTU4ZmJlOCIsInN1YiI6MzA1Mjk0NTIwLCJ1c2VyIjp7ImlkIjozMDUyOTQ1MjAsImVtYWlsIjoiZ3VzdGF2by5hbGJ1cXVlcnF1ZUBmY2FwanIuY29tLmJyIn19.cxPT2oAL3kF3gm4oKaugy7yYka_sef0HIMCqKJtGK015oHJSuxHb9k-KdyVNbOuNTp10YvDFPU0zro42K6xbVA"
pipe_id = "303931233"  # ID do Pipe no Pipefy

# Configura os cabeçalhos da requisição
headers = {
    "Authorization": f"Bearer {pipefy_api_key}",
    "Content-Type": "application/json"
}

# Configuração para o Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('pipefy-marketing-8ba6228e121f.json', scopes=scope)
client = gspread.authorize(creds)

# Função para buscar os dados paginados do Pipefy
def fetch_pipefy_data():
    print("Buscando dados do Pipefy...")
    all_cards = []
    has_next_page = True
    after_cursor = None
    items_per_page = 100  # Quantidade de cards por página (máximo de 100)

    while has_next_page:
        # Construir a query GraphQL
        if after_cursor:
            query = f'''
            {{
              allCards(pipeId: {pipe_id}, first: {items_per_page}, after: "{after_cursor}") {{
                pageInfo {{
                  hasNextPage
                  endCursor
                }}
                edges {{
                  node {{
                    id
                    title
                    current_phase {{
                      name
                    }}
                    fields {{
                      name
                      value
                    }}
                  }}
                }}
              }}
            }}
            '''
        else:
            # Sem o 'after' na primeira chamada
            query = f'''
            {{
              allCards(pipeId: {pipe_id}, first: {items_per_page}) {{
                pageInfo {{
                  hasNextPage
                  endCursor
                }}
                edges {{
                  node {{
                    id
                    title
                    current_phase {{
                      name
                    }}
                    fields {{
                      name
                      value
                    }}
                  }}
                }}
              }}
            }}
            '''

        url = "https://api.pipefy.com/graphql"
        response = requests.post(url, json={'query': query}, headers=headers)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            data = response.json()

            # Adiciona um tratamento para garantir que 'data' está presente
            if 'data' in data and 'allCards' in data['data']:
                cards = data['data']['allCards']['edges']
                all_cards.extend(cards)  # Armazenar todos os cards

                # Verificar se há mais páginas
                has_next_page = data['data']['allCards']['pageInfo']['hasNextPage']
                after_cursor = data['data']['allCards']['pageInfo']['endCursor']
                print(f"{len(cards)} cards coletados, continuando...")
            else:
                print("A resposta não contém os dados esperados. Resposta completa:", data)
                break
        else:
            print(f"Erro na requisição: {response.status_code}, Detalhes: {response.text}")
            has_next_page = False  # Parar o loop em caso de erro

    print(f"Total de {len(all_cards)} cards coletados.")
    return all_cards

# Função para enviar os dados para o Google Sheets, limpando e adicionando todos os dados novamente
def send_to_google_sheets(cards, sheet_id):
    # Abrir a planilha
    sheet = client.open_by_key(sheet_id).sheet1

    # Limpar todas as linhas da planilha
    print("Limpando a planilha...")
    sheet.clear()

    # Adicionar o cabeçalho novamente com os novos campos
    sheet.append_row(['ID', 'Título', 'Nome do Contato', 'Email', 'Telefone', 'Empresa', 'Cargo', 'Setor', 'Data', 'Origem do Lead', 'Dúvida do Lead', 'Responsável', 'Observações', 'Fase Atual'])

    # Lista para agrupar as linhas a serem enviadas
    rows = []
    
    # Escrevendo os dados dos cards no Google Sheets
    for card in cards:
        card_data = {}
        card_data['ID'] = card['node']['id']  # ID do card (único)
        card_data['Título'] = card['node']['title']
        card_data['Fase Atual'] = card['node']['current_phase']['name'] if 'current_phase' in card['node'] else "Sem Fase"

        # Inicializa variáveis com valores padrão para evitar erros
        card_data['Nome do Contato'] = ""
        card_data['Email'] = ""
        card_data['Telefone'] = ""
        card_data['Empresa'] = ""
        card_data['Cargo'] = ""
        card_data['Setor'] = ""
        card_data['Data'] = ""
        card_data['Origem do Lead'] = ""
        card_data['Dúvida do Lead'] = ""
        card_data['Responsável'] = ""
        card_data['Observações'] = ""

        # Associa os valores esperados pelos nomes dos campos
        for field in card['node']['fields']:
            if field['name'] == "Nome do contato":
                card_data['Nome do Contato'] = field['value']
            elif field['name'] == "Email":
                card_data['Email'] = field['value']
            elif field['name'] == "Telefone":
                card_data['Telefone'] = field['value']
            elif field['name'] == "Empresa":
                card_data['Empresa'] = field['value']
            elif field['name'] == "Cargo":
                card_data['Cargo'] = field['value']
            elif field['name'] == "Setor":
                card_data['Setor'] = field['value']
            elif field['name'] == "Data":
                card_data['Data'] = field['value']
            elif field['name'] == "Origem do lead":
                card_data['Origem do Lead'] = field['value']
            elif field['name'] == "Dúvida do Lead":
                card_data['Dúvida do Lead'] = field['value']
            elif field['name'] == "Responsável":
                card_data['Responsável'] = field['value']
            elif field['name'] == "Observações":
                card_data['Observações'] = field['value']

        # Adicionar o card à lista de linhas
        rows.append([
            card_data['ID'],
            card_data['Título'],
            card_data['Nome do Contato'],
            card_data['Email'],
            card_data['Telefone'],
            card_data['Empresa'],
            card_data['Cargo'],
            card_data['Setor'],
            card_data['Data'],
            card_data['Origem do Lead'],
            card_data['Dúvida do Lead'],
            card_data['Responsável'],
            card_data['Observações'],
            card_data['Fase Atual']
        ])

    # Enviar todas as linhas de uma vez para o Google Sheets
    if rows:
        print(f"Enviando {len(rows)} registros para o Google Sheets...")
        sheet.append_rows(rows, value_input_option="RAW")
        print("Dados enviados com sucesso!")

    print("Dados enviados para o Google Sheets com sucesso.")

# Executa suas funções aqui
cards_data = fetch_pipefy_data()
if cards_data:
    send_to_google_sheets(cards_data, '1UL3iC1zALFhRjFBgIMDf1beTAvnvr67J-KOe4kTs8u4')  # Substitua pelo ID da sua planilha do Google Sheets
