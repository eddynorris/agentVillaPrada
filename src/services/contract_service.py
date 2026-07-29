"""
Servicio de Generación Automática de Contratos PDF — Villa Prada.
Genera un contrato PDF profesional utilizando ReportLab.
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generar_contrato_pdf(evento_data: dict, output_path: str = None) -> str:
    """
    Genera el contrato PDF para un evento y retorna la ruta del archivo generado.
    
    Args:
        evento_data: Diccionario con datos del evento y cliente.
        output_path: Ruta personalizada para guardar el PDF.
    """
    if not output_path:
        os.makedirs('/tmp/contratos', exist_ok=True)
        evento_id_short = str(evento_data.get('id', 'temp'))[:8]
        output_path = f"/tmp/contratos/contrato_villa_prada_{evento_id_short}.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E293B'),
        alignment=1  # Center
    )
    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )
    style_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=10,
        spaceAfter=6
    )
    style_body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    elements = []

    # Encabezado
    elements.append(Paragraph("<b>LOCAL DE EVENTOS VILLA PRADA</b>", style_title))
    elements.append(Paragraph("Contrato de Prestación de Servicios de Eventos & Recepciones", style_subtitle))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3B82F6'), spaceBefore=5, spaceAfter=15))

    # Datos del Contrato
    cliente_nombre = evento_data.get('cliente_nombre', 'Cliente')
    cliente_doc = evento_data.get('cliente_doc', 'No especificado')
    cliente_tel = evento_data.get('cliente_telefono', 'No especificado')
    fecha_evento = str(evento_data.get('fecha_evento', ''))
    turno = str(evento_data.get('turno', '')).upper()
    nro_invitados = evento_data.get('nro_invitados', 100)
    total_estimado = float(evento_data.get('total_estimado', 0))
    adelanto_30pct = round(total_estimado * 0.30, 2)
    saldo_restante = round(total_estimado - adelanto_30pct - 300.0, 2)

    data_tabla_info = [
        [Paragraph("<b>CONTRATANTE:</b>", style_body), Paragraph(f"{cliente_nombre}", style_body),
         Paragraph("<b>DNI/RUC:</b>", style_body), Paragraph(f"{cliente_doc}", style_body)],
        [Paragraph("<b>TELÉFONO:</b>", style_body), Paragraph(f"{cliente_tel}", style_body),
         Paragraph("<b>FECHA EVENTO:</b>", style_body), Paragraph(f"{fecha_evento}", style_body)],
        [Paragraph("<b>TIPO EVENTO:</b>", style_body), Paragraph(f"{str(evento_data.get('tipo_evento')).upper()}", style_body),
         Paragraph("<b>TURNO:</b>", style_body), Paragraph(f"{turno}", style_body)],
        [Paragraph("<b>N° INVITADOS:</b>", style_body), Paragraph(f"{nro_invitados} personas", style_body),
         Paragraph("<b>DURACIÓN:</b>", style_body), Paragraph("8 Horas + 1h Tolerancia", style_body)]
    ]

    t_info = Table(data_tabla_info, colWidths=[100, 160, 100, 160])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 15))

    # Detalle Financiero
    elements.append(Paragraph("<b>CRONOGRAMA Y RESUMEN FINANCIERO</b>", style_heading))
    data_financiera = [
        ["Concepto", "Monto (S/)", "Estado"],
        ["Pre-reserva (Bloqueo de fecha)", "S/ 300.00", "PAGADO / REGISTRADO"],
        ["Adelanto 30% (Suscripción de Contrato)", f"S/ {adelanto_30pct:.2f}", "A PAGAR"],
        ["Saldo Pendiente (Cancelación 48h antes del evento)", f"S/ {max(0, saldo_restante):.2f}", "PENDIENTE"],
        ["TOTAL CONTRATADO", f"S/ {total_estimado:.2f}", "-"]
    ]
    t_fin = Table(data_financiera, colWidths=[260, 130, 130])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(t_fin)
    elements.append(Spacer(1, 15))

    # Cláusulas Principales
    elements.append(Paragraph("<b>CLÁUSULAS DEL SERVICIO</b>", style_heading))
    clausulas = (
        "<b>1. DURACIÓN Y TOLERANCIA:</b> El servicio comprende 8 horas efectivas de evento más 1 hora de tolerancia.<br/>"
        "<b>2. HORAS ADICIONALES:</b> Cada hora adicional se cobrará a S/ 300.00 Soles.<br/>"
        "<b>3. DECORACIÓN Y EQUIPAMIENTO:</b> Incluye estructura frontal, zona selfie en paleta de colores a elección y diseño alusivo en la pantalla gigante.<br/>"
        "<b>4. CANCELLACIÓN:</b> El monto de pre-reserva (S/ 300) garantiza la reserva de fecha y no es reembolsable."
    )
    elements.append(Paragraph(clausulas, style_body))
    elements.append(Spacer(1, 30))

    # Firmas
    data_firmas = [
        ["__________________________________", "__________________________________"],
        ["LOCAL DE EVENTOS VILLA PRADA", f"CLIENTE: {cliente_nombre}"],
        ["Representante Legal", f"DNI/RUC: {cliente_doc}"]
    ]
    t_firmas = Table(data_firmas, colWidths=[260, 260])
    t_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
    ]))
    elements.append(t_firmas)

    doc.build(elements)
    return output_path
