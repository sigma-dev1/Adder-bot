from telethon import TelegramClient, events
from telethon.errors import PeerFloodError, UserPrivacyRestrictedError, UserAlreadyParticipantError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import PeerChannel
import pickle
import time
import os
import asyncio

# Configurazioni API e HASH
api_id = '21963510'
api_hash = 'eddfccf6e4ea21255498028e5af25eb1'
admin_id = 6849853752  # Sostituisci con l'ID autorizzato

clients = []
stop_adding = False

# Carica gli account dal file vars.txt
def load_accounts():
    accounts = []
    if os.path.exists('vars.txt'):
        with open('vars.txt', 'rb') as f:
            while True:
                try:
                    accounts.append(pickle.load(f))
                except EOFError:
                    break
    return accounts

# Configura i client per ogni account, utilizzando le sessioni salvate
async def setup_clients():
    global clients
    accounts = load_accounts()
    
    for account in accounts:
        phone_number = account[0]
        session_file = f'sessions/{phone_number}.session'
        
        # Crea il client per ciascun account usando la sessione salvata
        client = TelegramClient(session_file, api_id, api_hash)
        await client.connect()
        
        # Verifica se l'account è autorizzato
        if await client.is_user_authorized():
            clients.append(client)
            print(f'Account {phone_number} autorizzato e aggiunto.')
        else:
            print(f'Account {phone_number} non è autorizzato. Saltato.')
            await client.disconnect()  # Disconnette se non autorizzato
    
    print(f'Set up {len(clients)} clients.')

# Gestione comando /start
async def handle_start(event):
    await event.respond("Comandi disponibili:\n/lista\n/ruba <group_id>\n/add <group_id>\n/add2\n/add3\n/stop")

# Gestione comando /lista
async def handle_lista(event):
    response = "Lista dei gruppi:\n"
    for client in clients:
        async for dialog in client.iter_dialogs():
            if dialog.is_channel:
                response += f"{dialog.entity.title} (ID: {dialog.entity.id})\n"
    await event.respond(response)

# Gestione comando /ruba
async def handle_ruba(event, group_id):
    with open('scraped_users.txt', 'w') as f:
        for client in clients:
            async for user in client.iter_participants(PeerChannel(group_id)):
                f.write(f"{user.id}\n")
    await event.respond(f"Utenti rubati dal gruppo {group_id}.")

# Gestione comando /add
async def handle_add(event, target_group_id):
    global stop_adding
    added_users = set()
    
    if os.path.exists('added_users.txt'):
        with open('added_users.txt', 'r') as f:
            for line in f:
                added_users.add(line.strip())
    
    with open('scraped_users.txt', 'r') as f:
        user_ids = f.readlines()

    for client in clients:
        for user_id in user_ids:
            if stop_adding:
                break

            if str(user_id.strip()) not in added_users:
                try:
                    await client(InviteToChannelRequest(PeerChannel(target_group_id), [int(user_id.strip())]))
                    added_users.add(str(user_id.strip()))
                    with open('added_users.txt', 'a') as f:
                        f.write(f'{user_id.strip()}\n')
                    await asyncio.sleep(30)  # Attesa di 30 secondi tra ogni aggiunta
                except (PeerFloodError, UserPrivacyRestrictedError, UserAlreadyParticipantError) as e:
                    print(f"Errore aggiungendo {user_id.strip()}: {e}")
    await event.respond(f"Utenti aggiunti al gruppo {target_group_id}.")

# Gestione comando /add2 e /add3
async def handle_add_special(event, command):
    global stop_adding
    added_users = set()
    command_users = set()

    if os.path.exists('added_users.txt'):
        with open('added_users.txt', 'r') as f:
            added_users.update(line.strip() for line in f)
    
    if os.path.exists('scraped_users.txt'):
        with open('scraped_users.txt', 'r') as f:
            command_users.update(line.strip() for line in f)

    for client in clients:
        async for dialog in client.iter_dialogs():
            if dialog.is_channel:
                async for message in client.iter_messages(dialog.entity.id):
                    if (message.sender_id and str(message.sender_id) in command_users 
                            and command in message.message.lower()):
                        if str(message.sender_id) not in added_users:
                            try:
                                await client(InviteToChannelRequest(PeerChannel(dialog.entity.id), [message.sender_id]))
                                added_users.add(str(message.sender_id))
                                with open('added_users.txt', 'a') as f:
                                    f.write(f"{message.sender_id}\n")
                                await asyncio.sleep(30)
                            except (PeerFloodError, UserPrivacyRestrictedError, UserAlreadyParticipantError) as e:
                                print(f"Errore aggiungendo {message.sender_id}: {e}")
    await event.respond(f"Utenti aggiunti tramite comando {command}.")

# Gestione comando /stop
async def handle_stop(event):
    global stop_adding
    stop_adding = True
    await event.respond("Aggiunta di utenti fermata.")

# Main function per avviare il bot con i comandi
async def main():
    await setup_clients()
    
    if clients:
        bot = clients[0]

        @bot.on(events.NewMessage(pattern='/start'))
        async def start(event):
            if event.sender_id == admin_id:
                await handle_start(event)
            else:
                await event.respond("Non sei autorizzato a usare questo bot.")

        @bot.on(events.NewMessage(pattern='/lista'))
        async def lista(event):
            if event.sender_id == admin_id:
                await handle_lista(event)
            else:
                await event.respond("Non sei autorizzato a usare questo comando.")

        @bot.on(events.NewMessage(pattern='/ruba (.+)'))
        async def ruba(event):
            if event.sender_id == admin_id:
                group_id = int(event.pattern_match.group(1))
                await handle_ruba(event, group_id)
            else:
                await event.respond("Non sei autorizzato a usare questo comando.")

        @bot.on(events.NewMessage(pattern='/add (.+)'))
        async def add(event):
            if event.sender_id == admin_id:
                target_group_id = int(event.pattern_match.group(1))
                await handle_add(event, target_group_id)
            else:
                await event.respond("Non sei autorizzato a usare questo comando.")

        @bot.on(events.NewMessage(pattern='/add2'))
        async def add2(event):
            if event.sender_id == admin_id:
                await handle_add_special(event, "/add2")
            else:
                await event.respond("Non sei autorizzato a usare questo comando.")

        @bot.on(events.NewMessage(pattern='/add3'))
        async def add3(event):
            if event.sender_id == admin_id:
                await handle_add_special(event, "/add3")
            else:
                await event.respond("Non sei autorizzato a usare questo comando.")

        @bot.on(events.NewMessage(pattern='/stop'))
        async def stop(event):
            if event.sender_id == admin_id:
                await handle_stop(event)
            else:
                await event.respond("Non sei autorizzato a usare questo comando.")

        await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
