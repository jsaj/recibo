import streamlit as st
from fpdf import FPDF
from io import BytesIO
import num2words
import os
from datetime import datetime
import tempfile
import json
import requests
import re
import yaml
from PIL import Image
import easyocr  # <--- Nova biblioteca de OCR

# ========================
# CONFIGURAÇÃO DE AMBIENTE
# ========================
def carregar_api_key():
    try:
        if "OPENROUTER_API_KEY" in st.secrets:
            return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        pass 

    env_path = os.path.join(os.path.dirname(__file__), 'env.yaml')
    try:
        with open(env_path, 'r', encoding='utf-8') as file:
            env_vars = yaml.safe_load(file)
            return env_vars.get('OPENROUTER_API_KEY')
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

# ========================
# MODELO OCR (EASYOCR)
# ========================
@st.cache_resource
def carregar_modelo_ocr():
    """Carrega o modelo EasyOCR para português e inglês"""
    return easyocr.Reader(['pt','en'], gpu=False) # GPU=True se tiver NVidia

def extrair_texto_imagem(imagem_cap):
    """Extrai texto bruto da imagem capturada usando EasyOCR"""
    try:
        # Converter a imagem do Streamlit para um objeto Pillow
        image = Image.open(imagem_cap)
        
        # Converter para formato que o EasyOCR aceita (array ou arquivo)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            image.save(tmp_file.name)
            tmp_path = tmp_file.name
            
        reader = carregar_modelo_ocr()
        # Ler o texto da imagem
        result = reader.readtext(tmp_path)
        
        # O EasyOCR retorna uma lista de tuplas [(bbox, text, prob), ...], pegamos o texto
        texto_bruto = " ".join([detection[1] for detection in result])
        
        # Limpar arquivo temporário
        os.unlink(tmp_path)
        
        return texto_bruto.strip()
    except Exception as e:
        st.error(f"⚠️ Erro no processamento de OCR: {e}")
        return ""

# ========================
# OPENROUTER
# ========================
def extrair_dados(texto, api_key):
    if not api_key:
        return None, None, None

    prompt = f"""Você é um assistente de extração de dados especializado em leitura de textos OCR.
O texto abaixo foi extraído de uma imagem e pode conter erros de ortografia e espaçamento.
Sua única função é ler o texto e retornar um JSON válido com os dados extraídos.
NÃO escreva introduções ou explicações.

Texto Extraído (OCR): "{texto}"

Formato OBRIGATÓRIO (retorne APENAS o JSON):
{{"nome": "Nome do Cliente", "quantidade": 0, "valor": 0.0}}"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openrouter/free", 
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
    )

    if response.status_code != 200:
        st.error(f"Erro na API: {response.text}")
        return None, None, None

    data = response.json()
    resposta = data["choices"][0]["message"]["content"]
    match = re.search(r'\{.*\}', resposta, re.DOTALL)

    if match:
        try:
            dados = json.loads(match.group(0))
            return dados.get("nome", ""), dados.get("quantidade", 0), float(dados.get("valor", 0.0))
        except json.JSONDecodeError:
            return None, None, None
            
    return None, None, None


# ========================
# UI - STREAMLIT
# ========================
st.set_page_config(page_title="Gerador de Recibo com IA (Visão)", page_icon="📝")
st.title("📷 Gerador de Recibo Inteligente (Visão)")

API_KEY = carregar_api_key()

BASE_DIR = os.path.dirname(__file__)
logo_path = os.path.join(BASE_DIR, "images", "logo.png")
assinatura_path = os.path.join(BASE_DIR, "images", "assinatura.png")

# Inicializa as variáveis na memória da sessão
if "dados_extraidos" not in st.session_state:
    st.session_state.dados_extraidos = False
if "ultima_imagem_id" not in st.session_state:
    st.session_state.ultima_imagem_id = None
# Inicializamos as chaves que vão se conectar diretamente aos widgets
if "nome" not in st.session_state:
    st.session_state.nome = ""
if "qtd" not in st.session_state:
    st.session_state.qtd = 0
if "val" not in st.session_state:
    st.session_state.val = 0.0

with st.sidebar:
    if API_KEY:
        st.success("✅ Chave da API carregada.")
    else:
        st.warning("❌ Chave da API ausente.")
    st.info("O processamento OCR é feito localmente. Apenas o texto extraído vai para a IA do OpenRouter.")

# Entrada da câmera (Não exibe o texto transcrito, apenas a imagem)
imagem_cap = st.camera_input("📷 Tire uma foto do seu documento ou anotação")

# Lógica de processamento automático da imagem
if imagem_cap is not None:
    
    # O Streamlit fornece um ID único para cada captura de imagem
    if st.session_state.ultima_imagem_id != imagem_cap.id:
        st.session_state.ultima_imagem_id = imagem_cap.id # Salva o novo ID na memória
        
        if not API_KEY:
            st.error("⚠️ API Key ausente. Configure para processar a imagem.")
        else:
            with st.spinner("Lendo imagem com OCR e extraindo dados..."):
                # 1. Extrair texto bruto da imagem (OCR local)
                texto_ocr = extrair_texto_imagem(imagem_cap)
                
                # Opcional: Para debugar o que o OCR leu, descomente a linha abaixo
                # st.write(f"Texto OCR Bruto: {texto_ocr}")
                
                if texto_ocr:
                    # 2. Enviar texto OCR para a IA extrair os valores
                    nome, qtd, val = extrair_dados(texto_ocr, API_KEY)
                    
                    if nome is not None:
                        # Atualiza os valores direto no session_state (isso atualiza a tela)
                        st.session_state.nome = str(nome).title()
                        
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
                    st.warning("Não foi possível ler nenhum texto na imagem. Tente tirar uma foto mais clara e focada.")

st.divider()

# Exibe os campos (agora conectados diretamente ao session_state via parâmetro "key")
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
            pdf_bytes = generate_pdf(nome_final, qtd_final, val_final, logo_path, azure_assinatura_path)
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