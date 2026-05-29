import os
import csv
import glob
import sys
import shutil
import zipfile
import urllib.request
import email.utils
from collections import defaultdict
from datetime import date, datetime, timedelta

def select_folder(title="Selecione a pasta", console_prompt="Digite o caminho da pasta"):
    print(f"Iniciando o selecionador de pastas para: {title}...")

    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()  
    
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title=title)
        if folder:
            return folder
    except Exception as e:
        
        pass
    

    print("\n--- Seleção Manual de Pasta (Interface Gráfica Não Disponível) ---")
    current_dir = os.getcwd()
    print(f"Diretório atual: {current_dir}")
    folder = input(f"{console_prompt} (pressione Enter para usar o diretório atual): ").strip()
    if not folder:
        return current_dir
    return folder

def classify_operator(empresa, grupo, porte):

    emp = str(empresa).upper().strip()
    grp = str(grupo).upper().strip()
    prt = str(porte).upper().strip()
    
    # 1. Grandes MNOs Nacionais
    if 'TELEFONICA' in emp or 'VIVO' in emp or 'TELEFÔNICA' in emp or 'VIVO' in grp or 'TELEFONICA' in grp:
        return 'VIVO', 'TELEFÔNICA', 'Grande Porte', 'MNO'
    if 'CLARO' in emp or 'TELECOM AMERICAS' in grp or 'TELECOM AMÉRICAS' in grp:
        return 'CLARO', 'TELECOM AMERICAS', 'Grande Porte', 'MNO'
    if 'TIM' in emp or 'TELECOM ITALIA' in grp:
        return 'TIM', 'TELECOM ITALIA', 'Grande Porte', 'MNO'
    if 'OI' in emp or 'OI' in grp:
        return 'OI', 'OI', 'Grande Porte', 'MNO'
    if 'NEXTEL' in emp or 'NEXTEL' in grp:
        return 'NEXTEL', 'NEXTEL', 'Grande Porte', 'MNO'


    if 'ALGAR' in emp or 'CTBC' in emp or 'ALGAR' in grp:
        return 'ALGAR', 'ALGAR', 'Pequeno Porte', 'MNO'
    if 'BRISANET' in emp or 'BRISANET' in grp:
        return 'BRISANET', 'BRISANET', 'Pequeno Porte', 'MNO'
    if 'UNIFIQUE' in emp or 'UNIFIQUE' in grp:
        return 'UNIFIQUE', 'UNIFIQUE', 'Pequeno Porte', 'MNO'
    if 'VERO' in emp or 'VERO' in grp:
        return 'VERO', 'VERO', 'Pequeno Porte', 'MNO'
    if 'LIGGA' in emp or 'LIGGA' in grp or 'COPEL' in grp or 'LONDRINA' in grp:
        return 'LIGGA TELECOM', 'LIGGA TELECOM', 'Pequeno Porte', 'MNO'
        
    
    if 'SURF' in emp or 'SURF' in grp:
        return 'SURF TELECOM', 'SURF TELECOM', 'Pequeno Porte', 'MVNO'
    if 'TELECALL' in emp or 'TELECALL' in grp:
        return 'TELECALL', 'TELECALL', 'Pequeno Porte', 'MVNO'
    if 'DATORA' in emp or 'DATORA' in grp or 'VODAFONE' in emp or 'ARQIA' in emp:
        return 'DATORA', 'DATORA', 'Pequeno Porte', 'MVNO'
    if '1NCE' in emp or '1NCE' in grp:
        return '1NCE', '1NCE', 'Pequeno Porte', 'MVNO'
    if 'EMNIFY' in emp or 'EMNIFY' in grp:
        return 'EMNIFY BRASIL', 'EMNIFY BRASIL', 'Pequeno Porte', 'MVNO'
    if 'TRANSATEL' in emp or 'TRANSATEL' in grp:
        return 'TRANSATEL BRASIL LTDA', 'TRANSATEL BRASIL LTDA', 'Pequeno Porte', 'MVNO'
    if 'AIRNITY' in emp or 'AIRNITY' in grp:
        return 'AIRNITY BRASIL', 'AIRNITY BRASIL', 'Pequeno Porte', 'MVNO'
    if 'NEXT LEVEL' in emp or 'NLT' in emp or 'NEXT LEVEL' in grp:
        return 'NLT', 'NLT', 'Pequeno Porte', 'MVNO'
    if 'PORTO SEGURO' in emp or 'PORTO SEGURO' in grp:
        return 'PORTO SEGURO', 'PORTO SEGURO', 'Pequeno Porte', 'MVNO'
    if 'AMERICA NET' in emp or 'AMERICA NET' in grp or 'AMERICAS NET' in emp:
        return 'AMERICA NET', 'AMERICA NET', 'Pequeno Porte', 'MVNO'
    
    tipo = 'MNO' if 'GRANDE' in prt else 'MVNO'
    return empresa or 'OUTROS', grupo or 'OUTROS', porte or 'Pequeno Porte', tipo

def print_preview(name, headers, rows):
    """Exibe uma tabela limpa e formatada das 5 primeiras linhas."""
    print("=" * 100)
    print(f" PRÉ-VISUALIZAÇÃO DO RELATÓRIO: {name} (Primeiras 5 linhas)")
    print("=" * 100)
    
    col_widths = []
    for i, h in enumerate(headers):
        max_w = len(h)
        for r in rows[:5]:
            max_w = max(max_w, len(str(r[i])))
        col_widths.append(min(max_w, 25))
        

    header_str = " | ".join(f"{h:<{col_widths[i]}}"[:col_widths[i]] for i, h in enumerate(headers))
    print(header_str)
    print("-" * len(header_str))
    

    for r in rows[:5]:
        row_str = " | ".join(f"{str(item):<{col_widths[i]}}"[:col_widths[i]] for i, item in enumerate(r))
        print(row_str)
    print("\n")

def generate_calendar(start_year=2005, end_year=2026):

    months_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    calendar_rows = []
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        year = current_date.year
        month = current_date.month
        month_name = months_pt[month]
        q = f"Q{(month - 1) // 3 + 1}"
        calendar_rows.append([date_str, year, month, month_name, q])
        current_date += timedelta(days=1)
        
    return calendar_rows

def get_prev_month_str(date_str):
    # date_str is "YYYY-MM-01"
    parts = date_str.split('-')
    year = int(parts[0])
    month = int(parts[1])
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    return f"{prev_year}-{prev_month:02d}-01"

def get_region(uf):
    uf = str(uf).strip().upper()
    if uf in ["AC", "AP", "AM", "PA", "RO", "RR", "TO"]:
        return "Norte"
    elif uf in ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]:
        return "Nordeste"
    elif uf in ["DF", "GO", "MT", "MS"]:
        return "Centro-Oeste"
    elif uf in ["ES", "MG", "RJ", "SP"]:
        return "Sudeste"
    elif uf in ["PR", "RS", "SC"]:
        return "Sul"
    else:
        return "Não Informado"

def check_anatel_update(url):
    print("Verificando se há atualizações no servidor da Anatel...")
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        with urllib.request.urlopen(req, timeout=10) as response:
            headers = response.info()
            last_modified_str = headers.get('Last-Modified')
            if last_modified_str:
                parsed_date = email.utils.parsedate_to_datetime(last_modified_str)
                now = datetime.now(parsed_date.tzinfo)
                diff = now - parsed_date
                return diff.days <= 15, parsed_date, diff.days
    except Exception as e:
        print(f"Aviso: Não foi possível checar atualizações online ({e}).")
    return False, None, None

def download_file_with_progress(url, dest_path):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    try:
        with urllib.request.urlopen(req) as response:
            total_size = int(response.info().get('Content-Length', 0))
            bytes_downloaded = 0
            block_size = 1024 * 1024  # 1MB blocks
            
            print(f"Baixando base de dados da Anatel ({total_size / (1024*1024*1024):.2f} GB)...")
            with open(dest_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    bytes_downloaded += len(buffer)
                    f.write(buffer)
                    
                    percent = (bytes_downloaded / total_size) * 100 if total_size else 0
                    sys.stdout.write(f"\rProgresso: {percent:.2f}% ({bytes_downloaded / (1024*1024):.1f} MB de {total_size / (1024*1024):.1f} MB)")
                    sys.stdout.flush()
            print("\nDownload concluído com sucesso!")
            return True
    except Exception as e:
        print(f"\nErro durante o download: {e}")
        return False

def extract_zip(zip_path, extract_to):
    print(f"Extraindo arquivos compactados em '{extract_to}'...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            total_files = len(file_list)
            for i, file in enumerate(file_list, 1):
                zip_ref.extract(file, extract_to)
                percent = (i / total_files) * 100
                sys.stdout.write(f"\rProgresso da extração: {percent:.2f}% ({i}/{total_files} arquivos)")
                sys.stdout.flush()
        print("\nExtração de arquivos concluída!")
        return True
    except Exception as e:
        print(f"\nErro durante a extração: {e}")
        return False

def main():
    print("==================================================================================")
    print("              ANATEL M2M & POS DATA CONSOLIDATOR FOR POWER BI                     ")
    print("==================================================================================")
    
    is_auto = "--auto" in sys.argv
    url_anatel = "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/acessos/acessos_telefonia_movel.zip"
    houve_atualizacao, data_mod, dias_atras = check_anatel_update(url_anatel)
    
    folder = None
    
    if is_auto:
        print("\n[MODO AUTOMÁTICO] Executando sem interação do usuário.")
        folder = os.path.join(os.getcwd(), "Bases", "Dados Anatel", "acessos_telefonia_movel")
        
        if houve_atualizacao:
            print(f"Atualização detectada no servidor da Anatel ({dias_atras} dias atrás). Iniciando atualização da base local...")
            if os.path.exists(folder):
                print(f"Apagando conteúdo da pasta antiga: {folder}...")
                try:
                    shutil.rmtree(folder)
                except Exception as e:
                    print(f"Aviso: Não foi possível limpar toda a pasta ({e}). Tentando prosseguir...")
            os.makedirs(folder, exist_ok=True)
            
            zip_temp = os.path.join(folder, "acessos_telefonia_movel_temp.zip")
            success = download_file_with_progress(url_anatel, zip_temp)
            if success:
                success_extract = extract_zip(zip_temp, folder)
                if os.path.exists(zip_temp):
                    os.remove(zip_temp)
                if not success_extract:
                    print("Erro ao extrair a base de dados.")
                    sys.exit(1)
            else:
                if os.path.exists(zip_temp):
                    os.remove(zip_temp)
                print("Erro ao realizar o download. Abortando.")
                sys.exit(1)
        else:
            if data_mod:
                print(f"Base da Anatel sem atualizações recentes (última modificação há {dias_atras} dias). Usando base local.")
            else:
                print("Não foi possível verificar atualizações ou não há atualizações nos últimos 15 dias. Usando base local.")
                
    else:
        if houve_atualizacao:
            print(f"\n[ATENÇÃO] A base de dados da Anatel foi atualizada no servidor há {dias_atras} dias ({data_mod.strftime('%d/%m/%Y %H:%M:%S')}).")
            escolha = input("Deseja baixar e atualizar sua base local? (S/N): ").strip().upper()
            
            if escolha in ["S", "SIM"]:
                print("\n1. SELEÇÃO DA PASTA DE DESTINO PARA ATUALIZAÇÃO")
                folder = select_folder("Selecione a pasta onde os arquivos serão descompactados", "Digite o caminho da pasta")
                if not folder:
                    print("Operação cancelada pelo usuário.")
                    sys.exit(0)
                    
                cwd = os.getcwd()
                if os.path.abspath(folder) == os.path.abspath(cwd):
                    print("Erro: A pasta de destino não pode ser o diretório atual de execução para evitar perda de código.")
                    sys.exit(1)
                    
                if os.path.exists(folder):
                    print(f"Apagando conteúdo da pasta antiga: {folder}...")
                    try:
                        shutil.rmtree(folder)
                    except Exception as e:
                        print(f"Aviso: Não foi possível limpar toda a pasta ({e}). Tentando prosseguir...")
                os.makedirs(folder, exist_ok=True)
                
                zip_temp = os.path.join(folder, "acessos_telefonia_movel_temp.zip")
                success = download_file_with_progress(url_anatel, zip_temp)
                if success:
                    success_extract = extract_zip(zip_temp, folder)
                    if os.path.exists(zip_temp):
                        os.remove(zip_temp)
                    if not success_extract:
                        print("Erro ao extrair a base de dados.")
                        sys.exit(1)
                else:
                    if os.path.exists(zip_temp):
                        os.remove(zip_temp)
                    print("Erro ao realizar o download. Abortando.")
                    sys.exit(1)
            else:
                print("\nUsando base de dados local existente.")
                
        else:
            if data_mod:
                print(f"\nA base de dados da Anatel foi modificada pela última vez em {data_mod.strftime('%d/%m/%Y %H:%M:%S')} (há {dias_atras} dias).")
                print("Não há atualizações recentes no servidor da Anatel nos últimos 15 dias.")
            else:
                print("\nNão foi possível verificar atualizações ou não há atualizações nos últimos 15 dias.")
                
        if not folder:
            print("\n1. SELEÇÃO DA PASTA DE ORIGEM (DADOS BRUTOS)")
            folder = select_folder("Selecione a pasta com os arquivos da ANATEL", "Digite o caminho da pasta contendo os arquivos")
        
    if not os.path.exists(folder):
        print(f"Erro: A pasta '{folder}' não foi encontrada.")
        sys.exit(1)
        
    print(f"\nBuscando arquivos da ANATEL na pasta: {folder}\n")
    

    hist_file = glob.glob(os.path.join(folder, "*2005-2018_Tecnologia.csv"))
    colunas_files = sorted(glob.glob(os.path.join(folder, "*_Colunas.csv")))
    

    colunas_files = [f for f in colunas_files if "2005-2009" not in f and "200902-2018" not in f]
    
    if not hist_file and not colunas_files:
        print("Aviso: Nenhum arquivo compatível com ANATEL foi encontrado na pasta selecionada.")
        print("Certifique-se de que os arquivos extraídos estão na pasta correta.")
        sys.exit(1)
        

    # Chave para Fato Detalhada: (Data, Cod_IBGE, UF, Municipio, Empresa, Tipo_Produto, Tipo_Pessoa) -> Acessos
    fato_detalhada = defaultdict(int)
    

    operadoras_unicas = set()
    

    if hist_file:
        file_path = hist_file[0]
        print(f"1/2. Lendo arquivo histórico: {os.path.basename(file_path)}...")
        with open(file_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
           
            first_line = f.readline()
            delim = ';' if ';' in first_line else ','
            f.seek(0)
            
            reader = csv.DictReader(f, delimiter=delim)
            count = 0
            for row in reader:
                tec = str(row.get('Tecnologia', '')).strip().upper()
                if 'M2M' in tec:
                    # Classifica
                    emp, grp, porte, tipo_op = classify_operator(
                        row.get('Empresa', ''),
                        row.get('Grupo Econômico', ''),
                        row.get('Porte da Prestadora', '')
                    )
                    operadoras_unicas.add((emp, grp, row.get('Porte da Prestadora', 'Pequeno Porte'), tipo_op))
                    
                    # Converte data
                    ano = row.get('Ano', '')
                    mes = row.get('Mês', '')
                    if not ano or not mes:
                        continue
                    date_str = f"{ano}-{int(mes):02d}-01"
                    
                    # Acessos
                    try:
                        acessos = int(row.get('Acessos', 0))
                    except ValueError:
                        continue
                        
                    if acessos > 0:
                        
                        chave = (date_str, "Não Informado", row.get('UF', ''), "Não Informado", emp, "M2M", "Pessoa Jurídica")
                        fato_detalhada[chave] += acessos
                        count += 1
            print(f"   -> {count:,} registros de M2M importados do histórico.")
    else:
        print("1/2. Arquivo histórico (2005-2018) não encontrado. Pulando...")
        
  
    if colunas_files:
        print(f"2/2. Lendo {len(colunas_files)} arquivos semestrais pivotados (*_Colunas.csv)...")
        for file_path in colunas_files:
            file_name = os.path.basename(file_path)
            print(f"   - Processando: {file_name}...")
            
            with open(file_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
                first_line = f.readline()
                delim = ';' if ';' in first_line else ','
                f.seek(0)
                
                reader = csv.DictReader(f, delimiter=delim)
                
         
                fieldnames = reader.fieldnames
                fixed_fields = {
                    'CNPJ', 'Código Nacional', 'Município', 'UF', 'Modalidade de Cobrança',
                    'Tecnologia', 'Tecnologia Geração', 'Empresa', 'Porte da Prestadora',
                    'Tipo de Pessoa', 'Tipo de Produto', 'Código IBGE Município', 'Grupo Econômico'
                }
                month_cols = [col for col in fieldnames if col not in fixed_fields and '-' in col]
                
                count_file = 0
                for row in reader:
                    prod = str(row.get('Tipo de Produto', '')).strip().upper()
                    
                    # Filtra apenas M2M e POS (Ponto de Serviço) usando busca parcial
                    if 'M2M' in prod or 'PONTO' in prod:
                        # Normaliza nome do produto
                        prod_norm = 'POS' if 'PONTO' in prod else 'M2M'
                        
                        # Classifica operadora
                        emp, grp, porte, tipo_op = classify_operator(
                            row.get('Empresa', ''),
                            row.get('Grupo Econômico', ''),
                            row.get('Porte da Prestadora', '')
                        )
                        operadoras_unicas.add((emp, grp, row.get('Porte da Prestadora', 'Pequeno Porte'), tipo_op))
                        
                        # Pega campos espaciais e demográficos
                        cod_ibge = row.get('Código IBGE Município', 'Não Informado')
                        uf = row.get('UF', '')
                        mun = row.get('Município', 'Não Informado')
                        tipo_pess = row.get('Tipo de Pessoa', 'Pessoa Jurídica')
                        
                        # Despivota os acessos mensais
                        for m_col in month_cols:
                            acc_val = row.get(m_col, '')
                            if not acc_val:
                                continue
                            try:
                                acessos = int(acc_val)
                            except ValueError:
                                continue
                                
                            if acessos > 0:
                                date_str = f"{m_col}-01"
                                chave = (date_str, cod_ibge, uf, mun, emp, prod_norm, tipo_pess)
                                fato_detalhada[chave] += acessos
                                count_file += 1
                print(f"     -> {count_file:,} registros extraídos.")
    else:
        print("2/2. Nenhum arquivo semestral pivotado (*_Colunas.csv) encontrado.")

    if not fato_detalhada:
        print("\nErro: Nenhum dado de M2M/POS pôde ser processado. Verifique os arquivos.")
        sys.exit(1)
        
    print("\n--- Processamento em Memória Concluído! ---")
    print(f"Total de registros na tabela fato detalhada: {len(fato_detalhada):,}")
    
  
    # Colunas: Data, Codigo_IBGE, Regiao, UF, Municipio, Empresa, Tipo_Produto, Tipo_Pessoa, Acessos
    rows_fato = []
    for chave, acessos in fato_detalhada.items():
        # chave: (date_str, cod_ibge, uf, mun, emp, prod_norm, tipo_pess)
        uf = chave[2]
        regiao = get_region(uf)
        row = list(chave)
        row.insert(2, regiao)
        rows_fato.append(row + [acessos])
    rows_fato.sort(key=lambda x: (x[0], x[2], x[3], x[4], x[5], x[6]))
    headers_fato = ["Data", "Codigo_IBGE", "Regiao", "UF", "Municipio", "Empresa", "Tipo_Produto", "Tipo_Pessoa", "Acessos"]
    
    # 2. Resumo por Estado (UF)
    # Colunas: Data, Regiao, UF, Empresa, Tipo_Produto, Acessos
    resumo_uf = defaultdict(int)
    for r in rows_fato:
        # r: Data, Codigo_IBGE, Regiao, UF, Municipio, Empresa, Tipo_Produto, Tipo_Pessoa, Acessos
        resumo_uf[(r[0], r[2], r[3], r[5], r[6])] += r[8]
    rows_uf = [list(k) + [v] for k, v in resumo_uf.items()]
    rows_uf.sort(key=lambda x: (x[0], x[1], x[2], x[3], x[4]))
    headers_uf = ["Data", "Regiao", "UF", "Empresa", "Tipo_Produto", "Acessos"]
    
    # 3. Resumo Operadora (Market Share)
    # Colunas: Data, Empresa, Grupo_Economico, Porte, Tipo_Operadora, Tipo_Produto, Acessos
    # Precisamos mapear o grupo_economico e porte correto
    op_map = {op[0]: op for op in operadoras_unicas}
    resumo_ms = defaultdict(int)
    for r in rows_fato:
        # r: Data, Codigo_IBGE, Regiao, UF, Municipio, Empresa, Tipo_Produto, Tipo_Pessoa, Acessos
        emp = r[5]
        op_info = op_map.get(emp, (emp, "OUTROS", "Pequeno Porte", "MVNO"))
        # op_info: Empresa, Grupo, Porte, Tipo_Operadora
        resumo_ms[(r[0], emp, op_info[1], op_info[2], op_info[3], r[6])] += r[8]
    rows_ms = [list(k) + [v] for k, v in resumo_ms.items()]
    rows_ms.sort(key=lambda x: (x[0], x[4], -x[6]))
    headers_ms = ["Data", "Empresa", "Grupo_Economico", "Porte", "Tipo_Operadora", "Tipo_Produto", "Acessos"]
    
    # 4. Dimensão Operadora
    # Colunas: Empresa, Grupo_Economico, Porte, Tipo_Operadora
    rows_op = [list(op) for op in operadoras_unicas]
    rows_op.sort(key=lambda x: (x[3], x[0]))
    headers_op = ["Empresa", "Grupo_Economico", "Porte", "Tipo_Operadora"]
    
    # 5. Dimensão Calendário
    # Colunas: Data, Ano, Mes, Nome_Mes, Trimestre
    rows_cal = generate_calendar(2005, 2026)
    headers_cal = ["Data", "Ano", "Mes", "Nome_Mes", "Trimestre"]
    
    # 6. Resumo para Gráfico de Cascata (Waterfall)
    # Colunas: Data, Empresa, Grupo_Economico, Porte, Tipo_Operadora, Tipo_Produto, Acessos_Atual, Acessos_Anterior, Variacao
    resumo_wf = []
    for k, acessos in resumo_ms.items():
        # k: (Data, Empresa, Grupo_Economico, Porte, Tipo_Operadora, Tipo_Produto)
        date_str, emp, grp, porte_op, tipo_op, prod = k
        prev_date_str = get_prev_month_str(date_str)
        
        # Procura acessos no mês anterior
        prev_key = (prev_date_str, emp, grp, porte_op, tipo_op, prod)
        acessos_anterior = resumo_ms.get(prev_key, 0)
        
        variacao = acessos - acessos_anterior
        
        # Só incluímos se houve acessos no período atual ou anterior para não encher de zeros
        if acessos > 0 or acessos_anterior > 0:
            resumo_wf.append([date_str, emp, grp, porte_op, tipo_op, prod, acessos, acessos_anterior, variacao])
            
    resumo_wf.sort(key=lambda x: (x[0], x[4], -x[8])) # Ordena por Data, Tipo Operadora e decrescente pela variação
    headers_wf = ["Data", "Empresa", "Grupo_Economico", "Porte", "Tipo_Operadora", "Tipo_Produto", "Acessos_Atual", "Acessos_Anterior", "Variacao"]
    
    # 7. Resumo Geográfico por Município (para mapas)
    # Colunas: Data, Codigo_IBGE, Municipio, UF, Localizacao_Mapa, Tipo_Produto, Acessos
    resumo_mun = defaultdict(int)
    for r in rows_fato:
        # r: Data, Codigo_IBGE, Regiao, UF, Municipio, Empresa, Tipo_Produto, Tipo_Pessoa, Acessos
        cod_ibge = r[1]
        uf = r[3]
        mun = r[4]
        if mun != "Não Informado":
            resumo_mun[(r[0], cod_ibge, uf, mun, r[6])] += r[8]
            
    state_names = {
        "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
        "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
        "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
        "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
        "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
        "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
        "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
    }
            
    rows_mun = []
    for k, v in resumo_mun.items():
        # k: Data, Codigo_IBGE, UF, Municipio, Tipo_Produto
        date_str, cod, uf, mun, prod = k
        
        # Normalização de nomes de municípios para evitar erros de geolocalização no Bing Maps
        mun_norm = mun.strip()
        mun_upper = mun_norm.upper()
        if (mun_upper.startswith("DUAR") or mun_upper.startswith("DUER")) and len(mun_norm) <= 7:
            mun_norm = "Dueré"
            
        state_full = state_names.get(uf, uf)
        loc_mapa = f"{mun_norm}, {state_full} - Brasil"
        rows_mun.append([date_str, cod, mun, uf, loc_mapa, prod, v])
        
    rows_mun.sort(key=lambda x: (x[0], x[3], x[2], x[5]))
    headers_mun = ["Data", "Codigo_IBGE", "Municipio", "UF", "Localizacao_Mapa", "Tipo_Produto", "Acessos"]
    
    # EXIBIR PRÉ-VISUALIZAÇÃO DE TODOS
    print("\n")
    print_preview("1 - Fato Acessos Detalhado (Municípios)", headers_fato, rows_fato)
    print_preview("2 - Resumo Geográfico por Estado (UF)", headers_uf, rows_uf)
    print_preview("3 - Resumo Operadoras (Market Share)", headers_ms, rows_ms)
    print_preview("4 - Dimensão Operadora", headers_op, rows_op)
    print_preview("5 - Dimensão Calendário", headers_cal, rows_cal)
    print_preview("6 - Resumo para Cascata (Waterfall)", headers_wf, resumo_wf)
    print_preview("7 - Resumo Geográfico por Município (Mapas)", headers_mun, rows_mun)
    
    # DETERMINA GERAÇÃO E DESTINO DOS RELATÓRIOS
    if is_auto:
        print("\n[MODO AUTOMÁTICO] Gerando todos os 7 relatórios por padrão.")
        generate_all = True
        selected_indices = set()
        out_folder = os.path.join(os.getcwd(), "Bases") # Salva na subpasta Bases
    else:
        # SOLICITAR ENTRADA DO USUÁRIO
        print("==================================================================================")
        print(" SELEÇÃO DE RELATÓRIOS A SEREM GERADOS")
        print("==================================================================================")
        print(" [1] Fato Acessos Detalhado (fato_acessos_m2m_pos.csv)")
        print(" [2] Resumo Geográfico por Estado (resumo_uf_m2m_pos.csv)")
        print(" [3] Resumo Operadoras (market_share_m2m_pos.csv)")
        print(" [4] Dimensão Operadora (dim_operadora.csv)")
        print(" [5] Dimensão Calendário (dim_calendario.csv)")
        print(" [6] Resumo para Cascata (resumo_waterfall_m2m_pos.csv)")
        print(" [7] Resumo Geográfico por Município (resumo_municipio_m2m_pos.csv)")
        print("----------------------------------------------------------------------------------")
        print(" Como selecionar:")
        print("   - Digite números separados por vírgula para relatórios específicos (ex: 1,3,4)")
        print("   - Digite 'Todos' ou deixe em BRANCO (pressione Enter) para gerar todos os 7.")
        print("==================================================================================")
        
        selection = input("\nSelecione os relatórios a serem gerados: ").strip()
        
        # Determina quais serão gerados
        generate_all = not selection or selection.lower() == 'todos'
        selected_indices = set()
        
        if not generate_all:
            try:
                for x in selection.split(','):
                    idx = int(x.strip())
                    if 1 <= idx <= 7:
                        selected_indices.add(idx)
            except ValueError:
                print("Entrada inválida. Gerando TODOS os relatórios por padrão.")
                generate_all = True
                
        print("\n2. SELEÇÃO DA PASTA DE DESTINO (RELATÓRIOS PARA POWER BI)")
        out_folder = select_folder("Selecione a pasta para SALVAR os relatórios", "Digite a pasta de destino")
        
    if not os.path.exists(out_folder):
        print(f"Criando a pasta de destino: {out_folder}")
        os.makedirs(out_folder)
        
    # Função para salvar CSV com ponto e vírgula
    def save_csv(filename, headers, rows):
        target_path = os.path.join(out_folder, filename)
        
        # Exclui o arquivo antigo específico se ele já existir, antes de gravar o novo
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception as e:
                print(f"   Aviso: Não foi possível excluir o arquivo antigo {filename}. Ele pode estar aberto no Power BI.")
                
        print(f"   -> Salvando: {filename}...")
        with open(target_path, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(headers)
            writer.writerows(rows)
            
    print("\nIniciando gravação dos relatórios...")
    
    # Grava conforme seleção
    if generate_all or 1 in selected_indices:
        save_csv("fato_acessos_m2m_pos.csv", headers_fato, rows_fato)
    if generate_all or 2 in selected_indices:
        save_csv("resumo_uf_m2m_pos.csv", headers_uf, rows_uf)
    if generate_all or 3 in selected_indices:
        save_csv("market_share_m2m_pos.csv", headers_ms, rows_ms)
    if generate_all or 4 in selected_indices:
        save_csv("dim_operadora.csv", headers_op, rows_op)
    if generate_all or 5 in selected_indices:
        save_csv("dim_calendario.csv", headers_cal, rows_cal)
    if generate_all or 6 in selected_indices:
        save_csv("resumo_waterfall_m2m_pos.csv", headers_wf, resumo_wf)
    if generate_all or 7 in selected_indices:
        save_csv("resumo_municipio_m2m_pos.csv", headers_mun, rows_mun)
        
    print("\n==================================================================================")
    print("          SUCESSO! Os relatórios selecionados foram salvos na pasta.              ")
    print("          Você já pode abrir o Power BI e carregar estes arquivos!               ")
    print("==================================================================================")

if __name__ == "__main__":
    main()
