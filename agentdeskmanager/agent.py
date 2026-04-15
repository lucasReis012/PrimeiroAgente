from google.adk.agents.llm_agent import Agent
from trello import TrelloClient
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

API_KEY = os.getenv('TRELLO_API_KEY')
API_SECRET = os.getenv('TRELLO_API_SECRET')
TOKEN= os.getenv('TRELLO_API_TOKEN')

def get_temporal_context():
    now = datetime.now()
    return now.strftime('%Y/%m/%d %H:%M:%S')

def adicionar_tarefa(nome_da_task: str, descricao_da_task: str, data_da_task: str):
    client = TrelloClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        token=TOKEN
    )

    # Converte a data para o formato aceito pelo Trello
    try:
        data_formatada = datetime.strptime(data_da_task, '%Y/%m/%d').strftime('%Y-%m-%dT00:00:00.000Z')
    except:
        data_formatada = None  # Se a data for inválida, cria o card sem data

    boards = client.list_boards()
    meu_board = [b for b in boards if b.name.upper() == 'PROJECT-DIO'][0]
    listas = meu_board.list_lists()
    minha_lista = [l for l in listas if l.name.upper() in ['TO DO', 'A FAZER']][0]
    minha_lista.add_card(nome_da_task, descricao_da_task, due=data_formatada)

def mudar_status_tarefa(nome_da_task:str, novo_status:str) -> str:
        client = TrelloClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        token=TOKEN
        )
        boards = client.list_boards()
        meu_board = [b for b in boards if b.name.upper() =='PROJECT-DIO'][0]
        listas = meu_board.list_lists()

        status_map ={
            'a fazer':'A FAZER',
            'em andamento':'EM ANDAMENTO',
            'concluído':'CONCLUÍDO'
        }
        nome_lista_destino = status_map.get(novo_status.lower())

        if not nome_lista_destino:
            return f"X Status invalido. use: 'a fazer', 'em andamento', ou 'concluído "
        lista_destino = next(
            (l for l in listas if l.name.upper() == nome_lista_destino.upper()), 
            None
        )
        if not lista_destino:
            return f"X lista '{nome_lista_destino}' não encontrada no board"
        card_encontrado = None
        lista_origem = None

        for lista in listas:
            cards= lista.list_cards()
            card_encontrado= next(
                (c for c in cards if c.name.lower() == nome_da_task.lower()),
                None
            )
            if card_encontrado:
                lista_origem= lista
                break
        if not card_encontrado:
            return f"X Card '{nome_da_task}' não encontrado"
        
        card_encontrado.change_list(lista_destino.id)
        return f"Verdadeiro, tarefa '{nome_da_task}' movida para '{novo_status}' com sucesso"





def listar_tarefas(status:str ="todas"):
    client = TrelloClient(
        api_key = API_KEY,
        api_secret=API_SECRET,
        token=TOKEN
    )
    boards = client.list_boards()
    meu_board = [b for b in boards if b.name.upper() =='PROJECT-DIO'][0]
    listas = meu_board.list_lists()
    if status.lower() == "todas":
        listas_filtradas = listas
    elif status.lower()=="a fazer":
        listas_filtradas = [l for l in listas if l.name.upper() in ['A FAZER', 'TO DO', 'TODO']]
    elif status.lower()=="em andamento":
        listas_filtradas = [l for l in listas if l.name.upper() in ['EM ANDAMENTO', 'DOING']]
    elif status.lower()=="concluido":
        listas_filtradas = [l for l in listas if l.name.upper() in ['CONCLUÍDO', 'CONCLUIDO','DONE']]
    else:
        listas_filtradas= listas

    tarefas =[]

    for lista in listas_filtradas:
        cards = lista.list_cards()
        for card in cards:
            tarefas.append({
                'nome': card.name,
                'descricao':card.desc, 
                'vencimento':card.due,
                'status': lista.name,
                'id':card.id
            })
    return tarefas

root_agent = Agent(
    model='gemini-2.5-flash',   
    name='root_agent',
    description='Agente de Organização de Tarefas',
    instruction="""
            Você é um agente de Organização de tarefas.
            Sua Função é receber uma tarefa e criar um card no trello com o nome e descrição da tarefa.
            Você deve me perguntar as atividades que tenho no dia e criar um card para cada uma delas.
            Você inicia a conversa assim que for ativado, perguntando quais são as tarefas do dia.
            Sempre inicie a conversa perguntando quais são as tarefas do dia informando a data com pela tool get_temporal_context,
            e depois vá perguntando se tem mais alguma tarefa, até que o usuário diga que não tem mais tarefas. 
            Suas Funções:
                1. Adicionar novas tarefas com o nome e descrição
                2. Listar as tarefas ou filtrar por status
                3. Marcas tarefas concluídas 
                4. Remover tarefas da lista
                5. Mudas o status da tarefa (ex: de "A Fazer" para "Em Andamento" para "Concluído")
                6. Gerar contexto temporal (data e hora atual) para organizar as tarefas do dia

    """,
    tools=[
        adicionar_tarefa, get_temporal_context, listar_tarefas, mudar_status_tarefa
        ]
)
