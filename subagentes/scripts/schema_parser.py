"""
Schema Parser
Extrae información estructurada del archivo schema_diseñado.md
"""

import re
from typing import Dict, List


def parse_schema(schema_md_path: str) -> Dict:
    """
    Lee schema_diseñado.md y extrae nodos, relaciones, validaciones

    Args:
        schema_md_path: Ruta al archivo schema_diseñado.md

    Returns:
        Diccionario con nodos, relaciones, constraints, etc.
    """
    with open(schema_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    schema_info = {
        "nodos": [],
        "relaciones": [],
        "constraints": [],
        "indices": []
    }

    # Parsear sección "2. NODOS DETALLADOS"
    nodos_match = re.search(
        r'## 2\. NODOS DETALLADOS(.+?)(?=## 3\. NODO ESPECIAL|## 4\. RELACIONES|$)',
        content,
        re.DOTALL
    )

    if nodos_match:
        nodos_text = nodos_match.group(1)

        # Buscar cada "### Nodo: (:NombreNodo)"
        nodo_pattern = r'### Nodo: \(:(\w+)\)(.+?)(?=### Nodo:|## 3\.|## 4\.|$)'
        nodo_blocks = re.findall(nodo_pattern, nodos_text, re.DOTALL)

        for label, block in nodo_blocks:
            nodo_info = {
                "label": label,
                "identidad": [],
                "propiedades": [],
                "descripcion": ""
            }

            # Extraer descripción
            desc_match = re.search(r'\*\*Descripción:\*\* (.+?)(?=\n\*\*)', block)
            if desc_match:
                nodo_info["descripcion"] = desc_match.group(1).strip()

            # Extraer regla de identidad
            identidad_match = re.search(
                r'Propiedades: `\((.+?)\)`',
                block
            )
            if identidad_match:
                identidad_str = identidad_match.group(1)
                nodo_info["identidad"] = [
                    prop.strip() for prop in identidad_str.split(',')
                ]

            # Extraer propiedades
            # Buscar bloques de propiedades en formato:
            # - `nombre_prop`
            #   - Tipo: String
            #   - Obligatoria: SÍ
            #   - Valores permitidos: [...]

            prop_pattern = r'- `(\w+)`\s+- Tipo: (\w+)\s+(?:- Parte de identidad: (.+?)\s+)?- Obligatoria: (SÍ|No)'
            prop_matches = re.findall(prop_pattern, block)

            for prop_name, prop_type, _, obligatoria in prop_matches:
                prop_info = {
                    "nombre": prop_name,
                    "tipo": prop_type,
                    "obligatoria": (obligatoria == "SÍ")
                }

                # Buscar valores permitidos para esta propiedad
                valores_pattern = rf'- `{prop_name}`.*?Valores permitidos: \[(.+?)\]'
                valores_match = re.search(valores_pattern, block, re.DOTALL)
                if valores_match:
                    valores_str = valores_match.group(1)
                    valores = [
                        v.strip().strip('"') for v in valores_str.split(',')
                    ]
                    prop_info["valores"] = valores

                nodo_info["propiedades"].append(prop_info)

            schema_info["nodos"].append(nodo_info)

    # Parsear sección "4. RELACIONES DETALLADAS"
    rels_match = re.search(
        r'## 4\. RELACIONES DETALLADAS(.+?)(?=## 5\.|$)',
        content,
        re.DOTALL
    )

    if rels_match:
        rels_text = rels_match.group(1)

        # Buscar cada "### Relación: [:NOMBRE_RELACION]"
        rel_pattern = r'### Relación: \[:(\w+)\](.+?)(?=### Relación:|## 5\.|$)'
        rel_blocks = re.findall(rel_pattern, rels_text, re.DOTALL)

        for rel_type, block in rel_blocks:
            rel_info = {
                "tipo": rel_type,
                "desde": "",
                "hacia": "",
                "propiedades": []
            }

            # Extraer dirección: **Conecta:** (:From) → (:To)
            conecta_match = re.search(
                r'\*\*Conecta:\*\* \(:(\w+)\) → \(:(\w+)\)',
                block
            )
            if conecta_match:
                rel_info["desde"] = conecta_match.group(1)
                rel_info["hacia"] = conecta_match.group(2)

            # Extraer propiedades de la relación
            # Formato: - `propiedad`: Tipo - Descripción
            prop_rel_pattern = r'- `(\w+)`: (\w+)'
            prop_rel_matches = re.findall(prop_rel_pattern, block)

            for prop_name, prop_type in prop_rel_matches:
                rel_info["propiedades"].append({
                    "nombre": prop_name,
                    "tipo": prop_type
                })

            schema_info["relaciones"].append(rel_info)

    return schema_info


def get_node_by_label(schema_info: Dict, label: str) -> Dict:
    """
    Obtiene información de un nodo por su label

    Args:
        schema_info: Diccionario retornado por parse_schema()
        label: Label del nodo a buscar

    Returns:
        Diccionario con información del nodo o None
    """
    for nodo in schema_info["nodos"]:
        if nodo["label"] == label:
            return nodo
    return None


def format_schema_for_prompt(schema_info: Dict) -> str:
    """
    Formatea el schema para incluir en prompts del LLM

    Args:
        schema_info: Diccionario retornado por parse_schema()

    Returns:
        String formateado para insertar en prompts
    """
    # Formatear nodos
    entities_desc = ""
    for nodo in schema_info["nodos"]:
        props_desc = ""
        for prop in nodo["propiedades"]:
            obligatoria = "OBLIGATORIA" if prop["obligatoria"] else "Opcional"
            valores = ""
            if "valores" in prop:
                valores = f" (Valores permitidos: {prop['valores']})"

            props_desc += f"    - {prop['nombre']} ({prop['tipo']}, {obligatoria}){valores}\n"

        identidad_str = ", ".join(nodo["identidad"])
        entities_desc += f"""
### {nodo['label']}
Descripción: {nodo.get('descripcion', 'N/A')}
Propiedades de Identidad (Clave): {identidad_str}
Propiedades:
{props_desc}
"""

    # Formatear relaciones
    rels_desc = ""
    for rel in schema_info["relaciones"]:
        props_rel = []
        for p in rel.get("propiedades", []):
            props_rel.append(f"{p['nombre']} ({p['tipo']})")

        props_str = ""
        if props_rel:
            props_str = f" [Propiedades: {', '.join(props_rel)}]"

        rels_desc += f"- {rel['tipo']}: ({rel['desde']}) → ({rel['hacia']}){props_str}\n"

    prompt_section = f"""
SCHEMA DEL GRAFO:

ENTIDADES DISPONIBLES:
{entities_desc}

RELACIONES DISPONIBLES:
{rels_desc}
"""
    return prompt_section


if __name__ == "__main__":
    # Test
    schema_info = parse_schema("../resultados/schema_diseñado.md")
    print("Schema parseado:")
    print(f"Nodos: {len(schema_info['nodos'])}")
    for nodo in schema_info["nodos"]:
        print(f"  - {nodo['label']}: {len(nodo['propiedades'])} propiedades")
    print(f"\nRelaciones: {len(schema_info['relaciones'])}")
    for rel in schema_info["relaciones"]:
        print(f"  - {rel['tipo']}: {rel['desde']} → {rel['hacia']}")

    print("\nFormateado para prompt (primeros 500 chars):")
    print(format_schema_for_prompt(schema_info)[:500])
