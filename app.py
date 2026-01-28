import fitz  # PyMuPDF
import re
import json
import time

def extract_clients_from_large_pdf(pdf_path, output_path):
    print(f"Iniciando processamento de: {pdf_path}")
    start_time = time.time()
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"Total de páginas encontradas: {total_pages}")
    except Exception as e:
        print(f"Erro ao abrir o PDF: {e}")
        return

    all_clients = []
    
    # Regex compilados para melhor performance em 900+ páginas
    re_cliente_start = re.compile(r'Cliente:\s*(.*?)(?=\s*Nome Fantasia|\s*Código|\n)')
    re_codigo = re.compile(r'Código:\s*(\d+)')
    re_cnpj = re.compile(r'CNPJ:\s*([\d./-]+)')
    re_cpf = re.compile(r'CPF:\s*([\d.-]+)')
    re_email = re.compile(r'Email:\s*(.*?)(?=\n|$|Cidade:|Logradouro:)')
    re_telefone = re.compile(r'Telefone:\s*(.*?)(?=\s*Celular|\n)')
    re_celular = re.compile(r'Celular:\s*(.*?)(?=\n|Email|CNPJ|CPF)')
    
    # Regex de Endereço
    re_logradouro = re.compile(r'Logradouro:\s*(.*?)(?=\s*Número|\n)')
    re_numero = re.compile(r'Número:\s*(.*?)(?=\s*Bairro|\n)')
    re_bairro = re.compile(r'Bairro:\s*(.*?)(?=\s*Cidade|\s*Telefone|\n)')
    re_cidade = re.compile(r'Cidade:\s*(.*?)(?=\s*Estado|\s*Código|\n)')
    re_uf = re.compile(r'Estado:\s*([A-Z]{2})')
    re_cep = re.compile(r'CEP:\s*([\d-]+)')

    # Iterar página por página para não sobrecarregar a memória
    for page_num, page in enumerate(doc):
        # Feedback de progresso a cada 100 páginas
        if (page_num + 1) % 100 == 0:
            print(f"Processando página {page_num + 1}/{total_pages}...")
            
        text = page.get_text()
        
        # Adicionar um marcador artificial para dividir os clientes, pois "Cliente:" é o início
        # Usamos uma estratégia de split baseada no texto bruto da página
        blocks = text.replace('Cliente:', '___SPLIT___Cliente:').split('___SPLIT___')
        
        for block in blocks:
            # Ignorar blocos que não sejam dados de cliente (cabeçalhos, etc)
            if 'Cliente:' not in block:
                continue
                
            client_data = {}
            
            # Nome / Razão Social
            nome_match = re_cliente_start.search(block)
            if nome_match:
                client_data['nome'] = nome_match.group(1).strip()
            else:
                continue # Se não achou nome, pula

            # Código
            cod_match = re_codigo.search(block)
            if cod_match: client_data['codigo'] = cod_match.group(1)

            # Documento (CNPJ ou CPF)
            cnpj_match = re_cnpj.search(block)
            cpf_match = re_cpf.search(block)
            if cnpj_match:
                client_data['documento'] = cnpj_match.group(1)
                client_data['tipo_doc'] = 'CNPJ'
            elif cpf_match:
                client_data['documento'] = cpf_match.group(1)
                client_data['tipo_doc'] = 'CPF'

            # Contatos (Email e Telefones)
            email_match = re_email.search(block)
            if email_match:
                raw_emails = email_match.group(1).strip()
                emails = [e.strip() for e in raw_emails.split(';') if '@' in e]
                if emails: client_data['emails'] = emails
            
            tel_match = re_telefone.search(block)
            cel_match = re_celular.search(block)
            
            phones = []
            if tel_match and len(tel_match.group(1).strip()) > 6:
                phones.append({'tipo': 'fixo', 'numero': tel_match.group(1).strip()})
            if cel_match and len(cel_match.group(1).strip()) > 6:
                phones.append({'tipo': 'celular', 'numero': cel_match.group(1).strip()})
            
            if phones: client_data['telefones'] = phones

            # Endereço
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
            
            if endereco: client_data['endereco'] = endereco
            
            all_clients.append(client_data)

    # Salvar Arquivo JSON Final
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_clients, f, ensure_ascii=False, indent=2)

    end_time = time.time()
    print(f"\nConcluído! {len(all_clients)} clientes extraídos.")
    print(f"Arquivo salvo em: {output_path}")
    print(f"Tempo total: {end_time - start_time:.2f} segundos")

# Execução
# Certifique-se de que o nome do arquivo PDF está correto aqui:
pdf_file = "clcientes.pdf" 
json_file = "clientes_completo.json"

if __name__ == "__main__":
    extract_clients_from_large_pdf(pdf_file, json_file)