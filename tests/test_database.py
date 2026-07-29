"""
Tests de integración para Base de Datos Supabase y Servicios de Villa Prada.
"""
import pytest
import os
import uuid
from datetime import datetime, timedelta
from src import database
from src.services.chef_service import generar_lista_compras_chef
from src.services.contract_service import generar_contrato_pdf


def test_supabase_cliente_crud():
    # Crear cliente de prueba con teléfono único
    random_suffix = str(uuid.uuid4().int)[:6]
    tel_test = f"99{random_suffix}"
    cliente = database.obtener_o_crear_cliente(
        nombre="Cliente Test Supabase",
        telefono=tel_test,
        ruc_dni="12345678"
    )
    
    assert cliente is not None
    assert cliente['nombre'] == "Cliente Test Supabase"
    assert cliente['telefono'] == tel_test


def test_supabase_verificar_disponibilidad_y_crear_evento():
    random_suffix = str(uuid.uuid4().int)[:6]
    tel_test = f"98{random_suffix}"
    cliente = database.obtener_o_crear_cliente("Maria Perez", tel_test)
    
    # Fecha única para evitar conflicto con restricción de clave única (fecha_evento, turno)
    fecha_futura = (datetime.now() + timedelta(days=200 + int(random_suffix) % 100)).strftime("%Y-%m-%d")
    turno = "cena"
    
    # 1. Verificar disponibilidad inicial
    disponible_inicial = database.verificar_disponibilidad_fecha(fecha_futura, turno)
    assert disponible_inicial is True
    
    # 2. Crear evento
    evento = database.crear_evento(
        cliente_id=cliente['id'],
        tipo_evento="boda",
        paquete="premium",
        fecha_evento=fecha_futura,
        turno=turno,
        nro_invitados=150,
        duracion_horas=8,
        horas_extras=1,
        precio_por_pax=114.0,
        total_estimado=17400.0,
        paleta_colores="Azul y Plateado",
        disenio_pantalla="Boda Maria & Juan"
    )
    
    assert evento is not None
    assert evento['estado'] == 'tentativo'
    
    # 3. Verificar que la fecha AHORA está ocupada (prevención de doble reserva)
    disponible_despues = database.verificar_disponibilidad_fecha(fecha_futura, turno)
    assert disponible_despues is False
    
    # 4. Registrar pago de pre-reserva (S/300)
    pago = database.registrar_pago(
        evento_id=evento['id'],
        tipo_pago="prereserva_300",
        monto=300.0,
        referencia="YAPE-83921"
    )
    
    assert pago is not None
    
    # Verificar que el estado del evento cambió a 'prereservado'
    evento_updated = database.obtener_evento_por_id(evento['id'])
    assert evento_updated['estado'] == 'prereservado'


def test_servicio_chef_lista_compras():
    res = generar_lista_compras_chef(150, "boda", "premium")
    assert res['nro_invitados'] == 150
    assert len(res['insumos']) > 0
    assert res['costo_total_estimado_insumos'] > 0


def test_generar_contrato_pdf():
    evento_mock = {
        "id": "12345678-90ab-cdef-1234-567890abcdef",
        "cliente_nombre": "Maria Perez Test",
        "cliente_doc": "47382910",
        "cliente_telefono": "987111222",
        "fecha_evento": "2026-12-25",
        "turno": "cena",
        "tipo_evento": "boda",
        "nro_invitados": 150,
        "total_estimado": 17400.0
    }
    
    pdf_path = generar_contrato_pdf(evento_mock)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000
