from io import BytesIO
from datetime import datetime, date, timedelta

from flask import request

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)

from app.models.device import Device


# ============================================================
# PALETA CORPORATIVA
# ============================================================

AZUL = colors.HexColor("#2563EB")
AZUL_ESC = colors.HexColor("#0F172A")
AZUL_MUITO_CLARO = colors.HexColor("#EFF6FF")
AZUL_CLARO = colors.HexColor("#DBEAFE")

VERDE = colors.HexColor("#16A34A")
VERDE_CLARO = colors.HexColor("#F0FDF4")

AMARELO = colors.HexColor("#CA8A04")
AMARELO_CLARO = colors.HexColor("#FEFCE8")

VERMELHO = colors.HexColor("#DC2626")
VERMELHO_CLARO = colors.HexColor("#FEF2F2")

CINZA_900 = colors.HexColor("#1E293B")
CINZA_700 = colors.HexColor("#475569")
CINZA_600 = colors.HexColor("#64748B")
CINZA_500 = colors.HexColor("#94A3B8")
CINZA_300 = colors.HexColor("#CBD5E1")
CINZA_200 = colors.HexColor("#E2E8F0")
CINZA_100 = colors.HexColor("#F1F5F9")
CINZA_050 = colors.HexColor("#F8FAFC")

BRANCO = colors.white


# ============================================================
# CONSTANTES DE DOCUMENTO
# ============================================================

PAGE_W, PAGE_H = A4

MARGEM_ESQ = 16 * mm
MARGEM_DIR = 16 * mm
MARGEM_SUP = 29 * mm
MARGEM_INF = 22 * mm

LARGURA_UTIL = PAGE_W - MARGEM_ESQ - MARGEM_DIR


# ============================================================
# FORMATAÇÃO
# ============================================================

def formatar_data(data):
    """Converte date/datetime para dd/mm/aaaa."""
    if not data:
        return "-"

    return data.strftime("%d/%m/%Y")


def normalizar_texto(valor):
    """Normaliza campos para exibição segura."""
    if valor is None:
        return "-"

    texto = str(valor).strip()

    return texto if texto else "-"


def normalizar_status(status):
    return (
        str(status or "")
        .strip()
        .upper()
    )


def obter_cor_status(status):
    status = normalizar_status(status)

    if status == "CALIBRADO":
        return VERDE

    if status == "ATRASADO":
        return VERMELHO

    if status == "DESENVOLVIMENTO":
        return AMARELO

    if status == "INATIVO":
        return CINZA_600

    return CINZA_600


def obter_fundo_status(status):
    status = normalizar_status(status)

    if status == "CALIBRADO":
        return VERDE_CLARO

    if status == "ATRASADO":
        return VERMELHO_CLARO

    if status == "DESENVOLVIMENTO":
        return AMARELO_CLARO

    return CINZA_050


def obter_situacao_calibracao(data_calibracao, hoje=None):
    """
    Determina a situação da próxima calibração.
    Retorna:
        (texto, prazo, cor)
    """
    hoje = hoje or date.today()

    if not data_calibracao:
        return "SEM DATA", "-", CINZA_600

    dias = (data_calibracao - hoje).days

    if dias < 0:
        return (
            "ATRASADA",
            f"{abs(dias)} dias",
            VERMELHO
        )

    if dias == 0:
        return "VENCE HOJE", "Hoje", VERMELHO

    if dias <= 30:
        return (
            "VENCENDO",
            f"{dias} dias",
            AMARELO
        )

    return (
        "VÁLIDA",
        f"{dias} dias",
        VERDE
    )


# ============================================================
# FILTROS
# ============================================================

def obter_clientes():
    """
    Retorna clientes únicos diretamente do cadastro Device.
    Os dados normalmente são alimentados pelo Excel importado.
    """
    clientes = (
        Device.query
        .with_entities(Device.cliente)
        .filter(Device.cliente.isnot(None))
        .distinct()
        .order_by(Device.cliente.asc())
        .all()
    )

    resultado = []

    for item in clientes:
        cliente = normalizar_texto(item[0])

        if cliente != "-":
            resultado.append(cliente)

    return resultado


def obter_filtros_request():
    """
    Lê e normaliza os filtros enviados pelo reports.js.
    """
    tipo = (
        request.args.get(
            "tipo",
            "calibrations"
        )
        .strip()
        .lower()
    )

    cliente = (
        request.args.get(
            "cliente",
            "todos"
        )
        .strip()
    )

    status = (
        request.args.get(
            "status",
            "todos"
        )
        .strip()
        .lower()
    )

    periodo = (
        request.args.get(
            "periodo",
            "current"
        )
        .strip()
        .lower()
    )

    tipos_validos = {
        "metrological",
        "calibrations",
        "inventory",
    }

    status_validos = {
        "todos",
        "calibrado",
        "desenvolvimento",
        "atrasado",
        "inativo",
    }

    periodos_validos = {
        "current",
        "30",
        "60",
        "90",
    }

    if tipo not in tipos_validos:
        tipo = "calibrations"

    if status not in status_validos:
        status = "todos"

    if periodo not in periodos_validos:
        periodo = "current"

    return {
        "tipo": tipo,
        "cliente": cliente or "todos",
        "status": status,
        "periodo": periodo,
    }


def aplicar_filtros(
    dispositivos,
    cliente="todos",
    status="todos",
    periodo="current",
):
    """
    Aplica os filtros selecionados na tela.

    Cliente:
        compara diretamente com Device.cliente.

    Status:
        compara com Device.status.

    Período:
        filtra a próxima calibração para os próximos
        30/60/90 dias. 'current' não restringe por período.
    """
    resultado = list(dispositivos)
    hoje = date.today()

    if cliente and cliente.lower() != "todos":
        resultado = [
            dispositivo
            for dispositivo in resultado
            if normalizar_texto(
                dispositivo.cliente
            ).casefold() == cliente.casefold()
        ]

    if status and status.lower() != "todos":
        status_alvo = status.upper()

        resultado = [
            dispositivo
            for dispositivo in resultado
            if normalizar_status(
                dispositivo.status
            ) == status_alvo
        ]

    if periodo in {"30", "60", "90"}:
        limite = hoje + timedelta(
            days=int(periodo)
        )

        resultado = [
            dispositivo
            for dispositivo in resultado
            if (
                dispositivo.proxima_calibracao
                and hoje <= dispositivo.proxima_calibracao <= limite
            )
        ]

    return sorted(
        resultado,
        key=lambda dispositivo: (
            normalizar_texto(dispositivo.numero)
        )
    )


# ============================================================
# NOMES DOS FILTROS
# ============================================================

def nome_tipo_relatorio(tipo):
    return {
        "metrological": "Relatório Metrológico",
        "calibrations": "Relatório de Calibrações",
        "inventory": "Inventário de Instrumentos",
    }.get(
        tipo,
        "Relatório SIGEM CAL"
    )


def nome_status(status):
    return {
        "todos": "Todos",
        "calibrado": "Calibrado",
        "desenvolvimento": "Desenvolvimento",
        "atrasado": "Atrasado",
        "inativo": "Inativo",
    }.get(
        status,
        status or "Todos"
    )


def nome_periodo(periodo):
    return {
        "current": "Situação atual",
        "30": "Próximos 30 dias",
        "60": "Próximos 60 dias",
        "90": "Próximos 90 dias",
    }.get(
        periodo,
        "Situação atual"
    )


# ============================================================
# ESTILOS
# ============================================================

def criar_estilos():
    estilos = getSampleStyleSheet()

    return {
        "titulo": ParagraphStyle(
            "TituloProfissional",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=23,
            textColor=AZUL_ESC,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),

        "subtitulo": ParagraphStyle(
            "SubtituloProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=CINZA_600,
            spaceAfter=10,
        ),

        "secao": ParagraphStyle(
            "SecaoProfissional",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=AZUL_ESC,
            spaceBefore=5,
            spaceAfter=5,
        ),

        "normal": ParagraphStyle(
            "NormalProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=CINZA_900,
        ),

        "normal_cinza": ParagraphStyle(
            "NormalCinza",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            textColor=CINZA_600,
        ),

        "label": ParagraphStyle(
            "LabelProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.3,
            leading=8,
            textColor=CINZA_600,
        ),

        "valor": ParagraphStyle(
            "ValorProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=AZUL_ESC,
        ),

        "kpi_label": ParagraphStyle(
            "KpiLabelProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=5.8,
            leading=7,
            textColor=CINZA_600,
            alignment=TA_LEFT,
        ),

        "kpi_valor": ParagraphStyle(
            "KpiValorProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=18,
            textColor=AZUL_ESC,
            alignment=TA_LEFT,
        ),

        "tabela_header": ParagraphStyle(
            "TabelaHeaderProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6,
            leading=7,
            textColor=BRANCO,
            alignment=TA_CENTER,
        ),

        "tabela": ParagraphStyle(
            "TabelaProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=5.9,
            leading=7.2,
            textColor=CINZA_900,
        ),

        "tabela_centro": ParagraphStyle(
            "TabelaCentroProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=5.9,
            leading=7.2,
            textColor=CINZA_900,
            alignment=TA_CENTER,
        ),

        "status": ParagraphStyle(
            "StatusProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=5.5,
            leading=7,
            alignment=TA_CENTER,
        ),

        "rodape": ParagraphStyle(
            "RodapeProfissional",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=6,
            leading=7,
            textColor=CINZA_500,
        ),
    }


# ============================================================
# CABEÇALHO / RODAPÉ
# ============================================================

def desenhar_cabecalho_rodape(
    canvas,
    documento,
):
    canvas.saveState()

    # --------------------------------------------------------
    # MARCA
    # --------------------------------------------------------

    x = MARGEM_ESQ
    y = PAGE_H - 15 * mm

    canvas.setFillColor(AZUL)
    canvas.roundRect(
        x,
        y - 4 * mm,
        9 * mm,
        7 * mm,
        1.5 * mm,
        fill=1,
        stroke=0,
    )

    canvas.setFillColor(BRANCO)
    canvas.setFont(
        "Helvetica-Bold",
        7,
    )
    canvas.drawCentredString(
        x + 4.5 * mm,
        y - 1.7 * mm,
        "S"
    )

    canvas.setFillColor(AZUL_ESC)
    canvas.setFont(
        "Helvetica-Bold",
        9,
    )
    canvas.drawString(
        x + 12 * mm,
        y,
        "SIGEM CAL",
    )

    canvas.setFillColor(CINZA_500)
    canvas.setFont(
        "Helvetica",
        5.8,
    )
    canvas.drawRightString(
        PAGE_W - MARGEM_DIR,
        y,
        "GESTÃO INTELIGENTE DE EQUIPAMENTOS DE METROLOGIA",
    )

    # --------------------------------------------------------
    # LINHA DE DESTAQUE
    # --------------------------------------------------------

    canvas.setFillColor(AZUL)
    canvas.roundRect(
        MARGEM_ESQ,
        PAGE_H - 20.5 * mm,
        LARGURA_UTIL,
        0.8 * mm,
        0.4 * mm,
        fill=1,
        stroke=0,
    )

    # --------------------------------------------------------
    # RODAPÉ
    # --------------------------------------------------------

    y_linha = 14.5 * mm

    canvas.setStrokeColor(CINZA_200)
    canvas.setLineWidth(0.45)
    canvas.line(
        MARGEM_ESQ,
        y_linha,
        PAGE_W - MARGEM_DIR,
        y_linha,
    )

    canvas.setFillColor(CINZA_500)
    canvas.setFont(
        "Helvetica",
        5.8,
    )

    canvas.drawString(
        MARGEM_ESQ,
        9.5 * mm,
        "SIGEM CAL • Documento gerado automaticamente",
    )

    canvas.drawCentredString(
        PAGE_W / 2,
        9.5 * mm,
        "Controle interno • Uso corporativo",
    )

    canvas.drawRightString(
        PAGE_W - MARGEM_DIR,
        9.5 * mm,
        f"Página {documento.page}",
    )

    canvas.restoreState()


# ============================================================
# COMPONENTES VISUAIS
# ============================================================

def criar_card_kpi(
    label,
    valor,
    observacao,
    cor,
    estilos,
):
    conteudo = [
        [
            Paragraph(
                label.upper(),
                estilos["kpi_label"],
            )
        ],
        [
            Paragraph(
                str(valor),
                estilos["kpi_valor"],
            )
        ],
        [
            Paragraph(
                observacao,
                estilos["normal_cinza"],
            )
        ],
    ]

    tabela = Table(
        conteudo,
        colWidths=[34.8 * mm],
        rowHeights=[6 * mm, 9 * mm, 7 * mm],
    )

    tabela.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                BRANCO,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.55,
                CINZA_200,
            ),
            (
                "LINEBEFORE",
                (0, 0),
                (0, -1),
                2.2,
                cor,
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
        ])
    )

    return tabela


def criar_badge(
    texto,
    cor,
    fundo,
    estilos,
):
    estilo = ParagraphStyle(
        f"Badge_{texto}",
        parent=estilos["status"],
        textColor=cor,
    )

    badge = Table(
        [[
            Paragraph(
                texto,
                estilo,
            )
        ]],
        colWidths=[25 * mm],
    )

    badge.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                fundo,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.35,
                fundo,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
        ])
    )

    return badge


def criar_ficha_filtros(
    tipo,
    cliente,
    status,
    periodo,
    estilos,
):
    dados = [
        [
            Paragraph(
                "RELATÓRIO",
                estilos["label"],
            ),
            Paragraph(
                nome_tipo_relatorio(tipo),
                estilos["valor"],
            ),
            Paragraph(
                "CLIENTE",
                estilos["label"],
            ),
            Paragraph(
                "Todos os clientes"
                if cliente.lower() == "todos"
                else cliente,
                estilos["valor"],
            ),
        ],
        [
            Paragraph(
                "STATUS",
                estilos["label"],
            ),
            Paragraph(
                nome_status(status),
                estilos["valor"],
            ),
            Paragraph(
                "PERÍODO",
                estilos["label"],
            ),
            Paragraph(
                nome_periodo(periodo),
                estilos["valor"],
            ),
        ],
    ]

    tabela = Table(
        dados,
        colWidths=[
            24 * mm,
            62 * mm,
            24 * mm,
            64 * mm,
        ],
    )

    tabela.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                CINZA_050,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                CINZA_200,
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.3,
                CINZA_200,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
        ])
    )

    return tabela


# ============================================================
# KPIs
# ============================================================

def calcular_kpis(dispositivos):
    hoje = date.today()

    total = len(dispositivos)
    calibrados = 0
    desenvolvimento = 0
    atrasadas = 0
    vencendo = 0
    validas = 0
    sem_data = 0
    inativos = 0

    for dispositivo in dispositivos:
        status = normalizar_status(
            dispositivo.status
        )

        if status == "CALIBRADO":
            calibrados += 1

        elif status == "DESENVOLVIMENTO":
            desenvolvimento += 1

        elif status == "INATIVO":
            inativos += 1

        if not dispositivo.proxima_calibracao:
            sem_data += 1
            continue

        dias = (
            dispositivo.proxima_calibracao - hoje
        ).days

        if dias < 0:
            atrasadas += 1

        elif dias <= 30:
            vencendo += 1

        else:
            validas += 1

    return {
        "total": total,
        "calibrados": calibrados,
        "desenvolvimento": desenvolvimento,
        "atrasadas": atrasadas,
        "vencendo": vencendo,
        "validas": validas,
        "sem_data": sem_data,
        "inativos": inativos,
    }


# ============================================================
# TABELA DE CALIBRAÇÕES
# ============================================================

def criar_tabela_calibracoes(
    dispositivos,
    estilos,
):
    hoje = date.today()

    dados = [
        [
            Paragraph("DC", estilos["tabela_header"]),
            Paragraph("Instrumento", estilos["tabela_header"]),
            Paragraph("Cliente", estilos["tabela_header"]),
            Paragraph("Última", estilos["tabela_header"]),
            Paragraph("Próxima", estilos["tabela_header"]),
            Paragraph("Prazo", estilos["tabela_header"]),
            Paragraph("Situação", estilos["tabela_header"]),
        ]
    ]

    situacoes = []

    for dispositivo in dispositivos:
        situacao, prazo, cor = obter_situacao_calibracao(
            dispositivo.proxima_calibracao,
            hoje,
        )

        situacoes.append(
            (situacao, cor)
        )

        dados.append([
            Paragraph(
                normalizar_texto(dispositivo.numero),
                estilos["tabela_centro"],
            ),

            Paragraph(
                normalizar_texto(dispositivo.descricao),
                estilos["tabela"],
            ),

            Paragraph(
                normalizar_texto(dispositivo.cliente),
                estilos["tabela"],
            ),

            Paragraph(
                formatar_data(
                    dispositivo.ultima_calibracao
                ),
                estilos["tabela_centro"],
            ),

            Paragraph(
                formatar_data(
                    dispositivo.proxima_calibracao
                ),
                estilos["tabela_centro"],
            ),

            Paragraph(
                prazo,
                estilos["tabela_centro"],
            ),

            criar_badge(
                situacao,
                cor,
                obter_fundo_status(
                    "ATRASADO"
                    if situacao == "ATRASADA"
                    else "DESENVOLVIMENTO"
                    if situacao == "VENCENDO"
                    else "CALIBRADO"
                    if situacao == "VÁLIDA"
                    else "INATIVO"
                ),
                estilos,
            ),
        ])

    tabela = Table(
        dados,
        colWidths=[
            18 * mm,
            42 * mm,
            30 * mm,
            22 * mm,
            22 * mm,
            19 * mm,
            27 * mm,
        ],
        repeatRows=1,
        splitByRow=1,
    )

    comandos = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            AZUL_ESC,
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            BRANCO,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.3,
            CINZA_200,
        ),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [
                BRANCO,
                CINZA_050,
            ],
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
    ]

    tabela.setStyle(
        TableStyle(comandos)
    )

    return tabela


# ============================================================
# TABELA DE INVENTÁRIO
# ============================================================

def criar_tabela_inventario(
    dispositivos,
    estilos,
):
    dados = [
        [
            Paragraph("DC", estilos["tabela_header"]),
            Paragraph("Instrumento", estilos["tabela_header"]),
            Paragraph("Cliente", estilos["tabela_header"]),
            Paragraph("Part Number", estilos["tabela_header"]),
            Paragraph("Última calibração", estilos["tabela_header"]),
            Paragraph("Próxima calibração", estilos["tabela_header"]),
            Paragraph("Status", estilos["tabela_header"]),
        ]
    ]

    for dispositivo in dispositivos:
        status = normalizar_status(
            dispositivo.status
        )

        status_texto = (
            dispositivo.status
            if dispositivo.status
            else "Não informado"
        )

        cor = obter_cor_status(status)
        fundo = obter_fundo_status(status)

        dados.append([
            Paragraph(
                normalizar_texto(dispositivo.numero),
                estilos["tabela_centro"],
            ),
            Paragraph(
                normalizar_texto(dispositivo.descricao),
                estilos["tabela"],
            ),
            Paragraph(
                normalizar_texto(dispositivo.cliente),
                estilos["tabela"],
            ),
            Paragraph(
                normalizar_texto(dispositivo.part_number),
                estilos["tabela"],
            ),
            Paragraph(
                formatar_data(
                    dispositivo.ultima_calibracao
                ),
                estilos["tabela_centro"],
            ),
            Paragraph(
                formatar_data(
                    dispositivo.proxima_calibracao
                ),
                estilos["tabela_centro"],
            ),
            criar_badge(
                str(status_texto).upper(),
                cor,
                fundo,
                estilos,
            ),
        ])

    tabela = Table(
        dados,
        colWidths=[
            17 * mm,
            38 * mm,
            28 * mm,
            28 * mm,
            27 * mm,
            27 * mm,
            25 * mm,
        ],
        repeatRows=1,
        splitByRow=1,
    )

    tabela.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                AZUL_ESC,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                BRANCO,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                CINZA_200,
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    BRANCO,
                    CINZA_050,
                ],
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
        ])
    )

    return tabela


# ============================================================
# TABELA METROLÓGICA
# ============================================================

def criar_tabela_metrologica(
    dispositivos,
    estilos,
):
    hoje = date.today()

    dados = [
        [
            Paragraph("DC", estilos["tabela_header"]),
            Paragraph("Instrumento", estilos["tabela_header"]),
            Paragraph("Cliente", estilos["tabela_header"]),
            Paragraph("Próxima", estilos["tabela_header"]),
            Paragraph("Prazo", estilos["tabela_header"]),
            Paragraph("Situação", estilos["tabela_header"]),
            Paragraph("Status", estilos["tabela_header"]),
        ]
    ]

    for dispositivo in dispositivos:
        situacao, prazo, cor = obter_situacao_calibracao(
            dispositivo.proxima_calibracao,
            hoje,
        )

        status = normalizar_status(
            dispositivo.status
        )

        status_texto = (
            dispositivo.status
            if dispositivo.status
            else "Não informado"
        )

        dados.append([
            Paragraph(
                normalizar_texto(dispositivo.numero),
                estilos["tabela_centro"],
            ),
            Paragraph(
                normalizar_texto(dispositivo.descricao),
                estilos["tabela"],
            ),
            Paragraph(
                normalizar_texto(dispositivo.cliente),
                estilos["tabela"],
            ),
            Paragraph(
                formatar_data(
                    dispositivo.proxima_calibracao
                ),
                estilos["tabela_centro"],
            ),
            Paragraph(
                prazo,
                estilos["tabela_centro"],
            ),
            criar_badge(
                situacao,
                cor,
                (
                    VERMELHO_CLARO
                    if situacao in {"ATRASADA", "VENCE HOJE"}
                    else AMARELO_CLARO
                    if situacao == "VENCENDO"
                    else VERDE_CLARO
                    if situacao == "VÁLIDA"
                    else CINZA_100
                ),
                estilos,
            ),
            criar_badge(
                str(status_texto).upper(),
                obter_cor_status(status),
                obter_fundo_status(status),
                estilos,
            ),
        ])

    tabela = Table(
        dados,
        colWidths=[
            17 * mm,
            42 * mm,
            29 * mm,
            25 * mm,
            20 * mm,
            30 * mm,
            27 * mm,
        ],
        repeatRows=1,
        splitByRow=1,
    )

    tabela.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                AZUL_ESC,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                BRANCO,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                CINZA_200,
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    BRANCO,
                    CINZA_050,
                ],
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
        ])
    )

    return tabela


# ============================================================
# GERADOR PRINCIPAL
# ============================================================

def gerar_relatorio(
    tipo="calibrations",
    cliente="todos",
    status="todos",
    periodo="current",
):
    """
    Gera o relatório profissional e retorna BytesIO.
    """

    agora = datetime.now()

    numero_documento = (
        f"SIGEM-{agora.strftime('%Y%m%d-%H%M%S')}"
    )

    # --------------------------------------------------------
    # CONSULTA
    # --------------------------------------------------------

    dispositivos = (
        Device.query
        .order_by(Device.numero.asc())
        .all()
    )

    # --------------------------------------------------------
    # FILTROS
    # --------------------------------------------------------

    dispositivos = aplicar_filtros(
        dispositivos,
        cliente=cliente,
        status=status,
        periodo=periodo,
    )

    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------

    kpis = calcular_kpis(
        dispositivos
    )

    # --------------------------------------------------------
    # DOCUMENTO
    # --------------------------------------------------------

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGEM_DIR,
        leftMargin=MARGEM_ESQ,
        topMargin=MARGEM_SUP,
        bottomMargin=MARGEM_INF,
        title=nome_tipo_relatorio(tipo),
        author="SIGEM CAL",
        subject="Relatório de Gestão de Equipamentos de Metrologia",
        creator="SIGEM CAL",
        keywords="metrologia, calibração, instrumentos, SIGEM CAL",
    )

    estilos = criar_estilos()

    elementos = []

    # ========================================================
    # CABEÇALHO DO DOCUMENTO
    # ========================================================

    elementos.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    elementos.append(
        Paragraph(
            nome_tipo_relatorio(tipo).upper(),
            estilos["titulo"],
        )
    )

    descricao_tipo = {
        "metrological":
            "Visão executiva da situação metrológica dos instrumentos.",
        "calibrations":
            "Controle e acompanhamento do ciclo de calibração dos instrumentos.",
        "inventory":
            "Relação consolidada dos instrumentos cadastrados no SIGEM CAL.",
    }.get(
        tipo,
        "Relatório gerencial do SIGEM CAL.",
    )

    elementos.append(
        Paragraph(
            descricao_tipo,
            estilos["subtitulo"],
        )
    )

    # --------------------------------------------------------
    # IDENTIFICAÇÃO
    # --------------------------------------------------------

    identificacao = Table(
        [[
            Paragraph(
                "<b>DOCUMENTO</b><br/>"
                f"{numero_documento}",
                estilos["normal"],
            ),
            Paragraph(
                "<b>EMISSÃO</b><br/>"
                f"{agora.strftime('%d/%m/%Y às %H:%M')}",
                estilos["normal"],
            ),
            Paragraph(
                "<b>SISTEMA</b><br/>"
                "SIGEM CAL",
                estilos["normal"],
            ),
        ]],
        colWidths=[
            63 * mm,
            63 * mm,
            63 * mm,
        ],
    )

    identificacao.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                CINZA_050,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                CINZA_200,
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.3,
                CINZA_200,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
        ])
    )

    elementos.append(
        identificacao
    )

    elementos.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # ========================================================
    # FILTROS
    # ========================================================

    elementos.append(
        Paragraph(
            "Parâmetros do relatório",
            estilos["secao"],
        )
    )

    elementos.append(
        criar_ficha_filtros(
            tipo,
            cliente,
            status,
            periodo,
            estilos,
        )
    )

    elementos.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # ========================================================
    # RESUMO EXECUTIVO
    # ========================================================

    elementos.append(
        Paragraph(
            "Resumo executivo",
            estilos["secao"],
        )
    )

    cards = [
        criar_card_kpi(
            "Instrumentos",
            kpis["total"],
            "Registros no relatório",
            AZUL,
            estilos,
        ),
        criar_card_kpi(
            "Calibrados",
            kpis["calibrados"],
            "Status cadastrado",
            VERDE,
            estilos,
        ),
        criar_card_kpi(
            "Vencendo",
            kpis["vencendo"],
            "Até 30 dias",
            AMARELO,
            estilos,
        ),
        criar_card_kpi(
            "Atrasados",
            kpis["atrasadas"],
            "Requerem atenção",
            VERMELHO,
            estilos,
        ),
        criar_card_kpi(
            "Sem data",
            kpis["sem_data"],
            "Próxima calibração",
            CINZA_500,
            estilos,
        ),
    ]

    tabela_kpis = Table(
        [cards],
        colWidths=[
            34.8 * mm,
            34.8 * mm,
            34.8 * mm,
            34.8 * mm,
            34.8 * mm,
        ],
    )

    tabela_kpis.setStyle(
        TableStyle([
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
        ])
    )

    elementos.append(
        tabela_kpis
    )

    elementos.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    # ========================================================
    # INDICADOR DE CONFORMIDADE
    # ========================================================

    if kpis["total"] > 0:
        conformidade = (
            kpis["validas"]
            / kpis["total"]
        ) * 100
    else:
        conformidade = 0

    conformidade = round(
        conformidade,
        1,
    )

    barra = Table(
        [[
            Paragraph(
                "<b>Índice de instrumentos dentro do prazo</b>",
                estilos["normal"],
            ),
            Paragraph(
                f"<b>{conformidade:.1f}%</b>",
                estilos["valor"],
            ),
        ]],
        colWidths=[
            145 * mm,
            30 * mm,
        ],
    )

    barra.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                AZUL_MUITO_CLARO,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                AZUL_CLARO,
            ),
            (
                "ALIGN",
                (1, 0),
                (1, 0),
                "RIGHT",
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
        ])
    )

    elementos.append(
        barra
    )

    elementos.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    # ========================================================
    # RELAÇÃO PRINCIPAL
    # ========================================================

    titulo_tabela = {
        "calibrations":
            "Controle de calibrações",
        "inventory":
            "Inventário de instrumentos",
        "metrological":
            "Visão metrológica dos instrumentos",
    }.get(
        tipo,
        "Relação de instrumentos",
    )

    elementos.append(
        Paragraph(
            titulo_tabela,
            estilos["secao"],
        )
    )

    if not dispositivos:
        vazio = Table(
            [[
                Paragraph(
                    "<b>Nenhum instrumento encontrado</b><br/>"
                    "Os filtros selecionados não retornaram registros.",
                    estilos["normal"],
                )
            ]],
            colWidths=[
                LARGURA_UTIL
            ],
        )

        vazio.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    CINZA_050,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    CINZA_200,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    18,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    18,
                ),
            ])
        )

        elementos.append(
            vazio
        )

    elif tipo == "inventory":
        elementos.append(
            criar_tabela_inventario(
                dispositivos,
                estilos,
            )
        )

    elif tipo == "metrological":
        elementos.append(
            criar_tabela_metrologica(
                dispositivos,
                estilos,
            )
        )

    else:
        elementos.append(
            criar_tabela_calibracoes(
                dispositivos,
                estilos,
            )
        )

    # ========================================================
    # NOTA DE RODAPÉ DO DOCUMENTO
    # ========================================================

    elementos.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=CINZA_200,
            spaceBefore=2,
            spaceAfter=5,
        )
    )

    elementos.append(
        Paragraph(
            "<b>Nota:</b> Este relatório apresenta os dados "
            "registrados no SIGEM CAL no momento da emissão. "
            "A situação de prazo é calculada com base na data "
            "de emissão do documento.",
            estilos["rodape"],
        )
    )

    elementos.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    elementos.append(
        Paragraph(
            f"Documento {numero_documento} • "
            f"Emitido em {agora.strftime('%d/%m/%Y às %H:%M')}",
            estilos["rodape"],
        )
    )

    # ========================================================
    # BUILD
    # ========================================================

    documento.build(
        elementos,
        onFirstPage=desenhar_cabecalho_rodape,
        onLaterPages=desenhar_cabecalho_rodape,
    )

    buffer.seek(0)

    return buffer


# ============================================================
# COMPATIBILIDADE
# ============================================================

def gerar_relatorio_calibracoes():
    """
    Compatibilidade com chamadas antigas.
    """
    return gerar_relatorio(
        tipo="calibrations",
        cliente="todos",
        status="todos",
        periodo="current",
    )