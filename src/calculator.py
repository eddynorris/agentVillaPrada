"""
Calculadora de Cotizaciones y Recursos para Villa Prada.
Implementa las reglas de negocio exactas:
- Precios base: Boda/15añero Premium (S/120), Básico (S/100), Institucional (S/60), Alquiler (S/4000/100pax)
- Escalonado por volumen: <100 (+5%), 100-149 (base), 150-199 (-5%), 200+ (-10%)
- Servicio: 8h + 1h tolerancia. Hora extra: S/300
- Pre-reserva: S/300, Adelanto contrato: 30% del total
- Personal: 1 mozo cada 25 personas @ S/70 por 8h + cena
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class CotizacionRequest(BaseModel):
    tipo_evento: str = Field(..., description="boda, quinceanero, institucional, alquiler_local")
    paquete: str = Field("basico", description="basico, premium, no_aplica")
    nro_invitados: int = Field(..., gt=0, description="Número total de personas/invitados")
    horas_extras: int = Field(0, ge=0, description="Horas adicionales a las 8 horas contratadas")


class CotizacionResponse(BaseModel):
    tipo_evento: str
    paquete: str
    nro_invitados: int
    horas_extras: int
    precio_unitario_pax: float
    subtotal_evento: float
    horas_extras_monto: float
    total_general: float
    monto_prereserva: float
    monto_adelanto_contrato_30pct: float
    mozos_requeridos: int
    costo_mozos_total: float


def calcular_cotizacion(request: CotizacionRequest) -> CotizacionResponse:
    tipo = request.tipo_evento.lower()
    paquete = request.paquete.lower()
    invitados = request.nro_invitados
    horas_extras = request.horas_extras

    # 1. Alquiler de Local Implementado
    if tipo == "alquiler_local":
        costo_base = 4000.0
        pax_extra = max(0, invitados - 100)
        subtotal = costo_base + (pax_extra * 20.0)
        precio_pax = round(subtotal / invitados, 2)
    
    # 2. Evento Institucional
    elif tipo == "institucional":
        base_pax = 60.0
        factor = _obtener_factor_volumen(invitados)
        precio_pax = round(base_pax * factor, 2)
        subtotal = round(precio_pax * invitados, 2)
        
    # 3. Boda o Quinceañero (Básico vs Premium)
    else: # boda, quinceanero
        base_pax = 120.0 if paquete == "premium" else 100.0
        factor = _obtener_factor_volumen(invitados)
        precio_pax = round(base_pax * factor, 2)
        subtotal = round(precio_pax * invitados, 2)

    # Horas Extras
    monto_horas_extras = float(horas_extras * 300.0)
    total_general = round(subtotal + monto_horas_extras, 2)

    # Prereserva y Adelanto
    prereserva = 300.0
    adelanto_30pct = round(total_general * 0.30, 2)

    # Cálculo de Mozos: 1 mozo por cada 25 personas @ S/70
    mozos = (invitados + 24) // 25
    costo_mozos = float(mozos * 70.0)

    return CotizacionResponse(
        tipo_evento=tipo,
        paquete=paquete if tipo in ("boda", "quinceanero") else "no_aplica",
        nro_invitados=invitados,
        horas_extras=horas_extras,
        precio_unitario_pax=precio_pax,
        subtotal_evento=subtotal,
        horas_extras_monto=monto_horas_extras,
        total_general=total_general,
        monto_prereserva=prereserva,
        monto_adelanto_contrato_30pct=adelanto_30pct,
        mozos_requeridos=mozos,
        costo_mozos_total=costo_mozos
    )


def _obtener_factor_volumen(invitados: int) -> float:
    """Aplica descuento escalonado según número de invitados."""
    if invitados < 100:
        return 1.05  # +5% para grupos pequeños
    elif 100 <= invitados <= 149:
        return 1.00  # Tarifa base
    elif 150 <= invitados <= 199:
        return 0.95  # 5% descuento
    else: # 200+
        return 0.90  # 10% descuento
