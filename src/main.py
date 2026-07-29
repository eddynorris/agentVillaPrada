"""
Servidor Principal Backend FastAPI — Agente Villa Prada.
Expone los webhooks de WhatsApp y Telegram, y endpoints REST para la operación del negocio.
"""
import os
import logging
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from src.calculator import calcular_cotizacion, CotizacionRequest
from src import database
from src.services.gemini_agent import VillaPradaAgent
from src.services.chef_service import generar_lista_compras_chef
from src.services.contract_service import generar_contrato_pdf
from src.services import telegram_owner_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("villa_prada_app")

app = FastAPI(
    title="Agente Villa Prada API",
    description="Backend oficial del Agente Secretario Comercial de Villa Prada",
    version="1.0.0"
)

agent = VillaPradaAgent()


@app.get("/health")
def health_check():
    """Endpoint de estado del servicio."""
    return {"status": "ok", "app": "Agente Villa Prada", "version": "1.0.0"}


@app.post("/api/cotizar")
def api_cotizar(req: CotizacionRequest):
    """Endpoint REST para cotizar un evento."""
    try:
        res = calcular_cotizacion(req)
        return res.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/eventos/{evento_id}/contrato")
def api_generar_contrato(evento_id: str):
    """Genera y retorna el contrato PDF de un evento."""
    evento = database.obtener_evento_por_id(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    pdf_path = generar_contrato_pdf(evento)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"contrato_villa_prada_{evento_id[:8]}.pdf"
    )


@app.get("/api/eventos/{evento_id}/lista-chef")
def api_lista_chef(evento_id: str):
    """Obtiene la lista de compras de insumos para el chef."""
    evento = database.obtener_evento_por_id(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    lista = generar_lista_compras_chef(
        nro_invitados=evento['nro_invitados'],
        tipo_evento=evento['tipo_evento'],
        paquete=evento['paquete']
    )
    return lista


@app.post("/webhook/whatsapp")
async def webhook_whatsapp(request: Request):
    """
    Webhook para recibir mensajes de clientes desde WhatsApp (Meta Cloud API / Conector).
    """
    try:
        body = await request.json()
        # Estructura simplificada para mensaje de WhatsApp
        user_phone = body.get("phone", "000000000")
        user_message = body.get("message", "")

        if not user_message:
            return JSONResponse({"status": "ignored", "reason": "empty_message"})

        # Procesar con el Agente Gemini
        reply = agent.process_message(user_message)
        
        # Si se creó una pre-reserva, notificar al dueño por Telegram
        if reply.get("action") == "prereserva_creada":
            evento = reply.get("evento")
            cliente = database.obtener_o_crear_cliente("Cliente WhatsApp", user_phone)
            telegram_owner_bot.notificar_nueva_prereserva(evento, cliente)

        return JSONResponse({
            "status": "success",
            "reply": reply["text"],
            "action": reply.get("action")
        })

    except Exception as e:
        logger.error(f"Error en webhook WhatsApp: {e}", exc_info=True)
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@app.post("/webhook/telegram")
async def webhook_telegram(request: Request):
    """
    Webhook para recibir callbacks e interacciones de Telegram del Dueño y Staff.
    """
    try:
        body = await request.json()
        callback = body.get("callback_query")
        if callback:
            data = callback.get("data", "")
            chat_id = callback.get("message", {}).get("chat", {}).get("id")
            
            # Manejar validación de pago por el dueño
            if data.startswith("validar_pago:"):
                _, evento_id, tipo_pago = data.split(":")
                pago = database.registrar_pago(evento_id, tipo_pago, 300.0, "Yape/Plin (Verificado)")
                telegram_owner_bot.enviar_alerta_duenio(
                    f"✅ <b>Pago Verificado exitosamente!</b>\n\nEl evento #{evento_id[:8]} pasó a estado <b>PRERESERVADO</b>."
                )
            
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Error en webhook Telegram: {e}", exc_info=True)
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
