"""
Servicio de Cálculo Logístico y Lista de Compras para el Chef — Villa Prada.
Genera la lista estimada de insumos requeridos según número de invitados y tipo de menú.
"""
from typing import Dict, Any, List


def generar_lista_compras_chef(nro_invitados: int, tipo_evento: str, paquete: str = 'basico') -> Dict[str, Any]:
    """
    Calcula los insumos necesarios para la cocina basados en reglas culinarias estándar:
    - Carne/Proteína: 250g por persona (bruto 300g)
    - Arroz: 80g por persona
    - Papas/Guarnición: 150g por persona
    - Ensalada/Verduras: 100g por persona
    - Bebidas (Gaseosas/Agua): 0.5L por persona
    - Cerveza/Vino: 2 cajas de cerveza por cada 50 adultos (estimado)
    """
    factor_pax = nro_invitados
    
    # Ratios base
    carne_kg = round((factor_pax * 0.300), 2)  # 300g por persona
    arroz_kg = round((factor_pax * 0.080), 2)  # 80g por persona
    papa_kg = round((factor_pax * 0.150), 2)   # 150g por persona
    verduras_kg = round((factor_pax * 0.100), 2) # 100g por persona
    aceite_litros = round((factor_pax * 0.020), 2) # 20ml por persona
    
    # Bebidas
    gaseosas_6packs = max(1, round(factor_pax / 6))
    cajas_cerveza = max(1, round(factor_pax / 25)) if paquete == 'premium' else max(1, round(factor_pax / 35))
    
    insumos: List[Dict[str, Any]] = [
        {"categoria": "Proteína", "insumo": "Carne/Pollo/Cerdo seleccionado", "cantidad": carne_kg, "unidad": "kg"},
        {"categoria": "Abarrotes", "insumo": "Arroz extra", "cantidad": arroz_kg, "unidad": "kg"},
        {"categoria": "Verduras", "insumo": "Papa / Yuca guarnición", "cantidad": papa_kg, "unidad": "kg"},
        {"categoria": "Verduras", "insumo": "Verduras mixtas ensalada", "cantidad": verduras_kg, "unidad": "kg"},
        {"categoria": "Abarrotes", "insumo": "Aceite vegetal / Condimentos", "cantidad": aceite_litros, "unidad": "litros"},
        {"categoria": "Bebidas", "insumo": "Gaseosas / Refrescos (paquetes 6u)", "cantidad": gaseosas_6packs, "unidad": "paquetes"},
        {"categoria": "Bebidas", "insumo": "Caja de cerveza / brindis", "cantidad": cajas_cerveza, "unidad": "cajas"}
    ]
    
    # Costo estimado aproximado por plato en insumos (aprox S/18 - S/25 por pax)
    costo_por_pax = 22.0 if paquete == 'premium' else 16.0
    costo_total_estimado = round(costo_por_pax * nro_invitados, 2)
    
    return {
        "nro_invitados": nro_invitados,
        "tipo_evento": tipo_evento,
        "paquete": paquete,
        "costo_total_estimado_insumos": costo_total_estimado,
        "insumos": insumos
    }
