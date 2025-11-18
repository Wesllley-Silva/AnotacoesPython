from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib # NOVO: Importa a biblioteca SMTP
from email.mime.text import MIMEText # NOVO: Para criar a mensagem de e-mail

# ----------------------------------------------------
# NOVO: Funções para formatar e enviar o e-mail
# ----------------------------------------------------

def formatar_dados_para_email(dados):
    """
    Formata a lista de dicionários de dados extraídos em uma string de texto legível.
    """
    if not dados:
        return "Nenhuma aposta segura encontrada na extração."

    corpo_email = "✨ Dados Extraídos da Tabela Surebet: ✨\n\n"
    corpo_email += "=" * 80 + "\n\n"

    for item in dados:
        # Linha principal com Evento, Modalidade e Lucro
        corpo_email += f"**Evento**: {item['Evento Principal']} ({item['Modalidade']}) | **Lucro/Tempo**: {item['Lucro/Tempo']}\n"
        
        # Detalhes das entradas
        for i, aposta in enumerate(item['Entradas']):
            corpo_email += f"  Entrada {i+1} 🚀 Casa: {aposta['Casa de Aposta']} | Chance: {aposta['Chance']} | Mercado: {aposta['Mercado']} | Data/Hora: {aposta['Data/Hora']}\n"
        
        corpo_email += "-" * 80 + "\n"
        
    return corpo_email

def enviar_email(dados, remetente, senha_app, destinatario):
    """
    Formata os dados e envia o e-mail usando o servidor SMTP do Gmail.
    """
    corpo_email = formatar_dados_para_email(dados)
    assunto = "Relatório de Surebets Diárias"
    
    # Cria o objeto da mensagem
    msg = MIMEText(corpo_email)
    msg['Subject'] = assunto
    msg['From'] = remetente
    msg['To'] = destinatario

    # Conexão com o servidor SMTP do Gmail
    try:
        # O Gmail usa o host 'smtp.gmail.com' e a porta 587 (TLS/STARTTLS)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls() # Inicia a segurança TLS
        server.login(remetente, senha_app)
        server.sendmail(remetente, destinatario, msg.as_string())
        server.close()
        print(f"\n✅ E-mail enviado com sucesso para {destinatario}!")
    except Exception as e:
        print(f"\n❌ Erro ao enviar e-mail: {e}")
        print("Certifique-se de ter usado uma Senha de App do Gmail.")


# ----------------------------------------------------
# Código Original (extrair_dados_surebets)
# ----------------------------------------------------

def extrair_dados_surebets(url, driver_instance):
    """
    [... Código da sua função original aqui ...]
    """
    # ... (O corpo desta função permanece inalterado) ...
    driver = driver_instance
    
    print("Navegando para o URL...")
    driver.get(url)

    # 1. Aguardar o carregamento da tabela
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "surebets-table"))
        )
        print("Tabela carregada com sucesso.")
    except Exception as e:
        print(f"Erro ao carregar a tabela: {e}")
        return []

    # 2. Encontrar todos os registros de apostas seguras
    surebet_records = driver.find_elements(By.CLASS_NAME, "surebet_record")
    
    if not surebet_records:
        print("Nenhum registro de aposta segura encontrado.")
        return []

    dados_extraidos = []
    
    # 3. Iterar sobre cada registro e extrair os dados
    for record in surebet_records:
        # Tenta extrair o lucro e a idade (primeira coluna do bloco)
        try:
            profit_element = record.find_element(By.CSS_SELECTOR, ".profit")
            profit_text = profit_element.text.strip()
            profit_age = record.find_element(By.CSS_SELECTOR, ".age").text.strip()
            lucro_tempo = f"{profit_text} / {profit_age}"
        except:
            lucro_tempo = "N/A"
            
        # O nome do evento e o esporte (modalidade) são encontrados na primeira aposta (Entrada 1)
        primeira_aposta_row = record.find_element(By.TAG_NAME, "tr")
        
        # Extrair Evento (Nome + Liga)
        try:
            event_element = primeira_aposta_row.find_element(By.CSS_SELECTOR, ".event")
            evento_texto = event_element.text.split('\n')
            evento_nome = evento_texto[0].strip()
            evento_liga = evento_texto[1].strip() if len(evento_texto) > 1 else ""
            evento_completo = f"{evento_nome} ({evento_liga})"
        except:
            evento_completo = "Evento Desconhecido"

        # Extrair a Modalidade (Esporte) - a tag <span> minor está dentro do .booker
        try:
            # Pega o texto da tag <span class="minor"> dentro do .booker (Futebol, Basquete, etc.)
            modalidade = primeira_aposta_row.find_element(By.CSS_SELECTOR, ".booker .minor").text.strip()
        except:
            modalidade = "N/A"


        # Encontrar todas as linhas de aposta dentro deste registro
        bet_rows = record.find_elements(By.TAG_NAME, "tr")
        
        apostas_detalhes = []
        
        for row in bet_rows:
            # Ignora a linha 'extra'
            if "extra" in row.get_attribute("class"):
                continue

            try:
                # Usamos find_elements e verificamos se o elemento existe (para lidar com rowspan)
                booker_elements = row.find_elements(By.CLASS_NAME, "booker")
                coeff_elements = row.find_elements(By.CLASS_NAME, "coeff")
                value_elements = row.find_elements(By.CLASS_NAME, "value")
                time_elements = row.find_elements(By.CLASS_NAME, "time")
                
                # Se não for uma linha de aposta completa, pula
                if not booker_elements or not value_elements:
                    continue 

                # Extração segura e limpeza de dados
                # A casa de aposta está na primeira linha (antes do \n)
                casa_aposta = booker_elements[0].text.split('\n')[0].strip()
                
                mercado = coeff_elements[0].text.strip() if coeff_elements else "N/A"
                
                chance_element = value_elements[0].find_element(By.CSS_SELECTOR, ".value_link")
                chance = chance_element.text.strip()
                
                data_hora = time_elements[0].text.strip().replace('\n', ' ') if time_elements else "N/A"
                
                # O evento/liga desta linha pode ser diferente, vamos extrair para garantir
                evento_row_element = row.find_elements(By.CLASS_NAME, "event")
                evento_row = evento_row_element[0].text.split('\n') if evento_row_element else []
                
                apostas_detalhes.append({
                    "Casa de Aposta": casa_aposta,
                    "Data/Hora": data_hora,
                    "Mercado": mercado,
                    "Chance": chance
                })

            except Exception as e:
                # Captura erros em linhas individuais
                continue
        
        # Adiciona o bloco completo de apostas no formato novo
        if apostas_detalhes:
             dados_extraidos.append({
                 "Evento Principal": evento_completo,
                 "Modalidade": modalidade,
                 "Lucro/Tempo": lucro_tempo,
                 "Entradas": apostas_detalhes
             })


    return dados_extraidos


# --- Configuração e Execução Principal (Com Envio de Email) ---
if __name__ == "__main__":
    
    # =========================================================================
    # 🚨 ONDE COLOCAR O E-MAIL E A SENHA 🚨
    # Você deve definir seu e-mail do Gmail, a Senha de App e o destinatário aqui.
    # =========================================================================
    EMAIL_REMETENTE = "wesllleygsilva@gmail.com" 
    SENHA_APP = "wbetunfsjfzbhfyu" # <-- USE ESTA SENHA DE APP AGORA
    EMAIL_DESTINATARIO = "wsplaytvonline@gmail.com"
    # =========================================================================
    
    url = "https://pt.surebet.com/surebets?utf8=%E2%9C%93&narrow=&filter[selected][]=&filter[selected][]=33879884&filter[save]=&filter[current_id]=33879884&selector[order]=created_at_desc&selector[outcomes][]=&selector[outcomes][]=2&selector[min_profit]=0.7&selector[max_profit]=&selector[min_roi]=&selector[max_roi]=&selector[comb_created_at_period]=0_0&selector[settled_period]=0_172800&selector[bookies_settings]=0%3A67%3A%3A%3A2%3B0%3A105%3A%3A%3A2%3B0%3A253%3A%3A%3A2%3B0%3A66%3A%3A%3A2%3B0%3A76%3A%3A%3A2%3B0%3A93%3A%3A%3A2%3B0%3A182%3A%3A%3A2%3B0%3A74%3A%3A%3A2%3B0%3A427%3A%3A%3A2%3B0%3A37%3A%3A%3A2%3B0%3A148%3A%3A%3A2%3B0%3A428%3A%3A%3A2%3B0%3A211%3A%3A%3A2%3B0%3A114%3A%3A%3A2%3B0%3A260%3A%3A%3A2%3B0%3A101%3A%3A%3A2%3B0%3A132%3A%3A%3A2%3B0%3A42%3A%3A%3A2%3B0%3A40%3A%3A%3A2%3B0%3A393%3A%3A%3A2%3B0%3A381%3A%3A%3A2%3B0%3A438%3A%3A%3A2%3B0%3A429%3A%3A%3A2%3B0%3A269%3A%3A%3A2%3B0%3A430%3A%3A%3A2%3B0%3A126%3A%3A%3A2%3B0%3A291%3A%3A%3A2%3B0%3A201%3A%3A%3A2%3B0%3A21%3A%3A%3A2%3B0%3A391%3A%3A%3A2%3B0%3A70%3A%3A%3A2%3B0%3A263%3A%3A%3A2%3B0%3A443%3A%3A%3A2%3B0%3A26%3A%3A%3A2%3B0%3A296%3A%3A%3A2%3B0%3A422%3A%3A%3A2%3B0%3A236%3A%3A%3A2%3B0%3A347%3A%3A%3A2%3B0%3A139%3A%3A%3A2%3B0%3A111%3A%3A%3A2%3B0%3A401%3A%3A%3A2%3B0%3A319%3A%3A%3A2%3B0%3A36%3A%3A%3A2%3B0%3A150%3A%3A%3A2%3B4%3A202%3A%3A%3A2%3B0%3A151%3A%3A%3A2%3B0%3A395%3A%3A%3A2%3B0%3A23%3A%3A%3A2%3B0%3A309%3A%3A%3A2%3B0%3A200%3A%3A%3A2%3B0%3A203%3A%3A%3A2%3B0%3A60%3A%3A%3A2%3B0%3A116%3A%3A%3A2%3B0%3A32%3A%3A%3A2%3B0%3A138%3A%3A%3A2%3B0%3A363%3A%3A%3A2%3B0%3A65%3A%3A%3A2%3B0%3A161%3A%3A%3A2%3B0%3A301%3A%3A%3A2%3B0%3A29%3A%3A%3A2%3B0%3A398%3A%3A%3A2%3B0%3A365%3A%3A%3A2%3B0%3A10%3A%3A%3A2%3B0%3A107%3A%3A%3A2%3B0%3A106%3A%3A%3A2%3B0%3A265%3A%3A%3A2%3B0%3A45%3A%3A%3A2%3B0%3A228%3A%3A%3A2%3B0%3A322%3A%3A%3A2%3B0%3A34%3A%3A%3A2%3B0%3A77%3A%3A%3A2%3B0%3A266%3A%3A%3A2%3B0%3A58%3A%3A%3A2%3B0%3A461%3A%3A%3A2%3B0%3A100%3A%3A%3A2%3B0%3A153%3A%3A%3A2%3B0%3A95%3A%3A%3A2%3B0%3A311%3A%3A%3A2%3B0%3A180%3A%3A%3A2%3B0%3A320%3A%3A%3A2%3B0%3A254%3A%3A%3A2%3B0%3A425%3A%3A%3A2%3B0%3A208%3A%3A%3A2%3B0%3A14%3A%3A%3A2%3B0%3A197%3A%3A%3A2%3B0%3A152%3A%3A%3A2%3B0%3A409%3A%3A%3A2%3B0%3A325%3A%3A%3A2%3B0%3A11%3A%3A%3A2%3B0%3A38%3A%3A%3A2%3B0%3A147%3A%3A%3A2%3B0%3A378%3A%3A%3A2%3B0%3A415%3A%3A%3A2%3B0%3A52%3A%3A%3A2%3B0%3A406%3A%3A%3A2%3B0%3A198%3A%3A%3A2%3B0%3A304%3A%3A%3A2%3B0%3A324%3A%3A%3A2%3B0%3A55%3A%3A%3A2%3B0%3A187%3A%3A%3A2%3B0%3A33%3A%3A%3A2%3B0%3A13%3A%3A%3A2%3B0%3A68%3A%3A%3A2%3B0%3A448%3A%3A%3A2%3B0%3A351%3A%3A%3A2%3B0%3A176%3A%3A%3A2%3B0%3A125%3A%3A%3A2%3B0%3A248%3A%3A%3A2%3B0%3A379%3A%3A%3A2%3B0%3A49%3A%3A%3A2%3B0%3A215%3A%3A%3A2%3B0%3A113%3A%3A%3A2%3B0%3A411%3A%3A%3A2%3B0%3A62%3A%3A%3A2%3B0%3A426%3A%3A%3A2%3B0%3A75%3A%3A%3A2%3B0%3A96%3A%3A%3A2%3B0%3A390%3A%3A%3A2%3B0%3A385%3A%3A%3A2%3B0%3A231%3A%3A%3A2%3B0%3A12%3A%3A%3A2%3B0%3A177%3A%3A%3A2%3B0%3A193%3A%3A%3A2%3B0%3A408%3A%3A%3A2%3B0%3A436%3A%3A%3A2%3B0%3A90%3A%3A%3A2%3B0%3A403%3A%3A%3A2%3B0%3A389%3A%3A%3A2%3B0%3A460%3A%3A%3A2%3B0%3A229%3A%3A%3A2%3B0%3A279%3A%3A%3A2%3B0%3A210%3A%3A%3A2%3B0%3A146%3A%3A%3A2%3B0%3A117%3A%3A%3A2%3B0%3A255%3A%3A%3A2%3B0%3A346%3A%3A%3A2%3B0%3A135%3A%3A%3A2%3B0%3A24%3A%3A%3A2%3B0%3A321%3A%3A%3A2%3B0%3A282%3A%3A%3A2%3B0%3A88%3A%3A%3A2%3B0%3A348%3A%3A%3A2%3B0%3A73%3A%3A%3A2%3B0%3A171%3A%3A%3A2%3B0%3A53%3A%3A%3A2%3B0%3A261%3A%3A%3A2%3B0%3A144%3A%3A%3A2%3B0%3A312%3A%3A%3A2%3B0%3A121%3A%3A%3A2%3B0%3A386%3A%3A%3A2%3B0%3A331%3A%3A%3A2%3B0%3A373%3A%3A%3A2%3B0%3A352%3A%3A%3A2%3B0%3A154%3A%3A%3A2%3B0%3A129%3A%3A%3A2%3B0%3A402%3A%3A%3A2%3B0%3A234%3A%3A%3A2%3B0%3A274%3A%3A%3A2%3B0%3A214%3A%3A%3A2%3B0%3A338%3A%3A%3A2%3B0%3A388%3A%3A%3A2%3B0%3A416%3A%3A%3A2%3B0%3A419%3A%3A%3A2%3B0%3A170%3A%3A%3A2%3B0%3A276%3A%3A%3A2%3B0%3A396%3A%3A%3A2%3B0%3A104%3A%3A%3A2%3B0%3A108%3A%3A%3A2%3B0%3A230%3A%3A%3A2%3B0%3A290%3A%3A%3A2%3B0%3A158%3A%3A%3A2%3B0%3A307%3A%3A%3A2%3B0%3A145%3A%3A%3A2%3B0%3A219%3A%3A%3A2%3B0%3A449%3A%3A%3A2%3B0%3A273%3A%3A%3A2%3B0%3A257%3A%3A%3A2%3B0%3A165%3A%3A%3A2%3B0%3A5%3A%3A%3A2%3B0%3A404%3A%3A%3A2%3B0%3A162%3A%3A%3A2%3B0%3A6%3A%3A%3A2%3B0%3A397%3A%3A%3A2%3B0%3A112%3A%3A%3A2%3B0%3A245%3A%3A%3A2%3B0%3A364%3A%3A%3A2%3B0%3A431%3A%3A%3A2%3B0%3A235%3A%3A%3A2%3B0%3A464%3A%3A%3A2%3B0%3A175%3A%3A%3A2%3B0%3A334%3A%3A%3A2%3B0%3A224%3A%3A%3A2%3B0%3A190%3A%3A%3A2%3B0%3A294%3A%3A%3A2%3B0%3A297%3A%3A%3A2%3B0%3A183%3A%3A%3A2%3B0%3A453%3A%3A%3A2%3B0%3A327%3A%3A%3A2%3B0%3A242%3A%3A%3A2%3B0%3A213%3A%3A%3A2%3B0%3A341%3A%3A%3A2%3B0%3A244%3A%3A%3A2%3B0%3A369%3A%3A%3A2%3B0%3A376%3A%3A%3A2%3B0%3A30%3A%3A%3A2%3B0%3A15%3A%3A%3A2%3B0%3A370%3A%3A%3A2%3B0%3A212%3A%3A%3A2%3B0%3A372%3A%3A%3A2%3B0%3A437%3A%3A%3A2%3B0%3A350%3A%3A%3A2%3B0%3A329%3A%3A%3A2%3B0%3A435%3A%3A%3A2%3B0%3A128%3A%3A%3A2%3B0%3A344%3A%3A%3A2%3B0%3A50%3A%3A%3A2%3B0%3A439%3A%3A%3A2%3B0%3A366%3A%3A%3A2%3B0%3A9%3A%3A%3A2%3B0%3A259%3A%3A%3A2%3B0%3A179%3A%3A%3A2%3B0%3A318%3A%3A%3A2%3B0%3A41%3A%3A%3A2%3B0%3A85%3A%3A%3A2%3B0%3A84%3A%3A%3A2%3B0%3A130%3A%3A%3A2%3B0%3A462%3A%3A%3A2%3B0%3A133%3A%3A%3A2%3B0%3A247%3A%3A%3A2%3B0%3A335%3A%3A%3A2%3B0%3A3%3A%3A%3A2%3B0%3A131%3A%3A%3A2%3B0%3A281%3A%3A%3A2%3B0%3A240%3A%3A%3A2%3B0%3A8%3A%3A%3A2%3B0%3A353%3A%3A%3A2%3B0%3A118%3A%3A%3A2%3B0%3A384%3A%3A%3A2%3B0%3A89%3A%3A%3A2%3B0%3A283%3A%3A%3A2%3B0%3A285%3A%3A%3A2%3B0%3A284%3A%3A%3A2%3B0%3A46%3A%3A%3A2%3B0%3A323%3A%3A%3A2%3B0%3A299%3A%3A%3A2%3B0%3A124%3A%3A%3A2%3B0%3A226%3A%3A%3A2%3B0%3A82%3A%3A%3A2%3B0%3A63%3A%3A%3A2%3B0%3A83%3A%3A%3A2%3B0%3A98%3A%3A%3A2%3B0%3A61%3A%3A%3A2%3B0%3A167%3A%3A%3A2%3B0%3A400%3A%3A%3A2%3B0%3A137%3A%3A%3A2%3B0%3A258%3A%3A%3A2%3B0%3A141%3A%3A%3A2%3B0%3A459%3A%3A%3A2%3B0%3A19%3A%3A%3A2%3B0%3A142%3A%3A%3A2%3B0%3A164%3A%3A%3A2%3B0%3A278%3A%3A%3A2%3B0%3A249%3A%3A%3A2%3B0%3A434%3A%3A%3A2%3B0%3A174%3A%3A%3A2%3B0%3A31%3A%3A%3A2%3B0%3A367%3A%3A%3A2%3B0%3A54%3A%3A%3A2%3B0%3A194%3A%3A%3A2%3B0%3A458%3A%3A%3A2%3B0%3A326%3A%3A%3A2%3B0%3A368%3A%3A%3A2%3B0%3A316%3A%3A%3A2%3B0%3A317%3A%3A%3A2%3B0%3A251%3A%3A%3A2%3B0%3A51%3A%3A%3A2%3B0%3A181%3A%3A%3A2%3B0%3A103%3A%3A%3A2%3B0%3A2%3A%3A%3A2%3B0%3A358%3A%3A%3A2%3B0%3A143%3A%3A%3A2%3B0%3A375%3A%3A%3A2%3B4%3A7%3A%3A%3A2%3B0%3A371%3A%3A%3A2%3B0%3A189%3A%3A%3A2%3B0%3A172%3A%3A%3A2%3B0%3A330%3A%3A%3A2%3B0%3A272%3A%3A%3A2%3B0%3A293%3A%3A%3A2%3B0%3A47%3A%3A%3A2%3B0%3A305%3A%3A%3A2%3B0%3A412%3A%3A%3A2%3B0%3A407%3A%3A%3A2%3B0%3A306%3A%3A%3A2%3B0%3A463%3A%3A%3A2%3B0%3A440%3A%3A%3A2%3B0%3A433%3A%3A%3A2%3B0%3A218%3A%3A%3A2%3B0%3A302%3A%3A%3A2%3B0%3A423%3A%3A%3A2%3B0%3A123%3A%3A%3A2%3B0%3A328%3A%3A%3A2%3B0%3A178%3A%3A%3A2%3B0%3A414%3A%3A%3A2%3B0%3A310%3A%3A%3A2%3B0%3A25%3A%3A%3A2%3B0%3A69%3A%3A%3A2%3B0%3A313%3A%3A%3A2%3B0%3A441%3A%3A%3A2%3B0%3A140%3A%3A%3A2%3B0%3A119%3A%3A%3A2%3B0%3A16%3A%3A%3A2%3B0%3A207%3A%3A%3A2%3B0%3A442%3A%3A%3A2%3B0%3A451%3A%3A%3A2%3B0%3A232%3A%3A%3A2%3B0%3A399%3A%3A%3A2%3B0%3A48%3A%3A%3A2%3B0%3A223%3A%3A%3A2%3B0%3A163%3A%3A%3A2%3B0%3A256%3A%3A%3A2%3B0%3A97%3A%3A%3A2%3B0%3A173%3A%3A%3A2%3B0%3A361%3A%3A%3A2%3B0%3A186%3A%3A%3A2%3B4%3A192%3A%3A%3A2%3B4%3A380%3A%3A%3A2%3B0%3A394%3A%3A%3A2%3B0%3A418%3A%3A%3A2%3B0%3A270%3A%3A%3A2%3B0%3A392%3A%3A%3A2%3B0%3A444%3A%3A%3A2%3B0%3A43%3A%3A%3A2%3B0%3A267%3A%3A%3A2%3B0%3A91%3A%3A%3A2%3B0%3A410%3A%3A%3A2%3B0%3A289%3A%3A%3A2%3B0%3A377%3A%3A%3A2%3B0%3A275%3A%3A%3A2%3B0%3A184%3A%3A%3A2%3B0%3A18%3A%3A%3A2%3B0%3A455%3A%3A%3A2%3B0%3A59%3A%3A%3A2%3B0%3A456%3A%3A%3A2%3B0%3A64%3A%3A%3A2%3B0%3A216%3A%3A%3A2%3B0%3A314%3A%3A%3A2%3B0%3A120%3A%3A%3A2%3B0%3A343%3A%3A%3A2%3B0%3A447%3A%3A%3A2%3B0%3A277%3A%3A%3A2%3B0%3A149%3A%3A%3A2%3B0%3A127%3A%3A%3A2%3B0%3A115%3A%3A%3A2%3B0%3A342%3A%3A%3A2%3B0%3A339%3A%3A%3A2%3B0%3A452%3A%3A%3A2%3B0%3A160%3A%3A%3A2%3B0%3A457%3A%3A%3A2%3B0%3A110%3A%3A%3A2%3B0%3A387%3A%3A%3A2%3B0%3A450%3A%3A%3A2%3B0%3A102%3A%3A%3A2%3B0%3A239%3A%3A%3A2%3B0%3A217%3A%3A%3A2%3B0%3A446%3A%3A%3A2%3B0%3A413%3A%3A%3A2%3B0%3A424%3A%3A%3A2%3B0%3A28%3A%3A%3A2%3B0%3A405%3A%3A%3A2%3B0%3A220%3A%3A%3A2%3B0%3A222%3A%3A%3A2%3B0%3A250%3A%3A%3A2%3B0%3A252%3A%3A%3A2%3B0%3A44%3A%3A%3A2%3B0%3A421%3A%3A%3A2%3B0%3A227%3A%3A%3A2%3B0%3A206%3A%3A%3A2%3B0%3A155%3A%3A%3A2%3B0%3A195%3A%3A%3A2%3B0%3A221%3A%3A%3A2%3B0%3A420%3A%3A%3A2%3B0%3A71%3A%3A%3A2%3B0%3A79%3A%3A%3A2%3B0%3A80%3A%3A%3A2%3B0%3A78%3A%3A%3A2%3B0%3A81%3A%3A%3A2%3B0%3A27%3A%3A%3A2"
    
    # Configurar o WebDriver
    chrome_options = Options()
    # Para rodar sem a interface gráfica, descomente a linha abaixo:
    # chrome_options.add_argument("--headless") 
    
    # Assumindo que o driver está no PATH, caso contrário, use Service(caminho_para_driver)
    driver = webdriver.Chrome(options=chrome_options) 

    # Inicia a extração
    dados = extrair_dados_surebets(url, driver)

    # 4. Processar e Imprimir os Resultados no Novo Formato
    print("\n" + "="*80)
    print("✨ Dados Extraídos da Tabela Surebet (Formato Limpo): ✨")
    print("="*80)

    if dados:
        # Imprime o formato de saída no console (igual ao original)
        for item in dados:
            print(f"**Evento**: {item['Evento Principal']} ({item['Modalidade']}) | **Lucro/Tempo**: **{item['Lucro/Tempo']}**")
            for i, aposta in enumerate(item['Entradas']):
                print(f"Entrada {i+1} 🚀 **Casa**: {aposta['Casa de Aposta']} | **Chance**: {aposta['Chance']} | **Mercado**: {aposta['Mercado']} | **Data/Hora**: {aposta['Data/Hora']}")
            print("-" * 80)
            
        # ⚡️ NOVO: Enviar o e-mail após a extração bem-sucedida
        enviar_email(dados, EMAIL_REMETENTE, SENHA_APP, EMAIL_DESTINATARIO)

    else:
        print("A extração não retornou dados. Nenhum e-mail enviado.")
        
    # 5. Fechar o navegador 
    driver.quit()
    print("\nNavegador fechado. Extração concluída.")