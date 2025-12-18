"""
Objetivo Parser
Extrae información estructurada del archivo objetivo_validado.md
"""

import re
from typing import Dict, List


def parse_objetivo(objetivo_md_path: str) -> Dict:
    """
    Lee objetivo_validado.md y extrae información clave

    Args:
        objetivo_md_path: Ruta al archivo objetivo_validado.md

    Returns:
        Diccionario con objetivo, dominio, entidades, consultas, etc.
    """
    with open(objetivo_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    objetivo_info = {}

    # Extraer objetivo del usuario
    match = re.search(
        r'\*\*Objetivo del Usuario:\*\*\s*(.+?)(?=\*\*Dominio:)',
        content,
        re.DOTALL
    )
    if match:
        objetivo_info["objetivo"] = match.group(1).strip()
    else:
        objetivo_info["objetivo"] = "No especificado"

    # Extraer dominio
    match = re.search(r'\*\*Dominio:\*\*\s*(\w+)', content)
    if match:
        objetivo_info["dominio"] = match.group(1).strip()
    else:
        objetivo_info["dominio"] = "general"

    # Extraer entidades clave
    match = re.search(
        r'\*\*Entidades Clave Identificadas:\*\*(.+?)(?=\*\*Relaciones|$)',
        content,
        re.DOTALL
    )
    if match:
        entidades_text = match.group(1)
        # Buscar líneas que empiecen con "- **NombreEntidad**:"
        entidades = re.findall(r'- \*\*(.+?)\*\*:', entidades_text)
        objetivo_info["entidades_clave"] = entidades
    else:
        objetivo_info["entidades_clave"] = []

    # Extraer consultas esperadas
    match = re.search(
        r'\*\*Consultas Esperadas.+?\*\*(.+?)(?=\*\*Tipos|$)',
        content,
        re.DOTALL
    )
    if match:
        consultas_text = match.group(1)
        # Buscar líneas numeradas con consultas entre comillas
        consultas = re.findall(r'\d+\. "(.+?)"', consultas_text)
        objetivo_info["consultas_esperadas"] = consultas
    else:
        objetivo_info["consultas_esperadas"] = []

    # Extraer tipos de inconsistencias
    match = re.search(
        r'\*\*Tipos de Inconsistencias a Detectar:\*\*(.+?)(?=\*\*Validación|$)',
        content,
        re.DOTALL
    )
    if match:
        tipos_text = match.group(1)
        # Buscar secciones numeradas "1. **Tipo**:"
        tipos = re.findall(r'\d+\.\s+\*\*(.+?)\*\*:', tipos_text)
        objetivo_info["tipos_inconsistencias"] = tipos
    else:
        objetivo_info["tipos_inconsistencias"] = []

    return objetivo_info


def format_objetivo_for_prompt(objetivo_info: Dict) -> str:
    """
    Formatea el objetivo para incluir en prompts del LLM

    Args:
        objetivo_info: Diccionario retornado por parse_objetivo()

    Returns:
        String formateado para insertar en prompts
    """
    consultas_top5 = objetivo_info.get("consultas_esperadas", [])[:5]
    consultas_formatted = "\n".join([f"  - {c}" for c in consultas_top5])

    tipos_inc = objetivo_info.get("tipos_inconsistencias", [])
    tipos_formatted = ", ".join(tipos_inc) if tipos_inc else "N/A"

    prompt_section = f"""
==========================================
OBJETIVO DEL GRAFO DE CONOCIMIENTO:
==========================================
{objetivo_info.get('objetivo', 'No especificado')}

DOMINIO: {objetivo_info.get('dominio', 'general')}

ENTIDADES CLAVE BUSCADAS:
{', '.join(objetivo_info.get('entidades_clave', []))}

CONSULTAS QUE EL USUARIO QUIERE RESPONDER:
{consultas_formatted}

TIPOS DE INCONSISTENCIAS A DETECTAR (si aplica):
{tipos_formatted}
==========================================
"""
    return prompt_section


if __name__ == "__main__":
    # Test
    objetivo_info = parse_objetivo("../resultados/objetivo_validado.md")
    print("Objetivo parseado:")
    print(f"Dominio: {objetivo_info['dominio']}")
    print(f"Entidades: {objetivo_info['entidades_clave']}")
    print(f"Consultas: {len(objetivo_info['consultas_esperadas'])}")
    print("\nFormateado para prompt:")
    print(format_objetivo_for_prompt(objetivo_info))
