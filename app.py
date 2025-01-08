import streamlit as st
from fpdf import FPDF
from PIL import Image
import datetime
from io import BytesIO
from num2words import num2words  # Biblioteca para converter números em texto
import locale  # Para manipulação de data em português

class CustomPDF(FPDF):
    def header(self):
        pass  # Remover o cabeçalho automático

def generate_pdf(nome_cliente, quantidade, valor, logo_path, assinatura_path):
    pdf = CustomPDF()
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')

    # pdf.set_auto_page_break(auto=True, margin=20)  # Configurar quebra automática de página
    pdf.set_left_margin(20)  # Margem esquerda de 3 cm (ABNT)
    pdf.set_right_margin(20)  # Margem direita de 2 cm (ABNT)
    pdf.add_page()

    # Adicionar logo centralizada no topo
    pdf.image(logo_path, x=80, y=30, w=35)

    # Adicionar título "RECIBO DE PAGAMENTO"
    pdf.set_font('Times', 'B', 18)
    pdf.ln(60)  # 5 células (5 x 8mm = 40mm)
    pdf.cell(0, 10, 'RECIBO DE PAGAMENTO', ln=True, align='C')

    # Adicionar texto principal do recibo com valores por extenso
    pdf.set_font('Times', '', 12)  # Fonte Times New Roman
    pdf.ln(25)  # 5 células (5 x 2mm = 10mm)
    valor_extenso = num2words(valor, lang='pt_BR', to='currency')
    quantidade_extenso = num2words(quantidade, lang='pt_BR')
    texto_recibo = (
        f"Eu, Maria Verônica Gomes Pereira Avelino, CPF: 047.589.934-24, recebi do(a) {nome_cliente} "
        f"o valor de R$ {valor:.2f} ({valor_extenso}), referente ao fornecimento de "
        f"{quantidade} ({quantidade_extenso}) salgados."
    )

    # Configurar espaçamento entre linhas e margens para o texto descritivo
    pdf.multi_cell(0, 8, texto_recibo, align='J')  # Justificado com espaçamento ajustado

    # Adicionar cidade e data
    pdf.ln(40)
    data_atual = datetime.datetime.now().strftime('%d de %B de %Y')
    pdf.cell(0, 10, f"Lajes/RN, {data_atual}", ln=True, align='C')

    # Adicionar assinatura digital
    pdf.ln(50)  # Ajustar espaço antes da assinatura
    pdf.image(assinatura_path, x=65, w=80)  # Aumentar assinatura e centralizar
    pdf.ln(-5)  # Espaço reduzido entre assinatura e linha
    pdf.set_font('Times', '', 11)
    pdf.cell(0, 10, "_______________________________________", ln=True, align='C')  # Linha da assinatura
    pdf.ln(-5)  # Espaço reduzido entre linha e nome
    pdf.cell(0, 10, "Maria Verônica Gomes Pereira Avelino", ln=True, align='C')  # Nome completo

    # Gerar o PDF em memória
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)

# Interface do Streamlit
st.title('Gerador de Recibo')

nome_cliente = st.text_input('Nome do Cliente')
quantidade = st.number_input('Quantidade de Itens', min_value=1, step=1)
valor = st.number_input('Valor Total (R$)', min_value=0.0, step=0.01)

# Caminho dos arquivos (substitua pelos seus caminhos reais)
logo_path = 'https://github.com/jsaj/recibo/blob/main/images/LOGO%20Veronica.png'
assinatura_path = 'https://github.com/jsaj/recibo/blob/main/images/ass_veronica.png'

if st.button('Gerar PDF'):
    pdf_bytes = generate_pdf(nome_cliente, quantidade, valor, logo_path, assinatura_path)

    nome_cliente_saida = nome_cliente.lower().split(" ")
    if len(nome_cliente_saida) > 1:
        nome_cliente_saida = "_".join(nome_cliente_saida)
    else:
        nome_cliente_saida = nome_cliente_saida[0]

    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"recibo_{nome_cliente_saida}.pdf",
        mime="application/pdf"
    )
