"""
Módulo de acceso a Base de Datos en Supabase PostgreSQL.
Proporciona pool de conexiones y funciones CRUD para el Agente Villa Prada.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.environ.get('DATABASE_URL')


@contextmanager
def get_db_connection():
    """Context manager para obtener una conexión a Supabase con cursor dict."""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_cursor():
    """Context manager para obtener un cursor dict con autocommit."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur


# ==================== CLIENTES ====================

def obtener_o_crear_cliente(nombre: str, telefono: str, ruc_dni: str = None, email: str = None) -> dict:
    """Busca un cliente por teléfono o lo crea si no existe."""
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM clientes WHERE telefono = %s;", (telefono,))
        cliente = cur.fetchone()
        if cliente:
            # Actualizar datos si viene información adicional
            if nombre and cliente['nombre'] != nombre:
                cur.execute("UPDATE clientes SET nombre = %s, updated_at = NOW() WHERE id = %s;", (nombre, cliente['id']))
                cliente['nombre'] = nombre
            return dict(cliente)
        
        cur.execute("""
            INSERT INTO clientes (nombre, telefono, ruc_dni, email)
            VALUES (%s, %s, %s, %s)
            RETURNING *;
        """, (nombre, telefono, ruc_dni, email))
        return dict(cur.fetchone())


# ==================== EVENTOS Y RESERVAS ====================

def verificar_disponibilidad_fecha(fecha_evento: str, turno: str) -> bool:
    """Retorna True si la fecha y turno están libres, False si ya están reservados."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT id FROM eventos
            WHERE fecha_evento = %s AND turno = %s AND estado NOT IN ('cancelado');
        """, (fecha_evento, turno))
        return cur.fetchone() is None


def crear_evento(cliente_id: str, tipo_evento: str, paquete: str, fecha_evento: str,
                 turno: str, nro_invitados: int, duracion_horas: int, horas_extras: int,
                 precio_por_pax: float, total_estimado: float, notas_decoracion: str = None,
                 paleta_colores: str = None, disenio_pantalla: str = None) -> dict:
    """Crea una reserva/evento en estado 'tentativo' o 'prereservado'."""
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO eventos (
                cliente_id, tipo_evento, paquete, fecha_evento, turno,
                nro_invitados, duracion_horas, horas_extras, precio_por_pax,
                total_estimado, notas_decoracion, paleta_colores, disenio_pantalla
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """, (
            cliente_id, tipo_evento, paquete, fecha_evento, turno,
            nro_invitados, duracion_horas, horas_extras, precio_por_pax,
            total_estimado, notas_decoracion, paleta_colores, disenio_pantalla
        ))
        return dict(cur.fetchone())


def obtener_evento_por_id(evento_id: str) -> dict:
    """Obtiene un evento completo con datos del cliente."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT e.*, c.nombre as cliente_nombre, c.telefono as cliente_telefono, c.ruc_dni as cliente_doc
            FROM eventos e
            JOIN clientes c ON e.cliente_id = c.id
            WHERE e.id = %s;
        """, (evento_id,))
        res = cur.fetchone()
        return dict(res) if res else None


def actualizar_estado_evento(evento_id: str, nuevo_estado: str) -> dict:
    """Actualiza el estado de un evento (tentativo, prereservado, confirmado, cancelado, finalizado)."""
    with get_db_cursor() as cur:
        cur.execute("""
            UPDATE eventos
            SET estado = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING *;
        """, (nuevo_estado, evento_id))
        return dict(cur.fetchone())


# ==================== PAGOS ====================

def registrar_pago(evento_id: str, tipo_pago: str, monto: float, metodo_pago: str = 'yape_plin',
                   referencia: str = None, url_comprobante: str = None) -> dict:
    """Registra un pago asociado a un evento (prereserva_300, adelanto_30pct, saldo_final)."""
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO pagos (evento_id, tipo_pago, monto, metodo_pago, referencia, url_comprobante, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'verificado')
            RETURNING *;
        """, (evento_id, tipo_pago, monto, metodo_pago, referencia, url_comprobante))
        pago = dict(cur.fetchone())

        # Si es pago de pre-reserva (S/300), pasar evento a 'prereservado'
        if tipo_pago == 'prereserva_300':
            actualizar_estado_evento(evento_id, 'prereservado')
        # Si es adelanto del 30% o más, pasar evento a 'confirmado'
        elif tipo_pago in ('adelanto_30pct', 'saldo_final'):
            actualizar_estado_evento(evento_id, 'confirmado')

        return pago


def obtener_pagos_evento(evento_id: str) -> list:
    """Obtiene el historial de pagos de un evento."""
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM pagos WHERE evento_id = %s ORDER BY fecha_pago ASC;", (evento_id,))
        return [dict(p) for p in cur.fetchall()]


# ==================== PERSONAL / MOZOS ====================

def asignar_personal_evento(evento_id: str, nombre: str, rol: str = 'mozo', pago_acordado: float = 70.0,
                            telefono_telegram: str = None) -> dict:
    """Asigna un trabajador a un evento."""
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO personal_evento (evento_id, nombre_trabajador, rol, pago_acordado, telefono_telegram)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *;
        """, (evento_id, nombre, rol, pago_acordado, telefono_telegram))
        return dict(cur.fetchone())


def obtener_personal_evento(evento_id: str) -> list:
    """Obtiene el personal asignado a un evento."""
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM personal_evento WHERE evento_id = %s ORDER BY rol, nombre_trabajador;", (evento_id,))
        return [dict(p) for p in cur.fetchall()]


# ==================== COMPRAS CHEF ====================

def guardar_lista_compras_chef(evento_id: str, lista_insumos_json: dict, costo_estimado: float) -> dict:
    """Guarda la lista de compras del chef para un evento."""
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO compras_chef (evento_id, lista_insumos_json, costo_estimado)
            VALUES (%s, %s, %s)
            RETURNING *;
        """, (evento_id, json.dumps(lista_insumos_json), costo_estimado))
        return dict(cur.fetchone())


# ==================== CONTRATOS ====================

def registrar_contrato(evento_id: str, url_pdf: str) -> dict:
    """Registra la URL del contrato PDF generado."""
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO contratos (evento_id, url_pdf)
            VALUES (%s, %s)
            RETURNING *;
        """, (evento_id, url_pdf))
        return dict(cur.fetchone())
