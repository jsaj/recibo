import streamlit as st
from fpdf import FPDF
from io import BytesIO
import num2words
import os
from datetime import datetime
import json
import requests
import yaml
import base64

# ========================
# CONFIGURAÇÃO DE AMBIENTE
# ========================
def carregar_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass 

    env_path = os.path.join(os.path.dirname(__file__), 'env.yaml')
    try:
        with open(env_path, 'r', encoding='utf-8') as file:
            env_vars = yaml.safe_load(file)
            return env_vars.get('GEMINI_API_KEY')
    except FileNotFoundError:
        return None
    except Exception as e:
        st.sidebar.error(f"⚠️ Erro ao ler env.yaml: {e}")
        return None

# ========================
# PDF COMPLETO COM ASSINATURA
# ========================
class CustomPDF(FPDF):
    def header(self):
        pass 

def data_atual_em_texto():
    meses = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    data = datetime.now()
    data_formatada = data.strftime('%d de %B de %Y')
    mes = data_formatada.split('de')[1].strip()
    return data_formatada.replace(mes, meses[mes])

def generate_pdf(nome_cliente, quantidade, valor, logo_path, assinatura_path):
    pdf = CustomPDF()
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.add_page()

    if not os.path.exists(logo_path):
        raise FileNotFoundError(f"Logo não encontrada: {logo_path}")
    if not os.path.exists(assinatura_path):
        raise FileNotFoundError(f"Assinatura não encontrada: {assinatura_path}")

    pdf.image(logo_path, x=87.5, y=30, w=35)
    pdf.set_font('Times', 'B', 18)
    pdf.ln(60)
    pdf.cell(0, 10, 'RECIBO DE PAGAMENTO', ln=True, align='C')

    pdf.set_font('Times', '', 11)
    pdf.ln(25)

    valor_extenso = num2words.num2words(valor, lang='pt_BR', to='currency')
    quantidade_extenso = num2words.num2words(quantidade, lang='pt_BR')
    valor_corrigido = f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    if quantidade < 1000:
        quantidade_corrigido = quantidade
    else:
        quantidade_corrigido = f"{quantidade:,}".replace(',', '.')

    texto = (
        f"Eu, Maria Verônica Gomes Pereira Avelino, CPF: 047.589.934-24, "
        f"recebi do(a) {nome_cliente} o valor de R$ {valor_corrigido} ({valor_extenso}), "
        f"referente ao fornecimento de {quantidade_corrigido} ({quantidade_extenso}) salgados."
    )
    pdf.multi_cell(0, 5, texto, align='J')

    pdf.ln(40)
    data_hoje = data_atual_em_texto()
    pdf.cell(0, 10, f"Lajes/RN, {data_hoje}", ln=True, align='C')

    pdf.ln(50)
    pdf.image(assinatura_path, x=65, w=80)
    pdf.ln(-5)
    pdf.set_font('Times', '', 11)
    pdf.cell(0, 10, "_______________________________________", ln=True, align='C')
    pdf.ln(-5)
    pdf.cell(0, 10, "Maria Verônica Gomes Pereira Avelino", ln=True, align='C')

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)

def extrair_dados_da_imagem(imagem_cap, gemini_key):
    if not gemini_key:
        return None, None, None

    # Lista de modelos em ordem de prioridade (conforme sua tabela)
    modelos_disponiveis = [
        "gemini-2.5-flash",
        "gemini-3-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite"
    ]

    bytes_data = imagem_cap.getvalue()
    base64_image = base64.b64encode(bytes_data).decode('utf-8')
    
    prompt = """Você é um especialista em ler anotações manuscritas de pedidos.
    Extraia os dados da imagem seguindo rigorosamente estas regras:
    
    1. "nome": O nome do cliente, empresa ou estabelecimento. ATENÇÃO: NUNCA coloque o nome do produto vendido (como "Salgados", "Doces", "Coxinhas") neste campo.
    2. "quantidade": A quantidade total de itens (apenas números).
    3. "valor": O preço total a ser cobrado, em formato decimal (ex: 114.00).
    4. Artigos, conjunções e preposição (como "do", "da", "de", "e") devem ser retornados em minúsculo.
    Retorne os dados usando estritamente as chaves JSON: "nome", "quantidade" e "valor"."""

    for modelo in modelos_disponiveis:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={gemini_key}"
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}]}],
            "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"}
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            
            # Se atingiu o limite (Erro 429), tenta o próximo modelo da lista
            if response.status_code == 429:
                st.warning(f"⚠️ Limite atingido no {modelo}. Tentando modelo de backup...")
                continue 
            
            if response.status_code != 200:
                st.error(f"Erro no modelo {modelo}: {response.status_code}")
                continue

            data = response.json()
            resposta = data["candidates"][0]["content"]["parts"][0]["text"]
            dados = json.loads(resposta)
            return dados.get("nome", ""), dados.get("quantidade", 0), float(dados.get("valor", 0.0))

        except Exception as e:
            continue # Tenta o próximo em caso de falha de conexão

    st.error("❌ Todos os modelos atingiram o limite ou falharam. Tente novamente em alguns minutos.")
    return None, None, None

# ========================
# API DIRETA DO GOOGLE GEMINI
# ========================
# def extrair_dados_da_imagem(imagem_cap, gemini_key):
#     """Envia a imagem direto para a API oficial do Google Gemini"""
#     if not gemini_key:
#         return None, None, None

#     # Prepara a imagem
#     bytes_data = imagem_cap.getvalue()
#     base64_image = base64.b64encode(bytes_data).decode('utf-8')

#     # URL oficial do Google AI Studio para o Gemini 2.5 Flash
#     url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    
#     headers = {'Content-Type': 'application/json'}
    
#     prompt = """Você é um especialista em ler anotações manuscritas de pedidos.
#     Extraia os dados da imagem seguindo rigorosamente estas regras:
    
#     1. "nome": O nome do cliente, empresa ou estabelecimento. ATENÇÃO: NUNCA coloque o nome do produto vendido (como "Salgados", "Doces", "Coxinhas") neste campo.
#     2. "quantidade": A quantidade total de itens (apenas números).
#     3. "valor": O preço total a ser cobrado, em formato decimal (ex: 114.00).
#     4. A imagem contém um pedido de compra de produtos de salgados.
#     5. NÃO escreva introduções, explicações ou formatação markdown.
#     6. Artigos, conjunções e preposição (como "do", "da", "de", "e") devem ser escritos em minúsculo.
#     Retorne os dados usando estritamente as chaves JSON: "nome", "quantidade" e "valor"."""

#     payload = {
#         "contents": [{
#             "parts": [
#                 {"text": prompt},
#                 {
#                     "inline_data": {
#                         "mime_type": "image/jpeg",
#                         "data": base64_image
#                     }
#                 }
#             ]
#         }],
#         "generationConfig": {
#             "temperature": 0.1,
#             "response_mime_type": "application/json" # Mágica do Google: força o modelo a retornar JSON válido!
#         }
#     }

#     try:
#         response = requests.post(url, headers=headers, json=payload)
        
#         if response.status_code != 200:
#             st.error(f"Erro na API do Google: {response.text}")
#             return None, None, None

#         data = response.json()
#         resposta = data["candidates"][0]["content"]["parts"][0]["text"]
        
#         # Como forçamos o response_mime_type, ele já vem como JSON limpo, sem precisar de Regex!
#         dados = json.loads(resposta)
#         return dados.get("nome", ""), dados.get("quantidade", 0), float(dados.get("valor", 0.0))

#     except Exception as e:
#         st.error(f"Falha ao conectar com o Google: {e}")
#         return None, None, None

# ========================
# UI - STREAMLIT
# ========================
st.set_page_config(page_title="Gerador de Recibo Inteligente", page_icon="📝")
st.title("📷 Gerador de Recibo Inteligente")

API_KEY = carregar_api_key()

BASE_DIR = os.path.dirname(__file__)
logo_path = os.path.join(BASE_DIR, "images", "logo.png")
assinatura_path = os.path.join(BASE_DIR, "images", "assinatura.png")

if "dados_extraidos" not in st.session_state:
    st.session_state.dados_extraidos = False
if "ultima_imagem_id" not in st.session_state:
    st.session_state.ultima_imagem_id = None
if "nome" not in st.session_state:
    st.session_state.nome = ""
if "qtd" not in st.session_state:
    st.session_state.qtd = 0
if "val" not in st.session_state:
    st.session_state.val = 0.0

imagem_cap = st.camera_input("📷 Tire uma foto do seu documento ou anotação manuscrita")

if imagem_cap is not None:
    if st.session_state.ultima_imagem_id != imagem_cap.file_id:
        st.session_state.ultima_imagem_id = imagem_cap.file_id
        
        if not API_KEY:
            st.error("⚠️ Configure sua chave do Gemini para processar a imagem.")
        else:
            with st.spinner("O Google Gemini está lendo a sua caligrafia..."):
                nome, qtd, val = extrair_dados_da_imagem(imagem_cap, API_KEY)
                
                if nome is not None:
                    # Função interna para formatar o nome respeitando as exceções
                    def formatar_nome_ptbr(texto):
                        excecoes = ['de', 'do', 'da', 'dos', 'das', 'e', 'o', 'os', 'a', 'as']
                        palavras = texto.split()
                        resultado = []
                        for i, palavra in enumerate(palavras):
                            palavra_lower = palavra.lower()
                            # A primeira palavra sempre é Maiúscula, as outras dependem da lista de exceções
                            if i == 0 or palavra_lower not in excecoes:
                                resultado.append(palavra.capitalize())
                            else:
                                resultado.append(palavra_lower)
                        return " ".join(resultado)

                    # Aplica a formatação inteligente no nome extraído
                    st.session_state.nome = formatar_nome_ptbr(str(nome))
                    
                    # Restante do código de processamento...
                    try:
                        st.session_state.qtd = int(qtd)
                    except:
                        st.session_state.qtd = 0
                    try:
                        st.session_state.val = float(val)
                    except:
                        st.session_state.val = 0.0
                        
                    st.session_state.dados_extraidos = True
                else:
                    st.warning("A imagem não ficou clara. Tente tirar uma foto mais focada e iluminada.")

st.divider()

if st.session_state.dados_extraidos:
    st.subheader("Verifique os dados do Recibo:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        nome_final = st.text_input("Nome do Cliente", key="nome")
    with col2:
        qtd_final = st.number_input("Quantidade", step=1, key="qtd")
    with col3:
        val_final = st.number_input("Valor (R$)", step=0.5, format="%.2f", key="val")
    
    if nome_final and qtd_final > 0 and val_final > 0:
        try:
            pdf_bytes = generate_pdf(nome_final, qtd_final, val_final, logo_path, assinatura_path)
            nome_arquivo = nome_final.lower().replace(" ", "_")
            
            st.download_button(
                label="📄 Baixar Recibo (PDF)",
                data=pdf_bytes,
                file_name=f"recibo_{nome_arquivo}.pdf",
                mime="application/pdf",
                type="primary"
            )
        except FileNotFoundError as e:
            st.error(f"**Erro nas Imagens:** {e}")
    else:
        st.info("💡 Preencha os campos com valores maiores que zero para habilitar o download do recibo.")