import uuid
import asyncio
from typing import Optional, List

from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from neo4j import AsyncGraphDatabase

from llama_parse import LlamaParse
from llama_cloud_services import (
    LlamaExtract,
    ExtractConfig,
    ExtractMode,
    SourceText,
)


from dotenv import load_dotenv
import os

load_dotenv()  # carga variables desde .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
PDF_PATH = os.getenv("PDF_PATH", "a1.pdf")


# -----------------------------
# CLIENTES
# -----------------------------
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

neo4j_driver = AsyncGraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
)

parser = LlamaParse(
    api_key=LLAMA_API_KEY,
    parse_mode="parse_page_without_llm",
)

extractor = LlamaExtract(api_key=LLAMA_API_KEY)


# -----------------------------
# MODELOS DE EXTRACCIÓN
# -----------------------------
class Location(BaseModel):
    """Información de ubicación de una parte."""
    country: Optional[str] = Field(None, description="Country")
    state: Optional[str] = Field(None, description="State or province")
    address: Optional[str] = Field(None, description="Street address or city")


class Party(BaseModel):
    """Parte contratante."""
    name: str = Field(description="Party name")
    location: Optional[Location] = Field(None, description="Party location details")


class BaseContract(BaseModel):
    """Campos comunes a contratos."""
    parties: Optional[List[Party]] = Field(None, description="All contracting parties")
    agreement_date: Optional[str] = Field(None, description="Contract signing date, YYYY-MM-DD")
    effective_date: Optional[str] = Field(None, description="Effective date, YYYY-MM-DD")
    expiration_date: Optional[str] = Field(None, description="Expiration date, YYYY-MM-DD")
    governing_law: Optional[str] = Field(None, description="Governing jurisdiction")
    termination_for_convenience: Optional[bool] = Field(None, description="Termination without cause allowed")
    anti_assignment: Optional[bool] = Field(None, description="Assignment to third parties restricted")
    cap_on_liability: Optional[str] = Field(None, description="Liability cap amount or description")


class AffiliateAgreement(BaseContract):
    """Affiliate Agreement."""
    exclusivity: Optional[str] = Field(None, description="Exclusive territory or market rights")
    non_compete: Optional[str] = Field(None, description="Non-compete restrictions")
    revenue_profit_sharing: Optional[str] = Field(None, description="Commission or revenue split")
    minimum_commitment: Optional[str] = Field(None, description="Minimum sales targets or commitments")


class CoBrandingAgreement(BaseContract):
    """Co-Branding Agreement."""
    exclusivity: Optional[str] = Field(None, description="Exclusive co-branding rights")
    ip_ownership_assignment: Optional[str] = Field(None, description="IP ownership allocation")
    license_grant: Optional[str] = Field(None, description="Brand/trademark licenses")
    revenue_profit_sharing: Optional[str] = Field(None, description="Revenue sharing terms")


CONTRACT_TYPE_MAPPING = {
    "Affiliate_Agreements": AffiliateAgreement,
    "Co_Branding": CoBrandingAgreement,
    # Podrías agregar otros tipos si los defines
}


# -----------------------------
# CLASIFICACIÓN DEL CONTRATO
# -----------------------------
CLASSIFICATION_PROMPT_TEMPLATE = """
You are a legal document classification assistant.
Your task is to pick the most appropriate contract type from the list.

Read the contract excerpt below and choose exactly one type.
Then respond using the following XML tags:

<Reason>brief explanation of why</Reason>
<ContractType>one_type_from_the_list</ContractType>

Contract excerpt:
{contract_text}

Possible contract types:
{contract_type_list}
""".strip()


async def classify_contract(contract_text: str, contract_types: list[str]) -> dict:
    prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(
        contract_text=contract_text,
        contract_type_list="\n".join(contract_types),
    )

    history = [{"role": "user", "content": prompt}]

    response = await openai_client.responses.create(
        input=history,
        model="gpt-4o-mini",
        store=False,
    )

    text = response.output[0].content[0].text

    reason = None
    ctype = None

    if "<Reason>" in text and "</Reason>" in text:
        reason = text.split("<Reason>", 1)[1].split("</Reason>", 1)[0].strip()

    if "<ContractType>" in text and "</ContractType>" in text:
        ctype = text.split("<ContractType>", 1)[1].split("</ContractType>", 1)[0].strip()

    if ctype not in contract_types:
        ctype = contract_types[0]

    return {
        "reason": reason,
        "contract_type": ctype,
        "raw_output": text,
    }


# -----------------------------
# EXTRACCIÓN ESTRUCTURADA
# -----------------------------
async def extract_structured_contract(full_text: str, contract_type: str, filename: str):
    schema_model = CONTRACT_TYPE_MAPPING[contract_type]

    agent = extractor.create_agent(
        name=f"extraction_workflow_{uuid.uuid4()}",
        data_schema=schema_model,
        config=ExtractConfig(
            extraction_mode=ExtractMode.BALANCED,
        ),
    )

    result = await agent.aextract(
        files=SourceText(
            text_content=full_text,
            filename=filename,
        )
    )

    return result.data  # dict compatible con el modelo Pydantic


# -----------------------------
# IMPORTACIÓN A NEO4J
# -----------------------------
# IMPORTANTE: requiere APOC instalado en Neo4j
IMPORT_QUERY = """
WITH $contract AS contract
MERGE (c:Contract {path: $path})
SET c += apoc.map.clean(contract, ["parties","agreement_date","effective_date","expiration_date"], [])
SET c.agreement_date = case
        when contract.agreement_date IS NULL then NULL
        else date(contract.agreement_date)
    end,
    c.effective_date = case
        when contract.effective_date IS NULL then NULL
        else date(contract.effective_date)
    end,
    c.expiration_date = case
        when contract.expiration_date IS NULL then NULL
        else date(contract.expiration_date)
    end
WITH c, contract
UNWIND coalesce(contract.parties, []) AS party
MERGE (p:Party {name: party.name})
MERGE (c)-[:HAS_PARTY]->(p)
WITH p, party
WHERE party.location IS NOT NULL
MERGE (p)-[:HAS_LOCATION]->(l:Location)
SET l += party.location
"""


async def import_into_neo4j(contract_data: dict, pdf_path: str):
    async with neo4j_driver.session() as session:
        await session.run(
            IMPORT_QUERY,
            contract=contract_data,
            path=pdf_path,
        )


# -----------------------------
# PIPELINE PRINCIPAL
# -----------------------------
async def process_legal_pdf(pdf_path: str):
    # 1) Parseo del PDF
    parsed = await parser.aparse(pdf_path)
    pages = [p.text for p in parsed.pages]

    first_10_pages_text = " ".join(pages[:10])
    full_text = " ".join(pages)

    # 2) Clasificación de tipo de contrato
    contract_types = list(CONTRACT_TYPE_MAPPING.keys())
    classification = await classify_contract(first_10_pages_text, contract_types)
    contract_type = classification["contract_type"]

    print(f"[INFO] Contract type detected: {contract_type}")
    print(f"[INFO] Reason: {classification['reason']}")

    # 3) Extracción estructurada con LlamaExtract
    structured_data = await extract_structured_contract(
        full_text=full_text,
        contract_type=contract_type,
        filename=pdf_path,
    )

    print("[INFO] Structured data extracted (truncated):")
    # Mostrar solo algunas claves para no saturar
    for k, v in list(structured_data.items())[:10]:
        print(f"  {k}: {v}")

    # 4) Importar al grafo Neo4j
    await import_into_neo4j(structured_data, pdf_path)
    print("[INFO] Data imported into Neo4j")

    return {
        "contract_type": contract_type,
        "classification_reason": classification["reason"],
    }


# -----------------------------
# ENTRYPOINT
# -----------------------------
async def main():
    result = await process_legal_pdf(PDF_PATH)
    print("[DONE]", result)


if __name__ == "__main__":
    asyncio.run(main())
