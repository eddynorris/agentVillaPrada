"""
Servicio de Alertas y Operaciones en Telegram para el Dueño y Personal — Villa Prada.
"""
import os
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_OWNER_CHAT_ID = os.environ.get("TELEGRAM_OWNER_CHAT_ID")


def enviar_alerta_duenio(mensaje_html: str, reply_markup: dict = None) -> bool:
    """Envía un mensaje formateado en HTML al chat de Telegram del dueño."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    owner_chat_id = os.environ.get("TELEGRAM_OWNER_CHAT_ID")
    
    if not token or not owner_chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN u OWNER_CHAT_ID no configurados. Alerta no enviada.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": owner_chat_id,
        "text": mensaje_html,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error al enviar alerta a Telegram: {e}")
        return False


def notificar_nueva_prereserva(evento: dict, cliente: dict) -> bool:
    """Notifica al dueño sobre una nueva pre-reserva de S/ 300 creada por un cliente."""
    msg = (
        f"🔔 <b>¡NUEVA PRE-RESERVA SOLICITADA!</b>\n\n"
        f"👤 <b>Cliente:</b> {cliente.get('nombre')} ({cliente.get('telefono')})\n"
        f"🎉 <b>Evento:</b> {str(evento.get('tipo_evento')).upper()} ({str(evento.get('paquete')).upper()})\n"
        f"📅 <b>Fecha:</b> {evento.get('fecha_evento')} ({str(evento.get('turno')).upper()})\n"
        f"👥 <b>Invitados:</b> {evento.get('nro_invitados')} personas\n"
        f"💰 <b>Total Cotizado:</b> S/ {float(evento.get('total_estimado', 0)):.2f}\n\n"
        f"📌 <b>Acción Requerida:</b> Verificar abono de pre-reserva de <b>S/ 300.00</b>."
    )
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Validar S/300 (Pre-reserva)", "callback_data": f"validar_pago:{evento['id']}:prereserva_300"},
                {"text": "📄 Ver Contrato Borrador", "callback_data": f"ver_contrato:{evento['id']}"}
            ]
        ]
    }
    return enviar_alerta_duenio(msg, keyboard)


def notificar_convocatoria_mozos(evento: dict, mozos_requeridos: int) -> str:
    """Genera el mensaje formateado para convocar mozos al evento."""
    msg = (
        f"📢 <b>CONVOCATORIA DE PERSONAL — VILLA PRADA</b>\n\n"
        f"🎉 <b>Evento:</b> {str(evento.get('tipo_evento')).upper()}\n"
        f"📅 <b>Fecha:</b> {evento.get('fecha_evento')} - Turno {str(evento.get('turno')).upper()}\n"
        f"👥 <b>Invitados:</b> {evento.get('nro_invitados')} pax\n"
        f"👔 <b>Mozos Necesarios:</b> {mozos_requeridos} mozos\n"
        f"💵 <b>Pago por Turno (8h):</b> S/ 70.00 (Incluye cena)\n\n"
        f"Por favor presiona el botón abajo para confirmar tu asistencia:"
    )
    return msg
