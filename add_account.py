from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
import pickle
import os

api_id = '21963510'
api_hash = 'eddfccf6e4ea21255498028e5af25eb1'

# Assicurati che la cartella per le sessioni esista
if not os.path.exists('sessions'):
    os.makedirs('sessions')

if not os.path.exists('vars.txt'):
    open('vars.txt', 'w').close()

def add_account(phone_number):
    client = TelegramClient(f'sessions/{phone_number}', api_id, api_hash)
    client.connect()
    
    if not client.is_user_authorized():
        try:
            client.send_code_request(phone_number)
            code = input(f'Inserisci il codice ricevuto via Telegram per {phone_number}: ')
            client.sign_in(phone_number, code)
        except SessionPasswordNeededError:
            password = input(f'Inserisci la tua password per {phone_number}: ')
            client.sign_in(password=password)
    
    me = client.get_me()
    print(f'Successfully logged in as {me.first_name} ({phone_number})')

    # Salva il numero di telefono in vars.txt
    with open('vars.txt', 'ab') as f:
        pickle.dump([phone_number], f)
    
    client.disconnect()

if __name__ == '__main__':
    phone_number = input('Inserisci il numero di telefono con il prefisso internazionale (es. +39...): ')
    add_account(phone_number)
