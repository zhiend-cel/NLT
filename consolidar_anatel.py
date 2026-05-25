#!/usr/bin/env python3
import os
import csv
import glob
import sys
from collections import defaultdict

def select_folder():
    """Permite selecionar a pasta graficamente ou por texto."""
    print("Iniciando o selecionador de pastas...")
    # Tenta usar o Tkinter para abrir uma janela gráfica
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()  # Oculta a janela principal do Tkinter
        # Tenta trazer para o primeiro plano
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title="Selecione a pasta com os arquivos da ANATEL")
        if folder:
            return folder
    except Exception as e:
        # Se falhar (ambiente sem tela/headless ou sem tkinter), usa entrada de texto
        pass
    
    # Fallback para entrada de texto
    print("\n--- Seleção Manual de Pasta (Interface Gráfica Não Disponível) ---")
    current_dir = os.getcwd()
    print(f"Diretório atual: {current_dir}")
    folder = input("Digite o caminho da pasta contendo os arquivos (pressione Enter para usar o diretório atual): ").strip()
    if not folder:
        return current_dir
    return folder

def classify_operator(empresa, grupo, porte):
    """Mapeia operadoras da ANATEL em MNO Nacional, MNO Regional ou MVNO."""
    emp = str(empresa).upper().strip()
    grp = str(grupo).upper().strip()
    prt = str(porte).upper().strip()
    
    # 1. Grandes MNOs Nacionais
    if 'TELEFONICA' in emp or 'VIVO' in emp or 'TELEFÔNICA' in emp or 'VIVO' in grp or 'TELEFONICA' in grp:
        return 'VIVO', 'TELEFÔNICA', 'Grande Porte', 'MNO Nacional'
    if 'CLARO' in emp or 'TELECOM AMERICAS' in grp or 'TELECOM AMÉRICAS' in grp:
        return 'CLARO', 'TELECOM AMERICAS', 'Grande Porte', 'MNO Nacional'
    if 'TIM' in emp or 'TELECOM ITALIA' in grp:
        return 'TIM', 'TELECOM ITALIA', 'Grande Porte', 'MNO Nacional'
    if 'OI' in emp or 'OI' in grp:
        return 'OI', 'OI', 'Grande Porte', 'MNO Nacional'
    if 'NEXTEL' in emp or 'NEXTEL' in grp:
        return 'NEXTEL', 'NEXTEL', 'Grande Porte', 'MNO Nacional'

    # 2. MNOs Regionais / Entrantes (PPP de rede própria)
    if 'ALGAR' in emp or 'CTBC' in emp or 'ALGAR' in grp:
        return 'ALGAR (CTBC TELECOM)', 'ALGAR (CTBC TELECOM)', 'Pequeno Porte', 'MNO Regional'
    if 'BRISANET' in emp or 'BRISANET' in grp:
        return 'BRISANET', 'BRISANET', 'Pequeno Porte', 'MNO Regional'
    if 'UNIFIQUE' in emp or 'UNIFIQUE' in grp:
        return 'UNIFIQUE', 'UNIFIQUE', 'Pequeno Porte', 'MNO Regional'
    if 'VERO' in emp or 'VERO' in grp:
        return 'VERO', 'VERO', 'Pequeno Porte', 'MNO Regional'
    if 'LIGGA' in emp or 'LIGGA' in grp or 'COPEL' in grp or 'LONDRINA' in grp:
        return 'LIGGA TELECOM', 'LIGGA TELECOM', 'Pequeno Porte', 'MNO Regional'
        
    # 3. MVNOs Tradicionais e de IoT
    if 'SURF' in emp or 'SURF' in grp:
        return 'SURF TELECOM', 'SURF TELECOM', 'Pequeno Porte', 'MVNO'
    if 'TELECALL' in emp or 'TELECALL' in grp:
        return 'Telecall', 'Telecall', 'Pequeno Porte', 'MVNO'
    if 'DATORA' in emp or 'DATORA' in grp or 'VODAFONE' in emp or 'ARQIA' in emp:
        return 'DATORA', 'DATORA', 'Pequeno Porte', 'MVNO IoT'
    if '1NCE' in emp or '1NCE' in grp:
        return '1NCE', '1NCE', 'Pequeno Porte', 'MVNO IoT'
    if 'EMNIFY' in emp or 'EMNIFY' in grp:
        return 'EMNIFY BRASIL', 'EMNIFY BRASIL', 'Pequeno Porte', 'MVNO IoT'
    if 'TRANSATEL' in emp or 'TRANSATEL' in grp:
        return 'TRANSATEL BRASIL LTDA', 'TRANSATEL BRASIL LTDA', 'Pequeno Porte', 'MVNO IoT'
    if 'AIRNITY' in emp or 'AIRNITY' in grp:
        return 'AIRNITY BRASIL', 'AIRNITY BRASIL', 'Pequeno Porte', 'MVNO IoT'
    if 'NEXT LEVEL' in emp or 'NLT' in emp or 'NEXT LEVEL' in grp:
        return 'Next Level Telecom', 'Next Level Telecom', 'Pequeno Porte', 'MVNO IoT'
    if 'PORTO SEGURO' in emp or 'PORTO SEGURO' in grp:
        return 'PORTO SEGURO', 'PORTO SEGURO', 'Pequeno Porte', 'MVNO'
    if 'AMERICA NET' in emp or 'AMERICA NET' in grp or 'AMERICAS NET' in emp:
        return 'AMERICA NET', 'AMERICA NET', 'Pequeno Porte', 'MVNO'
    
    # Fallback inteligente com base no Porte
    tipo = 'MNO Nacional' if 'GRANDE' in prt else 'MVNO'
    return empresa or 'OUTROS', grupo or 'OUTROS', porte or 'Pequeno Porte', tipo

def print_preview(name, headers, rows):
    """Exibe uma tabela limpa e formatada das 5 primeiras linhas."""
    print("=" * 100)
    print(f" PRÉ-VISUALIZAÇÃO DO RELATÓRIO: {name} (Primeiras 5 linhas)")
    print("=" * 100)
    
    # Calcula a largura máxima de cada coluna (com limite de 25 caracteres para não quebrar a tela)
    col_widths = []
    for i, h in enumerate(headers):
        max_w = len(h)
        for r in rows[:5]:
            max_w = max(max_w, len(str(r[i])))
        col_widths.append(min(max_w, 25))
        
    # Imprime cabeçalho
    header_str = " | ".join(f"{h:<{col_widths[i]}}"[:col_widths[i]] for i, h in enumerate(headers))
    print(header_str)
    print("-" * len(header_str))
    
    # Imprime linhas
    for r in rows[:5]:
        row_str = " | ".join(f"{str(item):<{col_widths[i]}}"[:col_widths[i]] for i, item in enumerate(r))
        print(row_str)
    print("\n")

def generate_calendar(start_year=2005, end_year=2026):
    """Gera dados da tabela de dimensão calendário."""
    months_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    calendar_rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            date_str = f"{year}-{month:02d}-01"
            q = f"Q{(month - 1) // 3 + 1}"
            calendar_rows.append([date_str, year, month, months_pt[month], q])
    return calendar_rows

def main():
    print("==================================================================================")
    print("              ANATEL M2M & POS DATA CONSOLIDATOR FOR POWER BI                     ")
    print("==================================================================================")
    
    folder = select_folder()
    if not os.path.exists(folder):
        print(f"Erro: A pasta '{folder}' não foi encontrada.")
        sys.exit(1)
        
    print(f"\nBuscando arquivos da ANATEL na pasta: {folder}\n")
    
    # Busca arquivos históricos e modernos
    hist_file = glob.glob(os.path.join(folder, "*2005-2018_Tecnologia.csv"))
    colunas_files = sorted(glob.glob(os.path.join(folder, "*_Colunas.csv")))
    
    # Remove histórico de colunas para não duplicar se houver
    colunas_files = [f for f in colunas_files if "2005-2009" not in f and "200902-2018" not in f]
    
    if not hist_file and not colunas_files:
        print("Aviso: Nenhum arquivo compatível com ANATEL foi encontrado na pasta selecionada.")
        print("Certifique-se de que os arquivos extraídos estão na pasta correta.")
        sys.exit(1)
        
    # Estruturas para consolidação na memória
    # Chave para Fato Detalhada: (Data, Cod_IBGE, UF, Municipio, Empresa, Tipo_Produto, Tipo_Pessoa) -> Acessos
    fato_detalhada = defaultdict(int)
    
    # Cadastro de operadoras único
    operadoras_unicas = set()
    
    # 1. PROCESSAR HISTÓRICO (2005-2018)
    if hist_file:
        file_path = hist_file[0]
        print(f"1/2. Lendo arquivo histórico: {os.path.basename(file_path)}...")
        with open(file_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
            # Tenta descobrir o delimitador
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
                        # Histórico só vai até nível de UF, marcamos Município como "Não Informado"
                        chave = (date_str, "Não Informado", row.get('UF', ''), "Não Informado", emp, "M2M", "Pessoa Jurídica")
                        fato_detalhada[chave] += acessos
                        count += 1
            print(f"   -> {count:,} registros de M2M importados do histórico.")
    else:
        print("1/2. Arquivo histórico (2005-2018) não encontrado. Pulando...")
        
    # 2. PROCESSAR PERÍODO SEMESTRAL (2019-2026)
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
                
                # Identifica colunas mensais de dados (ex: '2024-01', '2024-02')
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
                    
                    # Filtra apenas M2M e POS (Ponto de Serviço)
                    if prod in ('M2M', 'PONTO_DE_SERVICO', 'PONTO_DE_SERVIÇO'):
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
    
    # GERAR OS DADOS DOS 5 RELATÓRIOS PARA PRÉVIA
    
    # 1. Tabela Fato Detalhada (Municípios)
    # Colunas: Data, Codigo_IBGE, UF, Municipio, Empresa, Tipo_Produto, Tipo_Pessoa, Acessos
    rows_fato = []
    for chave, acessos in fato_detalhada.items():
        rows_fato.append(list(chave) + [acessos])
    rows_fato.sort(key=lambda x: (x[0], x[2], x[3], x[4], x[5]))
    headers_fato = ["Data", "Codigo_IBGE", "UF", "Municipio", "Empresa", "Tipo_Produto", "Tipo_Pessoa", "Acessos"]
    
    # 2. Resumo por Estado (UF)
    # Colunas: Data, UF, Empresa, Tipo_Produto, Acessos
    resumo_uf = defaultdict(int)
    for r in rows_fato:
        # r: Data, Codigo_IBGE, UF, Municipio, Empresa, Tipo_Produto, Tipo_Pessoa, Acessos
        resumo_uf[(r[0], r[2], r[4], r[5])] += r[7]
    rows_uf = [list(k) + [v] for k, v in resumo_uf.items()]
    rows_uf.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    headers_uf = ["Data", "UF", "Empresa", "Tipo_Produto", "Acessos"]
    
    # 3. Resumo Operadora (Market Share)
    # Colunas: Data, Empresa, Grupo_Economico, Porte, Tipo_Operadora, Tipo_Produto, Acessos
    # Precisamos mapear o grupo_economico e porte correto
    op_map = {op[0]: op for op in operadoras_unicas}
    resumo_ms = defaultdict(int)
    for r in rows_fato:
        # r: Data, Codigo_IBGE, UF, Municipio, Empresa, Tipo_Produto, Tipo_Pessoa, Acessos
        emp = r[4]
        op_info = op_map.get(emp, (emp, "OUTROS", "Pequeno Porte", "MVNO"))
        # op_info: Empresa, Grupo, Porte, Tipo_Operadora
        resumo_ms[(r[0], emp, op_info[1], op_info[2], op_info[3], r[5])] += r[7]
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
    
    # EXIBIR PRÉ-VISUALIZAÇÃO DE TODOS
    print("\n")
    print_preview("1 - Fato Acessos Detalhado (Municípios)", headers_fato, rows_fato)
    print_preview("2 - Resumo Geográfico por Estado (UF)", headers_uf, rows_uf)
    print_preview("3 - Resumo Operadoras (Market Share)", headers_ms, rows_ms)
    print_preview("4 - Dimensão Operadora", headers_op, rows_op)
    print_preview("5 - Dimensão Calendário", headers_cal, rows_cal)
    
    # SOLICITAR ENTRADA DO USUÁRIO
    print("==================================================================================")
    print(" SELEÇÃO DE RELATÓRIOS A SEREM GERADOS")
    print("==================================================================================")
    print(" [1] Fato Acessos Detalhado (fato_acessos_m2m_pos.csv)")
    print(" [2] Resumo Geográfico por Estado (resumo_uf_m2m_pos.csv)")
    print(" [3] Resumo Operadoras (market_share_m2m_pos.csv)")
    print(" [4] Dimensão Operadora (dim_operadora.csv)")
    print(" [5] Dimensão Calendário (dim_calendario.csv)")
    print("----------------------------------------------------------------------------------")
    print(" Como selecionar:")
    print("   - Digite números separados por vírgula para relatórios específicos (ex: 1,3,4)")
    print("   - Digite 'Todos' ou deixe em BRANCO (pressione Enter) para gerar todos os 5.")
    print("==================================================================================")
    
    selection = input("\nSelecione os relatórios a serem gerados: ").strip()
    
    # Determina quais serão gerados
    generate_all = not selection or selection.lower() == 'todos'
    selected_indices = set()
    
    if not generate_all:
        try:
            for x in selection.split(','):
                idx = int(x.strip())
                if 1 <= idx <= 5:
                    selected_indices.add(idx)
        except ValueError:
            print("Entrada inválida. Gerando TODOS os relatórios por padrão.")
            generate_all = True
            
    # Função para salvar CSV com ponto e vírgula
    def save_csv(filename, headers, rows):
        target_path = os.path.join(folder, filename)
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
        
    print("\n==================================================================================")
    print("          SUCESSO! Os relatórios selecionados foram salvos na pasta.              ")
    print("          Você já pode abrir o Power BI e carregar estes arquivos!               ")
    print("==================================================================================")

if __name__ == "__main__":
    main()
