"""
Tests unitarios para la calculadora de cotizaciones de Villa Prada.
"""
import pytest
from src.calculator import calcular_cotizacion, CotizacionRequest


def test_cotizacion_boda_basico_100_pax():
    req = CotizacionRequest(tipo_evento="boda", paquete="basico", nro_invitados=100, horas_extras=0)
    cot = calcular_cotizacion(req)
    
    assert cot.precio_unitario_pax == 100.0  # Base 100pax = S/100
    assert cot.subtotal_evento == 10000.0
    assert cot.total_general == 10000.0
    assert cot.monto_prereserva == 300.0
    assert cot.monto_adelanto_contrato_30pct == 3000.0
    assert cot.mozos_requeridos == 4  # 100 / 25 = 4
    assert cot.costo_mozos_total == 280.0  # 4 * 70


def test_cotizacion_quinceanero_premium_200_pax_con_descuento():
    req = CotizacionRequest(tipo_evento="quinceanero", paquete="premium", nro_invitados=200, horas_extras=2)
    cot = calcular_cotizacion(req)
    
    # Base Premium S/120. Con 200 pax -> 10% descuento = S/108
    assert cot.precio_unitario_pax == 108.0
    assert cot.subtotal_evento == 21600.0
    assert cot.horas_extras_monto == 600.0  # 2 * 300
    assert cot.total_general == 22200.0
    assert cot.mozos_requeridos == 8  # 200 / 25 = 8
    assert cot.costo_mozos_total == 560.0  # 8 * 70


def test_cotizacion_alquiler_local():
    req = CotizacionRequest(tipo_evento="alquiler_local", paquete="no_aplica", nro_invitados=100, horas_extras=0)
    cot = calcular_cotizacion(req)
    
    assert cot.subtotal_evento == 4000.0
    assert cot.total_general == 4000.0
    assert cot.monto_adelanto_contrato_30pct == 1200.0


def test_cotizacion_institucional_50_pax():
    req = CotizacionRequest(tipo_evento="institucional", paquete="no_aplica", nro_invitados=50, horas_extras=0)
    cot = calcular_cotizacion(req)
    
    # Base S/60. Con <100 pax -> +5% = S/63
    assert cot.precio_unitario_pax == 63.0
    assert cot.subtotal_evento == 3150.0
    assert cot.mozos_requeridos == 2  # 50 / 25 = 2
