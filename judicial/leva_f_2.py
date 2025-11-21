from neo4j import GraphDatabase

URI = "neo4j+s://b0df6e44.databases.neo4j.io"
AUTH = ("neo4j", "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g")
driver = GraphDatabase.driver(URI, auth=AUTH)

RUTA = "f_2.txt"

def crear_documento(tx, id_fallo, texto):
    tx.run("""
        MERGE (d:Documento {id: $id})
        SET d.texto = $texto
    """, id=id_fallo, texto=texto)

def procesar_archivo():
    with open(RUTA, encoding="utf-8") as f:
        lineas = f.readlines()

    documentos = []
    id_actual = None
    buffer_texto = []
    dentro_de_texto = False

    for linea in lineas:
        linea = linea.lstrip("\ufeff").rstrip("\n")

        # Detecta inicio de un fallo
        if linea.startswith("CSJN_") or linea.startswith("CFed_"):
            # Si ya hay uno en construcción, lo guardo
            if id_actual and buffer_texto:
                documentos.append((id_actual, "\n".join(buffer_texto)))

            # Nueva entrada
            partes = linea.split(",", 1)
            id_actual = partes[0].strip()

            # primer fragmento de texto
            if len(partes) > 1:
                texto_inicial = partes[1].lstrip('"').strip()
                buffer_texto = [texto_inicial]
            else:
                buffer_texto = []

            dentro_de_texto = True
            continue

        # Acumular líneas del bloque
        if dentro_de_texto:
            # Eliminar comillas finales si es la última línea del bloque
            linea_sin = linea.strip().rstrip('"')
            buffer_texto.append(linea_sin)

    # Guardar el último documento
    if id_actual and buffer_texto:
        documentos.append((id_actual, "\n".join(buffer_texto)))

    # Crear nodos
    with driver.session() as session:
        for id_fallo, texto in documentos:
            session.execute_write(crear_documento, id_fallo, texto)
            print("Documento creado:", id_fallo)

procesar_archivo()
print("Finalizado.")
