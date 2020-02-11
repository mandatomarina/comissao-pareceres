from lxml import html
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from gdrive_upload_folder import get_folder_id, create_folder, upload_files, authenticate
from os import chdir, listdir


PARENT_NAME = "PAUTAS_CCJR"

def uploadPareceres(data_reuniao):
    drive = authenticate()

    parent_folder_id = get_folder_id(drive, PARENT_NAME)

    # Upload the files
    dst_folder_id = create_folder(drive, data_reuniao, parent_folder_id)
    chdir('data/'+data_reuniao)

    for file1 in listdir('.'):
        f = drive.CreateFile(
            {"parents": [{"kind": "drive#fileLink", "id": dst_folder_id}]})
        f.SetContentFile(file1)
        f.Upload()


def getComissao(url, upload=False):
    print("Baixando pareceres...")
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    soup = html.fromstring(session.get(url).content)
    data_reuniao = soup.xpath("//table/tr/td[@width='30%']")[0].getnext().text_content().strip().replace('/','_')
    pauta = soup.xpath("//table/tr/td[@width='30%']")[3].getnext().xpath("./a")[0].get('href')

    if not os.path.exists("data/"+data_reuniao):
        os.mkdir("data/"+data_reuniao)
    p = session.get(pauta)
    with open("data/"+data_reuniao+"/pauta_"+data_reuniao+".pdf", 'wb') as pauta_f:
        pauta_f.write(p.content)

    lista_pareceres = soup.cssselect("#reunioes_detalhe_delibera tbody tr")
    for l in lista_pareceres:
        link = l.xpath("./td/a/img")
        name = l.xpath("./td/strong/a")
        for index, item in enumerate(link):
            url = item.getparent().get('href')
            filepath = url.split("/")[-1]

            if name:
                filepath = name[0].text_content().strip().replace("/","_").replace(" ","_") + ".doc"
                if len(link) > 1:
                    filepath = str(index) + "_" + filepath
            print(url)
            r = session.get(url)

            with open("data/"+data_reuniao+"/"+filepath, 'wb') as arquivo:
                arquivo.write(r.content)
    return data_reuniao

def getReuniao():
    print("Baixando a pauta...")
    url = "https://al.sp.gov.br/alesp/comissao?idComissao=12444"
    r = requests.get(url)
    soup = html.fromstring(r.content)

    base_url = "https://al.sp.gov.br"
    quadro = soup.cssselect("#reunioes_agendadas.quadro_conteudo_comissao")[0]
    for i in quadro.xpath(".//td/a"):
        if 'comissao-reuniao-agendada' in i.get('href'):
            data_reuniao = getComissao(base_url + i.get('href'))
            print("Got "+data_reuniao)
            uploadPareceres(data_reuniao)

getReuniao()

#hackish
#data_reuniao = getComissao("https://www.al.sp.gov.br/alesp/comissao-reuniao-agendada?idLegislatura=19&idComissao=12444&idReuniao=1000003117")
#uploadPareceres(data_reuniao)