"""
Motor de IA y NLU del Agente Secretario — Villa Prada.
Usa Gemini con tool calling moderno para cotizaciones, reservas e interacción con clientes.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

import google.genai as genai
from google.genai import types

from src.calculator import calcular_cotizacion, CotizacionRequest
from src import database

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Eres el Asistente Virtual Oficial y Secretario Comercial del Local de Eventos 'Villa Prada' en Andahuaylas, Perú.\n"
    "Tu trato es altamente profesional, cálido, formal y eficiente. Tu objetivo es cotizar eventos, verificar disponibilidad "
    "en calendario y guiar al cliente para realizar la pre-reserva de S/ 300.\n\n"
    "Reglas Comerciales de Villa Prada:\n"
    "- Servicios: Bodas, Quinceañeros, Eventos Institucionales y Alquiler de Local Implementado.\n"
    "- Duración base: 8 horas efectivas + 1 hora de tolerancia. Hora extra: S/ 300.\n"
    "- Tarifario por persona:\n"
    "  * Boda / 15 Años Premium: S/ 120 por persona.\n"
    "  * Boda / 15 Años Básico: S/ 100 por persona.\n"
    "  * Institucional: S/ 60 por persona.\n"
    "  * Alquiler de Local Implementado: S/ 4,000 (hasta 100 personas).\n"
    "- Descuento por Volumen (se aplica automáticamente al cotizar):\n"
    "  * <100 personas: +5% sobre base.\n"
    "  * 100-149 personas: Tarifa base.\n"
    "  * 150-199 personas: 5% de descuento.\n"
    "  * 200+ personas: 10% de descuento.\n"
    "- Proceso de Reserva:\n"
    "  1. Pre-reserva: S/ 300 (bloquea la fecha temporalmente).\n"
    "  2. Firma de Contrato: 30% de adelanto del total del evento.\n"
    "- Decoración Incluida: Frontal decorado + Zona Selfie (colores a elección del cliente) + Diseño alusivo en la Pantalla Gigante.\n\n"
    "Instrucciones:\n"
    "- Responde siempre de forma clara, amable y estructurada.\n"
    "- Usa las herramientas (functions) para calcular cotizaciones reales y verificar disponibilidad de fechas.\n"
    "- NUNCA inventes precios o fechas disponibles; usa las herramientas correspondientes.\n"
)

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="cotizar_evento",
                description="Calcula la cotización exacta para un evento aplicando descuentos por volumen y costos de horas extras.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "tipo_evento": types.Schema(
                            type="STRING", description="Tipo de evento.", enum=["boda", "quinceanero", "institucional", "alquiler_local"]
                        ),
                        "paquete": types.Schema(
                            type="STRING", description="Paquete del evento.", enum=["basico", "premium", "no_aplica"]
                        ),
                        "nro_invitados": types.Schema(type="INTEGER", description="Número total de personas/invitados."),
                        "horas_extras": types.Schema(type="INTEGER", description="Número de horas adicionales (default 0)."),
                    },
                    required=["tipo_evento", "nro_invitados"],
                ),
            ),
            types.FunctionDeclaration(
                name="verificar_disponibilidad",
                description="Verifica si una fecha y turno (almuerzo o cena) están disponibles en el calendario de Villa Prada.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "fecha_evento": types.Schema(type="STRING", description="Fecha del evento en formato YYYY-MM-DD."),
                        "turno": types.Schema(type="STRING", description="Turno deseado.", enum=["almuerzo", "cena"]),
                    },
                    required=["fecha_evento", "turno"],
                ),
            ),
            types.FunctionDeclaration(
                name="crear_prereserva",
                description="Crea una pre-reserva de evento para un cliente tras acordar fecha y paquete.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "nombre_cliente": types.Schema(type="STRING", description="Nombre completo del cliente."),
                        "telefono_cliente": types.Schema(type="STRING", description="Número de teléfono celular de 9 dígitos."),
                        "tipo_evento": types.Schema(
                            type="STRING", enum=["boda", "quinceanero", "institucional", "alquiler_local"]
                        ),
                        "paquete": types.Schema(type="STRING", enum=["basico", "premium", "no_aplica"]),
                        "fecha_evento": types.Schema(type="STRING", description="Fecha en formato YYYY-MM-DD."),
                        "turno": types.Schema(type="STRING", enum=["almuerzo", "cena"]),
                        "nro_invitados": types.Schema(type="INTEGER"),
                        "horas_extras": types.Schema(type="INTEGER"),
                        "paleta_colores": types.Schema(type="STRING", description="Colores preferidos para la decoración."),
                        "disenio_pantalla": types.Schema(type="STRING", description="Texto/Mensaje para la pantalla gigante."),
                    },
                    required=["nombre_cliente", "telefono_cliente", "tipo_evento", "fecha_evento", "turno", "nro_invitados"],
                ),
            ),
        ]
    )
]


class VillaPradaAgent:
    def __init__(self) -> None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        self.client = None
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                logger.info("Cliente Gemini inicializado correctamente.")
            except Exception as e:
                logger.error(f"No se pudo inicializar Gemini: {e}")
        else:
            logger.warning("GOOGLE_API_KEY no configurada.")

    def _execute_function(self, name: str, args: Dict[str, Any]) -> tuple[str, Optional[Dict[str, Any]]]:
        if name == "cotizar_evento":
            req = CotizacionRequest(
                tipo_evento=args.get("tipo_evento", "boda"),
                paquete=args.get("paquete", "basico"),
                nro_invitados=int(args.get("nro_invitados", 100)),
                horas_extras=int(args.get("horas_extras", 0)),
            )
            cot = calcular_cotizacion(req)
            lines = [
                "📊 <b>Cotización Personalizada - Villa Prada</b>",
                "",
                f"• <b>Evento:</b> {cot.tipo_evento.upper()} ({cot.paquete.upper()})",
                f"• <b>Invitados:</b> {cot.nro_invitados} personas",
                f"• <b>Precio por Persona:</b> S/ {cot.precio_unitario_pax:.2f}",
                f"• <b>Subtotal Evento:</b> S/ {cot.subtotal_evento:.2f}",
            ]
            if cot.horas_extras > 0:
                lines.append(f"• <b>Horas Extras ({cot.horas_extras}h):</b> S/ {cot.horas_extras_monto:.2f}")
            lines.extend([
                "",
                f"🏆 <b>TOTAL ESTIMADO:</b> S/ {cot.total_general:.2f}",
                "",
                "📌 <b>Pasos para Reservar:</b>",
                f"1. Pre-reserva tu fecha con solo <b>S/ {cot.monto_prereserva:.2f}</b>",
                f"2. Firma de contrato con el 30% de adelanto (S/ {cot.monto_adelanto_contrato_30pct:.2f})",
                "",
                f"✨ <b>Incluye:</b> 8h de evento + 1h tolerancia, mozos ({cot.mozos_requeridos} asignados), estructura frontal, zona selfie y pantalla gigante.",
                "",
                "¿Deseas consultar la disponibilidad de alguna fecha?",
            ])
            return "\n".join(lines), {"action": "cotizacion", "data": cot.model_dump()}

        if name == "verificar_disponibilidad":
            fecha = args.get("fecha_evento")
            turno = args.get("turno")
            disponible = database.verificar_disponibilidad_fecha(fecha, turno)
            if disponible:
                text = (
                    f"✅ Excelente noticia! La fecha <b>{fecha}</b> en el turno de la <b>{turno.upper()}</b> está <b>DISPONIBLE</b> en Villa Prada. 🎉\n\n"
                    "¿Te gustaría pre-reservarla con S/ 300?"
                )
            else:
                text = (
                    f"⚠️ Lo sentimos, la fecha <b>{fecha}</b> en el turno de la <b>{turno.upper()}</b> ya se encuentra reservada. "
                    "¿Deseas consultar otra fecha o turno?"
                )
            return text, {"action": "disponibilidad", "disponible": disponible}

        if name == "crear_prereserva":
            cliente = database.obtener_o_crear_cliente(
                nombre=args.get("nombre_cliente"),
                telefono=args.get("telefono_cliente"),
            )

            req = CotizacionRequest(
                tipo_evento=args.get("tipo_evento", "boda"),
                paquete=args.get("paquete", "basico"),
                nro_invitados=int(args.get("nro_invitados", 100)),
                horas_extras=int(args.get("horas_extras", 0)),
            )
            cot = calcular_cotizacion(req)

            evento = database.crear_evento(
                cliente_id=cliente["id"],
                tipo_evento=cot.tipo_evento,
                paquete=cot.paquete,
                fecha_evento=args.get("fecha_evento"),
                turno=args.get("turno"),
                nro_invitados=cot.nro_invitados,
                duracion_horas=8,
                horas_extras=cot.horas_extras,
                precio_por_pax=cot.precio_unitario_pax,
                total_estimado=cot.total_general,
                paleta_colores=args.get("paleta_colores"),
                disenio_pantalla=args.get("disenio_pantalla"),
            )

            text = (
                f"🎉 <b>¡Pre-reserva Creada con Éxito!</b>\n\n"
                f"• <b>Evento ID:</b> #{str(evento['id'])[:8]}\n"
                f"• <b>Cliente:</b> {cliente['nombre']}\n"
                f"• <b>Fecha:</b> {evento['fecha_evento']} ({evento['turno'].upper()})\n"
                f"• <b>Total Evento:</b> S/ {cot.total_general:.2f}\n\n"
                f"💳 <b>Para bloquear oficialmente la fecha:</b>\n"
                "Realiza el abono de pre-reserva de <b>S/ 300.00</b> vía Yape/Plin o transferencia.\n\n"
                "📱 Un asesor te contactará para coordinar la firma del contrato y adelanto del 30%."
            )
            return text, {"action": "prereserva_creada", "evento": evento}

        return "No entendí la acción solicitada.", None

    def process_message(self, user_text: str, history: Optional[list] = None) -> dict:
        if not self.client:
            return {
                "text": "El servicio de asistencia no está disponible porque GOOGLE_API_KEY no está configurada.",
                "action": "error",
            }

        contents = []
        if history and isinstance(history, list):
            contents.extend(history)
        contents.append({"role": "user", "parts": [user_text]})

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=TOOLS,
                    temperature=0.2,
                ),
            )

            candidate = response.candidates[0] if response.candidates else None
            if not candidate:
                return {"text": "Disculpa, no pude procesar tu solicitud. ¿Podrías repetirla?", "action": None}

            parts = candidate.content.parts
            client_action: Optional[Dict[str, Any]] = None

            for part in parts:
                function_call = getattr(part, "function_call", None)
                if function_call:
                    name = function_call.name
                    args = dict(function_call.args or {})
                    text, extra = self._execute_function(name, args)
                    if extra and not client_action:
                        client_action = extra
                    response_text = text
                    break
            else:
                response_text = "".join(part.text for part in parts if getattr(part, "text", None)) or "Entendido, ¿en qué más te puedo ayudar?"

            out: Dict[str, Any] = {"text": response_text}
            if client_action:
                out["action"] = client_action.get("action")
                if "data" in client_action:
                    out["data"] = client_action["data"]
                if "evento" in client_action:
                    out["evento"] = client_action["evento"]
                if "disponible" in client_action:
                    out["disponible"] = client_action["disponible"]
            return out

        except Exception as e:
            logger.error(f"Error en VillaPradaAgent: {e}", exc_info=True)
            return {"text": "Disculpa, ocurrió un error interno al consultar el sistema. Por favor intenta de nuevo.", "action": "error"}
