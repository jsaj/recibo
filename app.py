import streamlit as st
from fpdf import FPDF
from io import BytesIO
import num2words
import os
from datetime import datetime


class CustomPDF(FPDF):
    def header(self):
        pass


def data_em_texto(data):
    meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março',
        4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro',
        10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }

    return f"{data.day} de {meses[data.month]} de {data.year}"


def get_pessoa_info(escolha_pessoa):
    """Retorna informações da pessoa selecionada"""
    pessoas = {
        'Maria Verônica Gomes Pereira': {
            'nome': 'Maria Verônica Gomes Pereira',
            'cpf': '047.589.934-24',
            'assinatura': 'ass_001.png'
        },
        'Juscimara Gomes Avelino': {
            'nome': 'Juscimara Gomes Avelino',
            'cpf': '097.195.734-73',  # Ajuste para o CPF correto
            'assinatura': 'ass_002.jpeg'
        }
    }
    return pessoas.get(escolha_pessoa, pessoas['Maria Verônica Gomes Pereira'])


def generate_pdf(nome_cliente, quantidade, valor, data_recibo, tipo_item, logo_path, assinatura_path, 
                 nome_pessoa, cpf_pessoa, itens_misto=None):
    pdf = CustomPDF()

    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.add_page()

    # Logo
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=87.5, y=30, w=35)

    # Título
    pdf.set_font('Times', 'B', 18)
    pdf.ln(60)
    pdf.cell(0, 10, 'RECIBO DE PAGAMENTO', ln=True, align='C')

    # Texto
    pdf.set_font('Times', '', 11)
    pdf.ln(25)

    valor_extenso = num2words.num2words(valor, lang='pt_BR', to='currency')
    valor_corrigido = f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Construir texto de quantidade e descrição
    if tipo_item == "Misto":
        # Construir descrição dos itens mistos
        descricao_itens = []
        if itens_misto:
            for item in itens_misto:
                if item['quantidade'] > 0:
                    quantidade_extensa = num2words.num2words(item['quantidade'], lang='pt_BR')
                    if item['quantidade'] < 1000:
                        quantidade_formatada = item['quantidade']
                    else:
                        quantidade_formatada = f"{item['quantidade']:,}".replace(',', '.')
                    descricao_itens.append(f"{quantidade_formatada} ({quantidade_extensa}) {item['tipo'].lower()}")
        
        descricao = " e ".join(descricao_itens) if descricao_itens else ""
        texto = (
            f"Eu, {nome_pessoa}, CPF: {cpf_pessoa}, "
            f"recebi do(a) {nome_cliente} o pagamento no valor de R$ {valor_corrigido} ({valor_extenso}), "
            f"referente ao fornecimento de {descricao}."
        )
    else:
        # Tipo simples (Itens ou Salgados)
        quantidade_extenso = num2words.num2words(quantidade, lang='pt_BR')

        if quantidade < 1000:
            quantidade_corrigido = quantidade
        else:
            quantidade_corrigido = f"{quantidade:,}".replace(',', '.')

        tipo_item_minuscula = tipo_item.lower()

        texto = (
            f"Eu, {nome_pessoa}, CPF: {cpf_pessoa}, "
            f"recebi do(a) {nome_cliente} o pagamento no valor de R$ {valor_corrigido} ({valor_extenso}), "
            f"referente ao fornecimento de {quantidade_corrigido} ({quantidade_extenso}) {tipo_item_minuscula}."
        )

    pdf.multi_cell(0, 5, texto, align='J')

    # Data
    pdf.ln(40)
    data_formatada = data_em_texto(data_recibo)
    pdf.cell(0, 10, f"Lajes/RN, {data_formatada}", ln=True, align='C')

    # Assinatura
    pdf.ln(50)
    if os.path.exists(assinatura_path):
        pdf.image(assinatura_path, x=65, w=80)

    pdf.ln(-5)
    pdf.set_font('Times', '', 11)
    pdf.cell(0, 10, "_______________________________________", ln=True, align='C')
    pdf.ln(-5)
    pdf.cell(0, 10, nome_pessoa, ln=True, align='C')

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)


# ========================
# CUSTOM CSS
# ========================

st.set_page_config(
    page_title="Gerador de Recibo",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS customizado
custom_css = """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    [data-testid="stMainBlockContainer"] {
        padding-top: 0;
        padding-bottom: 2rem;
    }
    
    [data-testid="stHeader"] {
        background-color: #f8f9fa;
        border-bottom: 1px solid #e9ecef;
    }
    
    .form-card {
        background-color: white;
        border-radius: 12px;
        padding: 2.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        margin: 0 auto;
        max-width: 600px;
    }
    
    .title-container {
        text-align: center;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 2px solid #667eea;
    }
    
    .title-container h1 {
        color: #2c3e50;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .title-container p {
        color: #7f8c8d;
        font-size: 0.95rem;
    }
    
    .section-title {
        color: #667eea;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .section-number {
        background-color: #667eea;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    [data-testid="stTextInput"] input {
        border: 1px solid #ddd !important;
        border-radius: 6px !important;
        padding: 0.75rem !important;
        font-size: 0.95rem !important;
    }
    
    [data-testid="stNumberInput"] input {
        border: 1px solid #ddd !important;
        border-radius: 6px !important;
        padding: 0.75rem !important;
        font-size: 0.95rem !important;
    }
    
    [data-testid="stDateInput"] input {
        border: 1px solid #ddd !important;
        border-radius: 6px !important;
        padding: 0.75rem !important;
        font-size: 0.95rem !important;
    }
    
    [data-testid="stSelectbox"] {
        margin: 0.5rem 0;
    }
    
    [data-testid="stRadio"] {
        margin: 1rem 0;
    }
    
    [data-testid="stRadio"] label {
        background-color: #f8f9fa;
        padding: 0.75rem 1rem !important;
        border-radius: 6px;
        margin-bottom: 0.5rem !important;
        border: 2px solid transparent !important;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    [data-testid="stRadio"] label:hover {
        background-color: #e9ecef;
        border-color: #667eea !important;
    }
    
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-top: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3) !important;
    }
    
    [data-testid="stDownloadButton"] > button {
        width: 100%;
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        color: white !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 6px !important;
        font-weight: 600;
        font-size: 1rem;
    }
    
    [data-testid="stDownloadButton"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(17, 153, 142, 0.3) !important;
    }
    
    [data-testid="stAlert"] {
        border-radius: 6px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    [data-testid="stMarkdownContainer"] h3 {
        color: #667eea;
        font-size: 1.1rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# ========================
# STREAMLIT UI
# ========================

# Container principal
st.markdown('<div class="form-card">', unsafe_allow_html=True)

# Título
st.markdown("""
<div class="title-container">
    <h1>📄 Gerador de Recibo</h1>
    <p>Preencha os dados abaixo para gerar seu recibo de pagamento</p>
</div>
""", unsafe_allow_html=True)

# Seção 1: Pessoa que recebeu o pagamento
st.markdown('<div class="section-title"><div class="section-number">1</div>Pessoa que Recebeu o Pagamento</div>', unsafe_allow_html=True)

escolha_pessoa = st.selectbox(
    'Selecione a pessoa',
    options=['Maria Verônica Gomes Pereira', 'Juscimara Gomes Avelino'],
    label_visibility='collapsed'
)

# Obter informações da pessoa selecionada
pessoa_info = get_pessoa_info(escolha_pessoa)

# Exibir informações da pessoa selecionada
col1, col2 = st.columns(2, gap="medium")
with col1:
    st.text_input('Nome', value=pessoa_info['nome'], disabled=True)
with col2:
    st.text_input('CPF', value=pessoa_info['cpf'], disabled=True)

# Seção 2: Nome do Cliente
st.markdown('<div class="section-title"><div class="section-number">2</div>Dados do Cliente</div>', unsafe_allow_html=True)
nome_cliente = st.text_input(
    'Nome do Cliente',
    placeholder='Digite o nome completo do cliente',
    label_visibility='collapsed'
)

# Seção 3: Tipo de Item
st.markdown('<div class="section-title"><div class="section-number">3</div>Tipo de Item</div>', unsafe_allow_html=True)
tipo_item = st.radio(
    'Selecione uma opção',
    options=['Itens', 'Salgados', 'Misto'],
    horizontal=True,
    label_visibility='collapsed'
)

# Seção 4: Quantidade ou Itens Mistos
st.markdown('<div class="section-title"><div class="section-number">4</div>Detalhes da Entrega (quantidade)</div>', unsafe_allow_html=True)

if tipo_item != "Misto":
    quantidade = st.number_input(
        f'Quantidade de {tipo_item}',
        min_value=1,
        step=1,
        placeholder=f'Digite a quantidade de {tipo_item.lower()}',
        label_visibility='collapsed'
    )
else:
    quantidade = 0

# Itens Mistos
itens_misto = None
if tipo_item == "Misto":
    # Inicializar estado da sessão se não existir
    if 'itens_misto_list' not in st.session_state:
        st.session_state.itens_misto_list = [{'tipo': '', 'quantidade': 0}]
    
    itens_misto = []
    
    # Criar inputs para cada item
    for idx in range(len(st.session_state.itens_misto_list)):
        col1, col2, col3 = st.columns([2, 1, 0.4], gap="small")
        
        with col1:
            tipo = st.text_input(
                f'Tipo de Item {idx + 1}',
                value=st.session_state.itens_misto_list[idx]['tipo'],
                key=f'tipo_{idx}',
                placeholder='Ex: Salgados, Refrigerantes',
                label_visibility='collapsed'
            )
            st.session_state.itens_misto_list[idx]['tipo'] = tipo
        
        with col2:
            qtd = st.number_input(
                f'Qtd {idx + 1}',
                min_value=0,
                step=1,
                value=st.session_state.itens_misto_list[idx]['quantidade'],
                key=f'qtd_{idx}',
                label_visibility='collapsed'
            )
            st.session_state.itens_misto_list[idx]['quantidade'] = qtd
        
        with col3:
            if st.button('🗑️', key=f'remove_{idx}', help='Remover item'):
                st.session_state.itens_misto_list.pop(idx)
                st.rerun()
        
        if tipo and qtd > 0:
            itens_misto.append({'tipo': tipo, 'quantidade': qtd})
    
    # Botão para adicionar novo item
    if st.button('➕ Adicionar Item', use_container_width=True):
        st.session_state.itens_misto_list.append({'tipo': '', 'quantidade': 0})
        st.rerun()

# Seção 5: Valor e Data
st.markdown('<div class="section-title"><div class="section-number">5</div>Valor (R$)</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="medium")

with col1:
    valor = st.number_input(
        'Valor Total (R$)',
        min_value=0.0,
        step=0.01,
        placeholder='0,00',
        label_visibility='collapsed'
    )

with col2:
    data_recibo = st.date_input(
        'Data do Recibo',
        value=datetime.today(),
        label_visibility='collapsed'
    )

st.markdown('</div>', unsafe_allow_html=True)

# Caminhos das imagens
BASE_DIR = os.path.dirname(__file__)
logo_path = os.path.join(BASE_DIR, "images", "logo.png")
# Assinatura será determinada dinamicamente
assinatura_path = os.path.join(BASE_DIR, "images", pessoa_info['assinatura'])

# Botão Gerar PDF
gerar_pdf = st.button('📋 Gerar PDF', use_container_width=True)

if gerar_pdf:
    # Validações
    erro = False
    
    if not nome_cliente.strip():
        st.error("⚠️ Por favor, informe o nome do cliente.")
        erro = True

    if tipo_item != "Misto" and quantidade <= 0:
        st.error("⚠️ Por favor, informe a quantidade.")
        erro = True

    if tipo_item == "Misto":
        if not itens_misto:
            st.error("⚠️ Adicione pelo menos um item ao recibo misto.")
            erro = True

    if not os.path.exists(assinatura_path):
        st.error(f"⚠️ Arquivo de assinatura não encontrado: {pessoa_info['assinatura']}")
        erro = True

    if not erro:
        pdf_bytes = generate_pdf(
            nome_cliente,
            quantidade,
            valor,
            data_recibo,
            tipo_item,
            logo_path,
            assinatura_path,
            pessoa_info['nome'],
            pessoa_info['cpf'],
            itens_misto=itens_misto
        )

        nome_cliente_saida = "_".join(nome_cliente.lower().split())

        st.download_button(
            label="✅ Baixar PDF",
            data=pdf_bytes,
            file_name=f"recibo_{nome_cliente_saida}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        st.success("✨ Recibo gerado com sucesso! Clique no botão acima para fazer download.")