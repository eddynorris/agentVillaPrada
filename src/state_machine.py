"""
Máquina de Estados Conversacional para el Cliente en WhatsApp.
Mantiene el progreso de la reserva de cada cliente (teléfono):
- IDLE: Saludo / Consulta inicial
- COTIZANDO: Evaluación de paquete y número de personas
- ESPERANDO_FECHA: Fecha y turno deseados
- ESPERANDO_PRERESERVA: Esperando abono de S/ 300
- ESPERANDO_CONTRATO: Esperando firma y adelanto del 30%
- CONFIRMADO: Evento confirmado
"""
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class SessionState(str, Enum):
    IDLE = "idle"
    COTIZANDO = "cotizando"
    ESPERANDO_FECHA = "esperando_fecha"
    ESPERANDO_PRERESERVA = "esperando_prereserva"
    ESPERANDO_CONTRATO = "esperando_contrato"
    CONFIRMADO = "confirmado"


class ClientSession:
    """Mantiene el estado en memoria de la sesión conversacional de un teléfono."""
    
    def __init__(self, telefono: str):
        self.telefono = telefono
        self.state = SessionState.IDLE
        self.data: Dict[str, Any] = {}
        self.last_activity = datetime.now(timezone.utc)

    def update_state(self, new_state: SessionState, new_data: Dict[str, Any] = None):
        self.state = new_state
        if new_data:
            self.data.update(new_data)
        self.last_activity = datetime.now(timezone.utc)


class SessionManager:
    """Gestor de sesiones de clientes de WhatsApp."""
    
    _sessions: Dict[str, ClientSession] = {}

    @classmethod
    def get_session(cls, telefono: str) -> ClientSession:
        if telefono not in cls._sessions:
            cls._sessions[telefono] = ClientSession(telefono)
        return cls._sessions[telefono]

    @classmethod
    def clear_session(cls, telefono: str):
        if telefono in cls._sessions:
            del cls._sessions[telefono]
