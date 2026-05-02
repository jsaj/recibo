import streamlit as st
from fpdf import FPDF
from io import BytesIO
import num2words
import os
from datetime import datetime, date
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
# PDF
# ========================
class CustomPDF(FPDF):
    def header(self):
        pass


def data_em_texto(data):
    meses = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    data_formatada = data.strftime('%d de %B de %Y')
    mes = data_formatada.split('de')[1].strip()
    return data_formatada.replace(mes, meses[mes])


def generate_pdf(nome_cliente, quantidade, valor, logo_path, assinatura_path, data_recibo):
    pdf = CustomPDF()
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.add_page()

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
    data_formatada = data_em_texto(data_recibo)
    pdf.cell(0, 10, f"Lajes/RN, {data_formatada}", ln=True, align='C')

    pdf.ln(50)
    pdf.image(assinatura_path, x=65, w=80)
    pdf.ln(-5)
    pdf.set_font('Times', '', 11)
    pdf.cell(0, 10, "_______________________________________", ln=True, align='C')
    pdf.ln(-5)
    pdf.cell(0, 10, "Maria Verônica Gomes Pereira Avelino", ln=True, align='C')

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)

# ========================
# EXTRAÇÃO IA
# ========================
def extrair_dados_da_imagem(imagem_cap, gemini_key):
    if not gemini_key:
        return None, None, None

    modelos_disponiveis = [
        "gemini-2.5-flash",
        "gemini-3-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite"
    ]

    bytes_data = imagem_cap.getvalue()
    base64_image = base64.b64encode(bytes_data).decode('utf-8')

    prompt = """Extraia nome, quantidade e valor da imagem e retorne JSON."""

    for modelo in modelos_disponiveis:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={gemini_key}"
        headers = {'Content-Type': 'application/json'}

        payload = {
            "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}]}],
            "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"}
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                continue

            data = response.json()
            resposta = data["candidates"][0]["content"]["parts"][0]["text"]
            dados = json.loads(resposta)
            return dados.get("nome", ""), dados.get("quantidade", 0), float(dados.get("valor", 0.0))
        except:
            continue

    return None, None, None

# ========================
# UI
# ========================
st.set_page_config(page_title="Gerador de Recibo", layout="wide")
st.title("📷 Gerador de Recibo Inteligente")

API_KEY = carregar_api_key()

BASE_DIR = os.path.dirname(__file__)
logo_path = os.path.join(BASE_DIR, "images", "logo.png")
assinatura_path = os.path.join(BASE_DIR, "images", "assinatura.png")

if "nome" not in st.session_state:
    st.session_state.nome = ""
if "qtd" not in st.session_state:
    st.session_state.qtd = 0
if "val" not in st.session_state:
    st.session_state.val = 0.0

imagem_cap = st.camera_input("📷 Tire uma foto")

if imagem_cap and API_KEY:
    nome, qtd, val = extrair_dados_da_imagem(imagem_cap, API_KEY)
    if nome:
        st.session_state.nome = nome
        st.session_state.qtd = int(qtd)
        st.session_state.val = float(val)

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    nome_final = st.text_input("Nome", key="nome")
with col2:
    qtd_final = st.number_input("Quantidade", step=1, key="qtd")
with col3:
    val_final = st.number_input("Valor", step=0.5, key="val")
with col4:
    data_final = st.date_input("Data do Recibo", value=date.today())

if nome_final and qtd_final > 0 and val_final > 0:
    pdf_bytes = generate_pdf(
        nome_final,
        qtd_final,
        val_final,
        logo_path,
        assinatura_path,
        data_final
    )

    nome_arquivo = nome_final.strip().lower().replace(" ", "_")

    st.download_button(
        label="📄 Baixar PDF",
        data=pdf_bytes,
        file_name=f"recibo_{nome_arquivo}.pdf",
        mime="application/pdf"
    )
