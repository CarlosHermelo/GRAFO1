import os
import asyncio
import uuid
import re
from typing import List, Optional

from pydantic import BaseModel, Field
from neo4j import GraphDatabase
from dotenv import load_dotenv
import nest_asyncio

from openai import AsyncOpenAI
from llama_cloud_services.parse import LlamaParse
from llama_cloud_services.extract import (
    ExtractConfig,
    ExtractMode,
    LlamaExtract,
    SourceText,
)

# Necesario en algunos entornos interactivos (Jupyter, etc.)
nest_asyncio.apply()

# -----------------------------
# CARGA DE VARIABLES DE ENTORNO
# -----------------------------
load_dotenv()

LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
PDF_PATH = os.getenv("PDF_PATH", "a1.pdf")  # default a1.pdf si no está en .env

required_env_vars = {
    "LLAMA_API_KEY": LLAMA_API_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "NEO4J_URI": NEO4J_URI,
    "NEO4J_USER": NEO4J_USER,
    "NEO4J_PASSWORD": NEO4J_PASSWORD,
}

missing = [name for name, value in required_env_vars.items() if not value]
if missing:
    raise EnvironmentError(
        f"Faltan variables de entorno: {', '.join(missing)}. "
        "Revisa tu archivo .env y vuelve a ejecutar el script."
    )

# ----------------------------------------------------------------------------------
# 1. Definición de Schemas Pydantic
# ----------------------------------------------------------------------------------

class Location(BaseModel):
    """Location information with structured address components."""
    country: Optional[str] = Field(None, description="Country")
    state: Optional[str] = Field(None, description="State or province")
    address: Optional[str] = Field(None, description="Street address or city")


class Party(BaseModel):
    """Party information with name and location."""
    name: str = Field(description="Party name")
    location: Optional[Location] = Field(None, description="Party location details")


class BaseContract(BaseModel):
    """Base contract class with common fields."""
    parties: Optional[List[Party]] = Field(None, description="All contracting parties")
    agreement_date: Optional[str] = Field(None, description="Contract signing date. Use YYYY-MM-DD")
    effective_date: Optional[str] = Field(None, description="When contract becomes effective. Use YYYY-MM-DD")
    expiration_date: Optional[str] = Field(None, description="Contract expiration date. Use YYYY-MM-DD")
    governing_law: Optional[str] = Field(None, description="Governing jurisdiction")
    termination_for_convenience: Optional[bool] = Field(None, description="Can terminate without cause")
    anti_assignment: Optional[bool] = Field(None, description="Restricts assignment to third parties")
    cap_on_liability: Optional[str] = Field(None, description="Liability limit amount")


class AffiliateAgreement(BaseContract):
    """Affiliate Agreement extraction."""
    exclusivity: Optional[str] = Field(None, description="Exclusive territory or market rights")
    non_compete: Optional[str] = Field(None, description="Non-compete restrictions")
    revenue_profit_sharing: Optional[str] = Field(None, description="Commission or revenue split")
    minimum_commitment: Optional[str] = Field(None, description="Minimum sales targets")


class CoBrandingAgreement(BaseContract):
    """Co-Branding Agreement extraction."""
    exclusivity: Optional[str] = Field(None, description="Exclusive co-branding rights")
    ip_ownership_assignment: Optional[str] = Field(None, description="IP ownership allocation")
    license_grant: Optional[str] = Field(None, description="Brand/trademark licenses")
    revenue_profit_sharing: Optional[str] = Field(None, description="Revenue sharing terms")


schema_mapping = {
    "Affiliate_Agreements": AffiliateAgreement,
    "Co_Branding": CoBrandingAgreement,
}

# ----------------------------------------------------------------------------------
# 2. Lógica de Clasificación (usando OpenAI en lugar de LlamaClassify)
# ----------------------------------------------------------------------------------

classification_prompt = """You are a legal document classification assistant.
Your task is to identify the most likely contract type based on the content of the first 10 pages of a contract.
Instructions:
Read the contract excerpt below.
Review the list of possible contract types.
Choose the single most appropriate contract type from the list.
Justify your classification briefly, based only on the information in the excerpt.

Contract Excerpt:
{contract_text}
Possible Contract Types:
{contract_type_list}

Output Format:
<Reason>brief_justification</Reason>
<ContractType>chosen_type_from_list</ContractType>
"""


async def classify_contract(openai_client: AsyncOpenAI, contract_text: str, contract_types: List[str]) -> dict:
    prompt = classification_prompt.format(
        contract_text=contract_text,
        contract_type_list=contract_types,
    )

    response = await openai_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini",
    )
    content = response.choices[0].message.content

    type_match = re.search(r"<ContractType>(.*?)</ContractType>", content, re.IGNORECASE)
    contract_type = type_match.group(1).strip() if type_match else "Unknown"

    return {"contract_type": contract_type}

# ----------------------------------------------------------------------------------
# 3. Flujo Principal
# ----------------------------------------------------------------------------------

async def main():
    if not os.path.exists(PDF_PATH):
        print(f"❌ ERROR: No se encontró el archivo PDF en la ruta: {PDF_PATH}")
        print("Asegúrate de que el archivo exista o que PDF_PATH en tu .env sea correcto.")
        return

    # --- FASE 1: PARSEO Y CLASIFICACIÓN ---
    print(f"\n--- 1. Procesando documento: {PDF_PATH} ---")
    try:
        parser = LlamaParse(
            api_key=LLAMA_API_KEY,
            parse_mode="parse_page_without_llm",
        )

        raw_results = await parser.aparse(PDF_PATH)

        # Soporta versiones que devuelven .pages o lista directa
        if hasattr(raw_results, "pages"):
            results = raw_results.pages
        elif isinstance(raw_results, list):
            results = raw_results
        else:
            raise TypeError(
                f"LlamaParse devolvió un resultado inesperado: {type(raw_results)}. "
                f"Contenido: {raw_results}"
            )

        if not results or not all(hasattr(r, "text") for r in results):
            raise AttributeError("Los elementos del resultado de LlamaParse no tienen el atributo '.text'.")

        full_text = " ".join([el.text for el in results])
        print(f"   ✅ Parseo completado. Se extrajeron {len(results)} páginas.")

        print("--- 2. Clasificando tipo de contrato con OpenAI ---")
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        contract_types = list(schema_mapping.keys())
        first_pages_text = " ".join([el.text for el in results[:10]])

        classification = await classify_contract(openai_client, first_pages_text, contract_types)
        detected_type = classification["contract_type"]
        print(f"   ✅ Tipo detectado: {detected_type}")

        if detected_type not in schema_mapping:
            print(f"   ⚠️ Advertencia: Tipo '{detected_type}' no mapeado para extracción. Deteniendo proceso.")
            return

    except Exception as e:
        print(f"❌ ERROR en las fases de Parseo o Clasificación: {e}")
        return

    # --- FASE 2: EXTRACCIÓN ESTRUCTURADA ---
       # --- FASE 2: EXTRACCIÓN ESTRUCTURADA ---
    print("\n--- 3. Extrayendo información estructurada con LlamaExtract ---")
    try:
        extractor = LlamaExtract(api_key=LLAMA_API_KEY)
        extraction_mode = ExtractMode.BALANCED

        agent = extractor.create_agent(
            name=f"extraction_workflow_{uuid.uuid4()}",
            data_schema=schema_mapping[detected_type],
            config=ExtractConfig(extraction_mode=extraction_mode),
        )

        extraction_result = await agent.aextract(
            files=[SourceText(text_content=full_text, filename=PDF_PATH)]
        )

        # ----------------------------------------------------------------
        # FORMATO ROBUSTO PARA MANEJAR DISTINTOS TIPOS DE RESPUESTA
        # ----------------------------------------------------------------

        data_dict = None

        # Caso 1: devuelve lista
        if isinstance(extraction_result, list):
            first = extraction_result[0]

            # Caso 1a: el primer elemento tiene atributo .data
            if hasattr(first, "data"):
                raw = first.data
                if isinstance(raw, list):
                    data_dict = raw[0]
                elif isinstance(raw, dict):
                    data_dict = raw
                else:
                    raise TypeError(f"Formato inesperado en first.data: {type(raw)}")

            # Caso 1b: el primer elemento es un dict directo
            elif isinstance(first, dict):
                data_dict = first

            else:
                raise TypeError(f"Elemento inesperado en lista: {type(first)}")

        # Caso 2: devuelve un único objeto con .data
        elif hasattr(extraction_result, "data"):
            raw = extraction_result.data
            if isinstance(raw, list):
                data_dict = raw[0]
            elif isinstance(raw, dict):
                data_dict = raw
            else:
                raise TypeError(f"Formato inesperado en extraction_result.data: {type(raw)}")

        # Caso 3: devuelve un dict directo
        elif isinstance(extraction_result, dict):
            data_dict = extraction_result

        else:
            raise TypeError(
                f"Formato inesperado de extraction_result: {type(extraction_result)}"
            )

        # Chequeo final
        if not isinstance(data_dict, dict):
            raise ValueError("No se pudo obtener data_dict como diccionario válido.")

        print(f"   ✅ Extracción completada. Datos para {len(data_dict.get('parties', []))} partes.")

    except Exception as e:
        print(f"❌ ERROR en la fase de extracción: {e}")
        return

    # --- FASE 3: CARGA EN NEO4J ---
    print("\n--- 4. Importando a Neo4j Knowledge Graph ---")

    import_query = """
    WITH $contract AS contract
    // 1. Crear o unir el nodo de Contrato
    MERGE (c:Contract {path: $path})
    SET c += apoc.map.clean(contract, ["parties", "agreement_date", "effective_date", "expiration_date"], [])
    SET c.contract_type = $detected_type

    // 2. Convertir fechas a tipo Date (manejo defensivo de valores nulos)
    FOREACH (ignoreMe IN CASE WHEN contract.agreement_date IS NOT NULL THEN [1] ELSE [] END |
        SET c.agreement_date = date(contract.agreement_date))
    FOREACH (ignoreMe IN CASE WHEN contract.effective_date IS NOT NULL THEN [1] ELSE [] END |
        SET c.effective_date = date(contract.effective_date))
    FOREACH (ignoreMe IN CASE WHEN contract.expiration_date IS NOT NULL THEN [1] ELSE [] END |
        SET c.expiration_date = date(contract.expiration_date))

    // 3. Crear Partes y la relación con el Contrato
    WITH c, contract
    UNWIND coalesce(contract.parties, []) AS party
    MERGE (p:Party {name: party.name})
    MERGE (c)-[:HAS_PARTY]->(p)

    // 4. Crear Nodos de Ubicación y la relación con las Partes
    WITH p, party
    WHERE party.location IS NOT NULL
    MERGE (l:Location)
    SET l.country = party.location.country
    SET l.state = party.location.state
    SET l.address = party.location.address
    MERGE (p)-[:HAS_LOCATION]->(l)
    """

    driver = None
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()

        records, summary, keys = driver.execute_query(
            import_query,
            contract=data_dict,
            path=PDF_PATH,
            detected_type=detected_type,
            database_="neo4j",
        )
        print("   ✅ ¡Importación finalizada con éxito!")
        print(f"      ▶️ Nodos creados: {summary.counters.nodes_created}")
        print(f"      ▶️ Relaciones creadas: {summary.counters.relationships_created}")

    except Exception as e:
        print(f"❌ ERROR de conexión o consulta en Neo4j: {e}")
        print("   Asegúrate de que tus credenciales de Neo4j sean correctas y que la base de datos esté accesible.")
    finally:
        if driver:
            driver.close()


if __name__ == "__main__":
    asyncio.run(main())
