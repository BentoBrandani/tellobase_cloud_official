from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import qrcode
import os
from datetime import datetime

# Configurações básicas
PASTA_FOTOS = "fotos"  # Nome da pasta que será enviada ao Drive
PASTA_DRIVE_RAIZ = "Uploads_Fotos"  # Nome da pasta fixa para onde serão enviados álbuns
QR_CODE_FILE = "qrcode_album.png" # Nome da imagem QRcode que será gerada para acessar o link


def autenticar_google_drive():
    # Autentica usando as informações do client_secres.json
    gauth = GoogleAuth()

    # Para não ser necessário logar sempre em uma conta, as credenciais de uma conta
    # com acesso ao projeto serão guardadas aqui (por quanto, guardam as credenciais ligadas
    # à conta thiagomartins2710@gmail.com)
    gauth.LoadCredentialsFile("credentials.json")

    # Verifica se já há credenciais existentes
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("credentials.json")
    return GoogleDrive(gauth)


def criar_pasta_se_nao_existir(drive, nome_pasta):
    query = f"title='{nome_pasta}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    result = drive.ListFile({'q': query}).GetList()

    if result:
        print(f"Pasta já existe no Drive: {nome_pasta}")
        return result[0]['id']

    pasta = drive.CreateFile({
        'title': nome_pasta,
        'mimeType': 'application/vnd.google-apps.folder'
    })
    pasta.Upload()

    print(f"Pasta criada no Drive: {nome_pasta}")
    return pasta['id']


def enviar_fotos_individualmente(drive, pasta_drive_id):
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

# Gerar um qrcode a partir de um link fica fácil com a biblioteca qrcode :)
def gerar_qrcode(link):
    qr = qrcode.make(link)
    qr.save(QR_CODE_FILE)
    qr.show()
    print(f"QR Code salvo como: {QR_CODE_FILE}")


def main():
    # Autenticação
    drive = autenticar_google_drive()

    # Criar pasta fixa no Drive
    raiz_id = criar_pasta_se_nao_existir(drive, PASTA_DRIVE_RAIZ)

    # Criar pasta com timestamp para o álbum
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pasta_album_id = criar_pasta_se_nao_existir(drive, f"Album_{timestamp}")

    # Tornar pasta pública
    drive.auth.service.permissions().insert(
        fileId=pasta_album_id,
        body={"type": "anyone", "role": "reader"}
    ).execute()

    # Enviar fotos individualmente
    enviar_fotos_individualmente(drive, pasta_album_id)

    # Gerar link da pasta + QR Code
    link = f"https://drive.google.com/drive/folders/{pasta_album_id}?usp=sharing"
    print("Link do álbum:", link)
    gerar_qrcode(link)


if __name__ == "__main__":
    main()
