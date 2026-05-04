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


def generate_pdf(nome_cliente, quantidade, valor, data_recibo, tipo_item, logo_path, assinatura_path, itens_misto=None):
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
            f"Eu, Maria Verônica Gomes Pereira Avelino, CPF: 047.589.934-24, "
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
            f"Eu, Maria Verônica Gomes Pereira Avelino, CPF: 047.589.934-24, "
            f"recebi do(a) {nome_cliente} no valor de R$ {valor_corrigido} ({valor_extenso}), "
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
    pdf.cell(0, 10, "Maria Verônica Gomes Pereira Avelino", ln=True, align='C')

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)


# ========================
# STREAMLIT UI
# ========================

st.title('Gerador de Recibo')

# 1. Nome
nome_cliente = st.text_input('Nome do Cliente')

# 2. Tipo de Item (Itens, Salgados ou Misto)
tipo_item = st.radio(
    'Tipo de Item:',
    options=['Itens', 'Salgados', 'Misto'],
    horizontal=False
)

# 3. Quantidade (aparecer apenas se não for Misto)
if tipo_item != "Misto":
    quantidade = st.number_input(f'Quantidade de {tipo_item}', min_value=1, step=1)
else:
    quantidade = 0

# 4. Itens Mistos (aparecer apenas se for Misto)
itens_misto = None
if tipo_item == "Misto":
    st.subheader("Itens do Recibo")
    
    # Inicializar estado da sessão se não existir
    if 'itens_misto_list' not in st.session_state:
        st.session_state.itens_misto_list = [{'tipo': '', 'quantidade': 0}]
    
    itens_misto = []
    
    # Criar inputs para cada item
    for idx in range(len(st.session_state.itens_misto_list)):
        col1, col2, col3 = st.columns([2, 1, 0.5])
        
        with col1:
            tipo = st.text_input(
                f'Tipo de Item {idx + 1}',
                value=st.session_state.itens_misto_list[idx]['tipo'],
                key=f'tipo_{idx}'
            )
            st.session_state.itens_misto_list[idx]['tipo'] = tipo
        
        with col2:
            qtd = st.number_input(
                f'Quantidade {idx + 1}',
                min_value=0,
                step=1,
                value=st.session_state.itens_misto_list[idx]['quantidade'],
                key=f'qtd_{idx}'
            )
            st.session_state.itens_misto_list[idx]['quantidade'] = qtd
        
        with col3:
            if st.button('Remover', key=f'remove_{idx}'):
                st.session_state.itens_misto_list.pop(idx)
                st.rerun()
        
        if tipo and qtd > 0:
            itens_misto.append({'tipo': tipo, 'quantidade': qtd})
    
    # Botão para adicionar novo item
    if st.button('Adicionar Item'):
        st.session_state.itens_misto_list.append({'tipo': '', 'quantidade': 0})
        st.rerun()

# 5. Valor
valor = st.number_input('Valor Total (R$)', min_value=0.0, step=0.01)

# 6. Data (editável)
data_recibo = st.date_input('Data do Recibo', value=datetime.today())

# Caminhos das imagens
BASE_DIR = os.path.dirname(__file__)
logo_path = os.path.join(BASE_DIR, "images", "logo.png")
assinatura_path = os.path.join(BASE_DIR, "images", "assinatura.png")


if st.button('Gerar PDF'):

    if not nome_cliente:
        st.error("Informe o nome do cliente.")
        st.stop()

    if tipo_item != "Misto" and quantidade <= 0:
        st.error("Informe a quantidade.")
        st.stop()

    if tipo_item == "Misto":
        if not itens_misto:
            st.error("Adicione pelo menos um item ao recibo misto.")
            st.stop()

    pdf_bytes = generate_pdf(
        nome_cliente,
        quantidade,
        valor,
        data_recibo,
        tipo_item,
        logo_path,
        assinatura_path,
        itens_misto=itens_misto
    )

    nome_cliente_saida = "_".join(nome_cliente.lower().split())

    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"recibo_{nome_cliente_saida}.pdf",
        mime="application/pdf"
    )