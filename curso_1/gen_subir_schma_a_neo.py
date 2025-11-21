import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# cargar variables de entorno
load_dotenv()

print("URI:", os.getenv("NEO4J_URI"))
print("USER:", os.getenv("NEO4J_USER"))
print("PASS:", os.getenv("NEO4J_PASSWORD"))

#

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://b0df6e44.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# script cypher completo
CYPHER_SCRIPT = """
// --- CREACIÓN DE NODOS (MERGE) ---
MERGE (n:Resolucion {id: "resol_2024_1967_inssjp_de_inssjp"}) ON CREATE SET n.nombre = "RESOL-2024-1967-INSSJP-DE#INSSJP";
MERGE (n:Externo {id: "ex_2024_67302759_inssjp_gvg_inssjp"}) ON CREATE SET n.nombre = "EX-2024-67302759-INSSJP-GVG#INSSJP";
MERGE (n:Instituto {id: "instituto_nacional_de_servicios_sociales_para_jubilados_y_pensionados"}) ON CREATE SET n.nombre = "INSTITUTO NACIONAL DE SERVICIOS SOCIALES para JUBILADOS y PENSIONADOS";
MERGE (n:Ley {id: "ley_19032"}) ON CREATE SET n.nombre = "Ley Nº 19.032";
MERGE (n:Ley {id: "ley_25615"}) ON CREATE SET n.nombre = "Ley Nº 25.615";
MERGE (n:Resolucion {id: "resol_2021_1335_inssjp_de_inssjp"}) ON CREATE SET n.nombre = "RESOL-2021-1335-INSSJP-DE#INSSJP";
MERGE (n:Programa {id: "programa_odontologico_veteranos"}) ON CREATE SET n.nombre = "PROGRAMA ODONTOLÓGICO VETERANOS";
MERGE (n:Nomenclador {id: "nomenclador_odontologico_exclusivo"}) ON CREATE SET n.nombre = "Nomenclador odontológico exclusivo";
MERGE (n:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}) ON CREATE SET n.nombre = "RESOL-2024-2076-INSSJP-DE#INSSJP";
MERGE (n:Externo {id: "ex_2020_15409689_inssjp_usa_inssjp"}) ON CREATE SET n.nombre = "EX-2020-15409689- -INSSJP-USA#INSSJP";
MERGE (n:Ley {id: "ley_19_032"}) ON CREATE SET n.nombre = "Ley 19.032";
MERGE (n:Ley {id: "ley_27_275"}) ON CREATE SET n.nombre = "Ley 27.275";
MERGE (n:Decreto {id: "decreto_206_pen_17"}) ON CREATE SET n.nombre = "Decreto 206/PEN/17";
MERGE (n:Resolucion {id: "resol_2020_1637_inssjp_de_inssjp"}) ON CREATE SET n.nombre = "RESOL-2020-1637-INSSJP-DE#INSSJP";
MERGE (n:Resolucion {id: "resol_2021_1278_inssjp_de_inssjp"}) ON CREATE SET n.nombre = "RESOL-2021-1278-INSSJP-DE#INSSJP";
MERGE (n:Resolucion {id: "resol_2024_80_apn_aaip"}) ON CREATE SET n.nombre = "RESOL-2024-80-APN-AAIP";
MERGE (n:Articulo {id: "articulo_6_ley_19_032"}) ON CREATE SET n.nombre = "Artículo 6º de la Ley Nº 19.032";
MERGE (n:Decreto {id: "decreto_02_04_pen"}) ON CREATE SET n.nombre = "Decreto Nº 02/04-PEN";
MERGE (n:Directorio {id: "directorio_ejecutivo_nacional_inssjp"}) ON CREATE SET n.nombre = "Directorio Ejecutivo Nacional del INSSJP";
MERGE (n:UnidadSecretaria {id: "unidad_secretaria_administrativa"}) ON CREATE SET n.nombre = "Unidad Secretaría Administrativa";
MERGE (n:Gerencia {id: "gerencia_de_asuntos_juridicos"}) ON CREATE SET n.nombre = "Gerencia de Asuntos Jurídicos";
MERGE (n:Anexo {id: "anexo_i_2024_76807687_inssjp_de_inssjp"}) ON CREATE SET n.nombre = "Anexo I (IF-2024-76807687-INSSJP-DE#INSSJP)";
MERGE (n:Anexo {id: "anexo_ii_2024_76807730_inssjp_de_inssjp"}) ON CREATE SET n.nombre = "Anexo II (IF-2024-76807730-INSSJP-DE#INSSJP)";
MERGE (n:Resolucion {id: "resolucion_2024_2568"}) ON CREATE SET n.nombre = "RESOL-2024-2568-INSSJP-DE#INSSJP";
MERGE (n:Año {id: "anio_de_la_defensa_de_la_vida_la_libertad_y_la_propiedad"}) ON CREATE SET n.nombre = "AÑO DE LA DEFENSA DE LA VIDA, LA LIBERTAD Y LA PROPIEDAD";
MERGE (n:Resolucion {id: "resolucion_2024_1272"}) ON CREATE SET n.nombre = "RESOL-2024-1272-INSSJP-DE#INSSJP";
MERGE (n:Resolucion {id: "resolucion_662_1979"}) ON CREATE SET n.nombre = "Resolución N° 662/I/1979";
MERGE (n:Resolucion {id: "resolucion_27_2002"}) ON CREATE SET n.nombre = "Resolución N° 27/I/2002";
MERGE (n:Resolucion {id: "resolucion_120_1998"}) ON CREATE SET n.nombre = "Resolución N° 120/P/98";
MERGE (n:Anexo {id: "anexo_i_2024"}) ON CREATE SET n.nombre = "Anexo I";
MERGE (n:Anexo {id: "anexo_ii_2024"}) ON CREATE SET n.nombre = "Anexo II";
MERGE (n:Anexo {id: "anexo_iii_2024"}) ON CREATE SET n.nombre = "Anexo III";
MERGE (n:UnidadDeGestionLocal {id: "unidad_de_gestion_local"}) ON CREATE SET n.nombre = "Unidades de Gestión Local";
MERGE (n:Gerencia {id: "gerencia_de_coordinacion_de_unidades_de_gestion_local"}) ON CREATE SET n.nombre = "Gerencia de Coordinación de Unidades de Gestión Local";
MERGE (n:Gerencia {id: "gerencia_de_recursos_humanos"}) ON CREATE SET n.nombre = "Gerencia de Recursos Humanos";
MERGE (n:Resolucion {id: "resolucion_164_2011"}) ON CREATE SET n.nombre = "Resolución N° 164/DE/11";
MERGE (n:Subgerencia {id: "subgerencia_de_pami_escucha_y_responde"}) ON CREATE SET n.nombre = "Subgerencia de PAMI Escucha y Responde";
MERGE (n:Gerencia {id: "gerencia_de_auditoria_prestacional"}) ON CREATE SET n.nombre = "Gerencia de Auditoria Prestacional";
MERGE (n:Gerencia {id: "gerencia_de_tecnologia_de_informacion"}) ON CREATE SET n.nombre = "Gerencia de Tecnología de Información";
MERGE (n:UnidadDeGestionLocal {id: "unidad_de_gestion_local_xiv_parana"}) ON CREATE SET n.nombre = "Unidad de Gestión Local XIV - Paraná";
MERGE (n:UnidadDeGestionLocal {id: "unidad_de_gestion_local_xxxiv_concordia"}) ON CREATE SET n.nombre = "Unidad de Gestión Local XXXIV - Concordia";
MERGE (n:Departamento {id: "departamento_medico"}) ON CREATE SET n.nombre = "Departamento Médico";
MERGE (n:Division {id: "division_operativa"}) ON CREATE SET n.nombre = "División Operativa";
MERGE (n:Division {id: "division_moeit"}) ON CREATE SET n.nombre = "División MOEIT";
MERGE (n:Externo {id: "referente_pami_escucha"}) ON CREATE SET n.nombre = "Referente PAMI Escucha";
MERGE (n:Departamento {id: "departamento_de_politicas_sociales"}) ON CREATE SET n.nombre = "Departamento de Políticas Sociales";
MERGE (n:Division {id: "division_promocion_social_y_comunitaria"}) ON CREATE SET n.nombre = "División de Promoción Social y Comunitaria";
MERGE (n:Division {id: "division_relacion_organizaciones_jubilados"}) ON CREATE SET n.nombre = "División de Relación con las Organizaciones de Jubilados y Pensionados";
MERGE (n:Division {id: "division_politicas_de_cuidado"}) ON CREATE SET n.nombre = "División de Políticas de Cuidado";
MERGE (n:Departamento {id: "departamento_contable"}) ON CREATE SET n.nombre = "Departamento Contable";
MERGE (n:Division {id: "division_contabilidad"}) ON CREATE SET n.nombre = "División Contabilidad";
MERGE (n:Division {id: "division_tesoreria"}) ON CREATE SET n.nombre = "División Tesorería";
MERGE (n:Division {id: "division_liquidacion"}) ON CREATE SET n.nombre = "División Liquidación";
MERGE (n:Division {id: "division_presupuesto"}) ON CREATE SET n.nombre = "División Presupuesto";
MERGE (n:Departamento {id: "departamento_administrativo"}) ON CREATE SET n.nombre = "Departamento Administrativo";
MERGE (n:Sector {id: "sector_intendencia"}) ON CREATE SET n.nombre = "Sector Intendencia";
MERGE (n:Division {id: "division_recursos_humanos"}) ON CREATE SET n.nombre = "División Recursos Humanos";
MERGE (n:Division {id: "division_tecnologia"}) ON CREATE SET n.nombre = "División Tecnología";
MERGE (n:Division {id: "division_mesa_entradas_salidas"}) ON CREATE SET n.nombre = "División Mesa de Entradas y Salidas";
MERGE (n:Division {id: "division_compras_contrataciones"}) ON CREATE SET n.nombre = "División Compras y Contrataciones";
MERGE (n:UnidadDeGestionLocal {id: "centro_atencion_personalizada"}) ON CREATE SET n.nombre = "Centro de Atención Personalizada";
MERGE (n:UnidadDeGestionLocal {id: "boca_atencion"}) ON CREATE SET n.nombre = "Boca de Atención";
MERGE (n:Resolucion {id: "resolucion_548_2002"}) ON CREATE SET n.nombre = "Resolución N° 548/I/2002";
MERGE (n:Decreto {id: "decreto_pen_02_04"}) ON CREATE SET n.nombre = "Decreto PEN N° 02/04";
MERGE (n:Decreto {id: "decreto_2023_63_pte"}) ON CREATE SET n.nombre = "Decreto DECTO-2023-63-APN-PTE";
MERGE (n:Resolucion {id: "resol_2024_2603_INSSJP"}) ON CREATE SET n.nombre = "RESOL-2024-2603-INSSJP-DE#INSSJP";
MERGE (n:Instituto {id: "INSSJP"}) ON CREATE SET n.nombre = "Instituto Nacional de Servicios Sociales para Jubilados y Pensionados";
MERGE (n:Ley {id: "ley_24156"}) ON CREATE SET n.nombre = "Ley N° 24.156";
MERGE (n:Decreto {id: "decreto_2_2004"}) ON CREATE SET n.nombre = "Decreto N° 2/PEN/2004";
MERGE (n:Resolucion {id: "RESOL_2023_992"}) ON CREATE SET n.nombre = "RESOL-2023-992-INSSJP-DE#INSSJP";
MERGE (n:Resolucion {id: "RESOL_2023_1593"}) ON CREATE SET n.nombre = "RESOL-2023-1593-INSSJP-DE#INSSJP";
MERGE (n:Resolucion {id: "RESOL_2023_1911"}) ON CREATE SET n.nombre = "RESOL-2023-1911-INSSJP-DE#INSSJP";
MERGE (n:Resolucion {id: "RESOL_2024_1"}) ON CREATE SET n.nombre = "RESOL-2024-1-INSSJP-DE#INSSJP";
MERGE (n:Resolucion {id: "RESOL_2024_1932"}) ON CREATE SET n.nombre = "RESOL-2024-1932-INSSJP-DE#INSSJP";
MERGE (n:Presupuesto {id: "presupuesto_2024"}) ON CREATE SET n.nombre = "Presupuesto General del Ejercicio 2024 ";
MERGE (n:Departamento {id: "departamento_ee"}) ON CREATE SET n.nombre = "Departamento Estudios Económicos";
MERGE (n:Subgerencia {id: "subgerencia_gepe"}) ON CREATE SET n.nombre = "Subgerencia de Gestión y Programación Económica";
MERGE (n:Gerencia {id: "gerencia_ef"}) ON CREATE SET n.nombre = "Gerencia Económico Financiera";
MERGE (n:Gerencia {id: "gerencia_aj"}) ON CREATE SET n.nombre = "Gerencia de Asuntos Jurídicos";
MERGE (n:Anexo {id: "anexo_1"}) ON CREATE SET n.nombre = "IF-2024-97548795-INSSJP-DE#INSSJP ";

MATCH (a:Resolucion {id: "resol_2024_1967_inssjp_de_inssjp"}), (b:Externo {id: "ex_2024_67302759_inssjp_gvg_inssjp"}) MERGE (a)-[:CITA]->(b);
MATCH (a:Resolucion {id: "resol_2024_1967_inssjp_de_inssjp"}), (b:Ley {id: "ley_19032"}) MERGE (a)-[:CITA]->(b);
MATCH (a:Resolucion {id: "resol_2024_1967_inssjp_de_inssjp"}), (b:Ley {id: "ley_25615"}) MERGE (a)-[:CITA]->(b);
MATCH (a:Resolucion {id: "resol_2024_1967_inssjp_de_inssjp"}), (b:Instituto {id: "instituto_nacional_de_servicios_sociales_para_jubilados_y_pensionados"}) MERGE (a)-[:ES_PARTE_DE]->(b);
MATCH (a:Instituto {id: "instituto_nacional_de_servicios_sociales_para_jubilados_y_pensionados"}), (b:Programa {id: "programa_odontologico_veteranos"}) MERGE (a)-[:CREA]->(b);
MATCH (a:Nomenclador {id: "nomenclador_odontologico_exclusivo"}), (b:Programa {id: "programa_odontologico_veteranos"}) MERGE (a)-[:IMPORTADO_POR]->(b);
MATCH (a:Resolucion {id: "resol_2021_1335_inssjp_de_inssjp"}), (b:Programa {id: "programa_odontologico_veteranos"}) MERGE (a)-[:CREA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Ley {id: "ley_19_032"}) MERGE (a)-[:CITA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Ley {id: "ley_27_275"}) MERGE (a)-[:CITA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Decreto {id: "decreto_206_pen_17"}) MERGE (a)-[:CITA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Resolucion {id: "resol_2020_1637_inssjp_de_inssjp"}) MERGE (a)-[:CITA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Resolucion {id: "resol_2021_1278_inssjp_de_inssjp"}) MERGE (a)-[:CITA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Resolucion {id: "resol_2024_80_apn_aaip"}) MERGE (a)-[:CITA]->(b);
MATCH (a:Instituto {id: "instituto_nacional_de_servicios_sociales_para_jubilados_y_pensionados"}), (b:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}) MERGE (a)-[:CREA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Resolucion {id: "resol_2020_1637_inssjp_de_inssjp"}) MERGE (a)-[:DEROGA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Anexo {id: "anexo_i_2024_76807687_inssjp_de_inssjp"}) MERGE (a)-[:APRUEBA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Anexo {id: "anexo_ii_2024_76807730_inssjp_de_inssjp"}) MERGE (a)-[:APRUEBA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:Resolucion {id: "resol_2021_1278_inssjp_de_inssjp"}) MERGE (a)-[:MODIFICA]->(b);
MATCH (a:Anexo {id: "anexo_i_2024_76807687_inssjp_de_inssjp"}), (b:Externo {id: "ex_2020_15409689_inssjp_usa_inssjp"}) MERGE (a)-[:CONTIENE]->(b);
MATCH (a:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}), (b:UnidadSecretaria {id: "unidad_secretaria_administrativa"}) MERGE (a)-[:AUTORIZA]->(b);
MATCH (a:Gerencia {id: "gerencia_de_asuntos_juridicos"}), (b:Resolucion {id: "resol_2024_2076_inssjp_de_inssjp"}) MERGE (a)-[:INTERVIENE]->(b);
MATCH (a:Instituto {id: "instituto_nacional_de_servicios_sociales_para_jubilados_y_pensionados"}), (b:Directorio {id: "directorio_ejecutivo_nacional_inssjp"}) MERGE (a)-[:TIENE_DIRECTORIO]->(b);
MATCH (a:Resolucion {id: "resolucion_2024_2568"}), (b:Instituto {id: "instituto_nacional_de_servicios_sociales_para_jubilados_y_pensionados"}) MERGE (a)-[:DOCUMANTA]->(b);
MATCH (a:Resolucion {id: "resolucion_2024_2568"}), (b:Anexo {id: "anexo_i_2024"}) MERGE (a)-[:TIENE_ANEXO]->(b);
MATCH (a:Resolucion {id: "resolucion_2024_2568"}), (b:Anexo {id: "anexo_ii_2024"}) MERGE (a)-[:TIENE_ANEXO]->(b);
MATCH (a:Resolucion {id: "resolucion_2024_2568"}), (b:Anexo {id: "anexo_iii_2024"}) MERGE (a)-[:TIENE_ANEXO]->(b);
MATCH (a:Resolucion {id: "resolucion_2024_2568"}), (b:UnidadDeGestionLocal {id: "unidad_de_gestion_local"}) MERGE (a)-[:APRUEBA]->(b);
MATCH (a:Resolucion {id: "resolucion_2024_2568"}), (b:Resolucion {id: "resolucion_662_1979"}) MERGE (a)-[:DEROGA]->(b);
MATCH (a:Resolucion {id: "resolucion_2024_2568"}), (b:UnidadDeGestionLocal {id: "unidad_de_gestion_local_xiv_parana"}) MERGE (a)-[:MODIFICA]->(b);
MATCH (a:UnidadDeGestionLocal {id: "unidad_de_gestion_local_xiv_parana"}), (b:UnidadDeGestionLocal {id: "unidad_de_gestion_local_xxxiv_concordia"}) MERGE (a)-[:CREA]->(b);
MATCH (a:Resolucion {id: "resolucion_120_1998"}), (b:Resolucion {id: "resolucion_548_2002"}) MERGE (a)-[:MODIFICA]->(b);
MATCH (a:Resolucion {id: "resolucion_2024_2568"}), (b:Gerencia {id: "gerencia_de_coordinacion_de_unidades_de_gestion_local"}) MERGE (a)-[:TIENE_GERENCIA]->(b);
MATCH (a:Resolucion {id: "resolucion_2024_2568"}), (b:Gerencia {id: "gerencia_de_recursos_humanos"}) MERGE (a)-[:TIENE_GERENCIA]->(b);
MATCH (a:Ley {id: "ley_19032"}), (b:Decreto {id: "decreto_pen_02_04"}) MERGE (a)-[:MODIFICA]->(b);
MATCH (a:Decreto {id: "decreto_pen_02_04"}), (b:Decreto {id: "decreto_2023_63_pte"}) MERGE (a)-[:CITA]->(b);
MATCH (a:UnidadDeGestionLocal {id: "unidad_de_gestion_local"}), (b:Departamento {id: "departamento_medico"}) MERGE (a)-[:TIENE_DEPARTAMENTO]->(b);
MATCH (a:Departamento {id: "departamento_medico"}), (b:Division {id: "division_operativa"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:Departamento {id: "departamento_medico"}), (b:Division {id: "division_moeit"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:UnidadDeGestionLocal {id: "unidad_de_gestion_local"}), (b:Departamento {id: "departamento_contable"}) MERGE (a)-[:TIENE_DEPARTAMENTO]->(b);
MATCH (a:Departamento {id: "departamento_contable"}), (b:Division {id: "division_contabilidad"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:Departamento {id: "departamento_contable"}), (b:Division {id: "division_tesoreria"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:Departamento {id: "departamento_contable"}), (b:Division {id: "division_liquidacion"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:Departamento {id: "departamento_administrativo"}), (b:Sector {id: "sector_intendencia"}) MERGE (a)-[:TIENE_SECTOR]->(b);
MATCH (a:Departamento {id: "departamento_administrativo"}), (b:Division {id: "division_recursos_humanos"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:Departamento {id: "departamento_administrativo"}), (b:Division {id: "division_tecnologia"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:Departamento {id: "departamento_administrativo"}), (b:Division {id: "division_mesa_entradas_salidas"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:Departamento {id: "departamento_administrativo"}), (b:Division {id: "division_compras_contrataciones"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:UnidadDeGestionLocal {id: "unidad_de_gestion_local"}), (b:Departamento {id: "departamento_de_politicas_sociales"}) MERGE (a)-[:TIENE_DEPARTAMENTO]->(b);
MATCH (a:Departamento {id: "departamento_de_politicas_sociales"}), (b:Division {id: "division_promocion_social_y_comunitaria"}) MERGE (a)-[:TIENE_DIVISION]->(b);
MATCH (a:Resolucion {id: "resol_2024_2603_INSSJP"}), (b:Ley {id: "ley_19032"}) MERGE (a)-[:APLICA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2603_INSSJP"}), (b:Ley {id: "ley_24156"}) MERGE (a)-[:APLICA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2603_INSSJP"}), (b:Decreto {id: "decreto_2_2004"}) MERGE (a)-[:APLICA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2603_INSSJP"}), (b:Instituto {id: "INSSJP"}) MERGE (a)-[:APLICA]->(b);
MATCH (a:Instituto {id: "INSSJP"}), (b:Resolucion {id: "resol_2024_2603_INSSJP"}) MERGE (a)-[:CREA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2603_INSSJP"}), (b:Resolucion {id: "RESOL_2024_1932"}) MERGE (a)-[:MODIFICA]->(b);
MATCH (a:Resolucion {id: "resol_2024_2603_INSSJP"}), (b:Resolucion {id: "RESOL_2024_1"}) MERGE (a)-[:MODIFICA]->(b);
MATCH (a:Resolucion {id: "RESOL_2024_1932"}), (b:Presupuesto {id: "presupuesto_2024"}) MERGE (a)-[:APUESTA]->(b);
MATCH (a:Resolucion {id: "RESOL_2024_1"}), (b:Presupuesto {id: "presupuesto_2024"}) MERGE (a)-[:APUESTA]->(b);
MATCH (a:Departamento {id: "departamento_ee"}), (b:Subgerencia {id: "subgerencia_gepe"}) MERGE (a)-[:DEPENDIENTE_DE]->(b);
MATCH (a:Subgerencia {id: "subgerencia_gepe"}), (b:Departamento {id: "departamento_ee"}) MERGE (a)-[:TIENE_DEPARTAMENTO]->(b);
MATCH (a:Resolucion {id: "resol_2024_2603_INSSJP"}), (b:Anexo {id: "anexo_1"}) MERGE (a)-[:TIENE_ANEXO]->(b);
MATCH (a:Gerencia {id: "gerencia_ef"}), (b:Resolucion {id: "resol_2024_2603_INSSJP"}) MERGE (a)-[:INTERVIENE]->(b);
MATCH (a:Gerencia {id: "gerencia_aj"}), (b:Resolucion {id: "resol_2024_2603_INSSJP"}) MERGE (a)-[:INTERVIENE]->(b);

"""

# conexión y ejecución
def run_script(cypher):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        for block in cypher.split("MATCH"):
            if block.strip():
                script_part = ("MATCH" + block) if not block.strip().startswith("//") else block
                try:
                    session.run(script_part)
                except Exception as e:
                    print("Error ejecutando bloque:")
                    print(script_part)
                    print(e)
    driver.close()

# ejecutar script
if __name__ == "__main__":
    print("Ejecutando Cypher...")
    run_script(CYPHER_SCRIPT)
    print("Finalizado.")
