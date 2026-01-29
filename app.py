from fastapi import FastAPI, UploadFile, File
import fitz
import re
import json

app = FastAPI()

# ======= seu parser (praticamente igual) =======
re_cliente_start = re.compile(r'Cliente:\s*(.*?)(?=\s*Nome Fantasia|\s*Código|\n)')
re_codigo = re.compile(r'Código:\s*(\d+)')
re_cnpj = re.compile(r'CNPJ:\s*([\d./-]+)')
re_cpf = re.compile(r'CPF:\s*([\d.-]+)')
re_email = re.compile(r'Email:\s*(.*?)(?=\n|$|Cidade:|Logradouro:)')
re_telefone = re.compile(r'Telefone:\s*(.*?)(?=\s*Celular|\n)')
re_celular = re.compile(r'Celular:\s*(.*?)(?=\n|Email|CNPJ|CPF)')

re_logradouro = re.compile(r'Logradouro:\s*(.*?)(?=\s*Número|\n)')
re_numero = re.compile(r'Número:\s*(.*?)(?=\s*Bairro|\n)')
re_bairro = re.compile(r'Bairro:\s*(.*?)(?=\s*Cidade|\s*Telefone|\n)')
re_cidade = re.compile(r'Cidade:\s*(.*?)(?=\s*Estado|\s*Código|\n)')
re_uf = re.compile(r'Estado:\s*([A-Z]{2})')
re_cep = re.compile(r'CEP:\s*([\d-]+)')

def extract_clients_from_pdf_bytes(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_clients = []

    for page in doc:
        text = page.get_text()  # do jeito que funcionou pra você

        blocks = text.replace('Cliente:', '___SPLIT___Cliente:').split('___SPLIT___')
        for block in blocks:
            if 'Cliente:' not in block:
                continue

            client_data = {}

            nome_match = re_cliente_start.search(block)
            if not nome_match:
                continue
            client_data['nome'] = nome_match.group(1).strip()

            cod_match = re_codigo.search(block)
            if cod_match:
                client_data['codigo'] = cod_match.group(1)

            cnpj_match = re_cnpj.search(block)
            cpf_match = re_cpf.search(block)
            if cnpj_match:
                client_data['documento'] = cnpj_match.group(1)
                client_data['tipo_doc'] = 'CNPJ'
            elif cpf_match:
                client_data['documento'] = cpf_match.group(1)
                client_data['tipo_doc'] = 'CPF'

            email_match = re_email.search(block)
            if email_match:
                raw_emails = email_match.group(1).strip()
                emails = [e.strip() for e in raw_emails.split(';') if '@' in e]
                if emails:
                    client_data['emails'] = emails

            tel_match = re_telefone.search(block)
            cel_match = re_celular.search(block)
            phones = []
            if tel_match and len(tel_match.group(1).strip()) > 6:
                phones.append({'tipo': 'fixo', 'numero': tel_match.group(1).strip()})
            if cel_match and len(cel_match.group(1).strip()) > 6:
                phones.append({'tipo': 'celular', 'numero': cel_match.group(1).strip()})
            if phones:
                client_data['telefones'] = phones

            endereco = {}
            log_match = re_logradouro.search(block)
            num_match = re_numero.search(block)
            bai_match = re_bairro.search(block)
            cid_match = re_cidade.search(block)
            uf_match = re_uf.search(block)
            cep_match = re_cep.search(block)

            if log_match: endereco['logradouro'] = log_match.group(1).strip()
            if num_match: endereco['numero'] = num_match.group(1).strip()
            if bai_match: endereco['bairro'] = bai_match.group(1).strip()
            if cid_match: endereco['cidade'] = cid_match.group(1).strip()
            if uf_match: endereco['uf'] = uf_match.group(1).strip()
            if cep_match: endereco['cep'] = cep_match.group(1).strip()
            if endereco:
                client_data['endereco'] = endereco

            all_clients.append(client_data)

    return all_clients

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    clients = extract_clients_from_pdf_bytes(pdf_bytes)
    return {"count": len(clients), "clients": clients}
