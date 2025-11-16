import time
from time import sleep
import cv2
import random
import os
import sys
from djitellopy import Tello
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import qrcode
from datetime import datetime

# -v --> Verbose
verbose = False
if '-v' in sys.argv or '--v' in sys.argv or '--verbose' in sys.argv:
    verbose = True
    print("Verbose mode enabled")

# --- LIMPAR PASTA FOTOS A CADA EXECUÇÃO ---
FOTOS_DIR = "fotos"
if os.path.isdir(FOTOS_DIR):
    for file in os.listdir(FOTOS_DIR):
        try:
            os.remove(os.path.join(FOTOS_DIR, file))
        except:
            pass
else:
    os.makedirs(FOTOS_DIR)
# ------------------------------------------

PICTURES_UNTILL_CHANGE = 3
DOWN_LIMIT = 80
UP_LIMIT = 230
SLEEP_FOR = 2

# Configurações básicas
PASTA_FOTOS = "fotos"  # Nome da pasta local contendo as fotos
PASTA_DRIVE_RAIZ = "Uploads_Fotos"  # Nome da pasta fixa no Drive
QR_CODE_FILE = "qrcode_album.png"  # Nome da imagem QRcode gerada

def autenticar_google_drive():
    """Autentica no Google Drive usando credentials.json"""
    gauth = GoogleAuth()

    gauth.LoadCredentialsFile("credentials.json")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("credentials.json")
    return GoogleDrive(gauth)


def criar_pasta_se_nao_existir(drive, nome_pasta, parent_id=None):
    """
    Cria uma pasta no Drive, opcionalmente dentro de outra pasta.
    Se já existir, retorna seu ID.
    """

    # Query muda caso exista parent
    if parent_id:
        query = (
            f"title='{nome_pasta}' and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false and '{parent_id}' in parents"
        )
    else:
        query = (
            f"title='{nome_pasta}' and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        )

    result = drive.ListFile({'q': query}).GetList()

    if result:
        print(f"Pasta já existe: {nome_pasta}")
        return result[0]['id']

    metadata = {
        'title': nome_pasta,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    if parent_id:
        metadata['parents'] = [{'id': parent_id}]

    pasta = drive.CreateFile(metadata)
    pasta.Upload()

    print(f"Pasta criada: {nome_pasta}")
    return pasta['id']


def enviar_fotos_individualmente(drive, pasta_drive_id):
    """Envia todos os arquivos da pasta local para o Drive."""
    arquivos = os.listdir(PASTA_FOTOS)
    if not arquivos:
        print("Nenhuma foto encontrada na pasta local!")
        return

    for arquivo in arquivos:
        caminho = os.path.join(PASTA_FOTOS, arquivo)
        if os.path.isfile(caminho):
            file_drive = drive.CreateFile({
                'title': arquivo,
                'parents': [{'id': pasta_drive_id}]
            })

            file_drive.SetContentFile(caminho)
            file_drive.Upload()

            # Permitir acesso público
            file_drive.InsertPermission({
                "type": "anyone",
                "role": "reader"
            })

            print(f"Foto enviada: {arquivo}")

    print("Upload de todas as fotos concluído!")


def gerar_qrcode(link):
    """Gera imagem QR Code apontando para o link."""
    qr = qrcode.make(link)
    qr.save(QR_CODE_FILE)
    qr.show()
    print(f"QR Code salvo como: {QR_CODE_FILE}")


# Autenticação
drive = autenticar_google_drive()

# Criar pasta raiz (fica na raiz do Drive)
raiz_id = criar_pasta_se_nao_existir(drive, PASTA_DRIVE_RAIZ)

# Criar pasta do álbum dentro da pasta raiz
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
nome_album = f"Album_{timestamp}"

pasta_album_id = criar_pasta_se_nao_existir(drive, nome_album, parent_id=raiz_id)

# Tornar álbum público
drive.auth.service.permissions().insert(
    fileId=pasta_album_id,
    body={"type": "anyone", "role": "reader"}
).execute()

tello = Tello()
tello.connect()
tello.streamon()

cap = tello.get_frame_read()

sleep(0.2)

tello.takeoff()
tello.move_up(100)

index = 0
pictures_til_change = 0

dist = tello.get_distance_tof()

try:
    while True:
        if abs(tello.get_distance_tof() - dist) > 60:
            tello.emergency()

        if pictures_til_change == PICTURES_UNTILL_CHANGE:
            pictures_til_change = 0
            tello.move_down(random.randint(20, 40))
            dist = tello.get_distance_tof()
        else:
            if random.randint(0, 1) == 0:
                tello.rotate_clockwise(random.randint(40, 360))
            else:
                tello.rotate_counter_clockwise(random.randint(40, 360))
            
            sleep(1)
            
            # Salvar a imagem na pasta "fotos"
            frame = cv2.cvtColor(cap.frame, cv2.COLOR_RGB2BGR)
            filename = f"fotos/picture_{index}.png"
            cv2.imwrite(filename, frame)
            print(f"Foto salva: {filename}")

            index += 1
            pictures_til_change += 1

except KeyboardInterrupt:
    print("Interrompido pelo usuário")

finally:
    # Sempre executar esta parte, mesmo em caso de erro
    tello.streamoff()
    tello.land()
    
    # Enviar as fotos para o Drive
    enviar_fotos_individualmente(drive, pasta_album_id)

    # Gerar link do álbum
    link = f"https://drive.google.com/drive/folders/{pasta_album_id}?usp=sharing"
    print("Link do álbum:", link)

    gerar_qrcode(link)