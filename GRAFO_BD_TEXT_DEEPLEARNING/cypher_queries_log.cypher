
// CREACIÓN FORZADA DEL NODO RAÍZ

    MERGE (n:Normativa {id: $id})
    SET n.codigo = $id,
        n.tipo_norma = 'Resolución',
        n.estado = 'Vigente',
        n.fecha_ingesta = date()
    
// Params: id='RESOL-2024-2249-INSSJP-DE#INSSJP'

// NODO: Normativa (RESOL-2020-1746-INSSJP-DE#INSSJP)
MERGE (n:`Normativa` {id: $id}) SET n += $props
// Params: {'id': 'RESOL-2020-1746-INSSJP-DE#INSSJP'}

// NODO: Normativa (RESOL-2022-973-INSSJP-DE#INSSJP)
MERGE (n:`Normativa` {id: $id}) SET n += $props
// Params: {'id': 'RESOL-2022-973-INSSJP-DE#INSSJP'}

// NODO: Normativa (RESOL-2022-1085-INSSJP-DE#INSSJP)
MERGE (n:`Normativa` {id: $id}) SET n += $props
// Params: {'id': 'RESOL-2022-1085-INSSJP-DE#INSSJP'}

// NODO: Normativa (RESOL-2024-1272-INSSJP-DE#INSSJP)
MERGE (n:`Normativa` {id: $id}) SET n += $props
// Params: {'id': 'RESOL-2024-1272-INSSJP-DE#INSSJP'}

// NODO: Normativa (Ley N° 19.032)
MERGE (n:`Normativa` {id: $id}) SET n += $props
// Params: {'id': 'Ley N° 19.032'}

// NODO: Normativa (Ley N° 26.427)
MERGE (n:`Normativa` {id: $id}) SET n += $props
// Params: {'id': 'Ley N° 26.427'}

// NODO: Normativa (Decreto N° 2/04)
MERGE (n:`Normativa` {id: $id}) SET n += $props
// Params: {'id': 'Decreto N° 2/04'}

// NODO: Prestacion (Pasantías)
MERGE (n:`Prestacion` {id: $id}) SET n += $props
// Params: {'codigo_practica': 'N/A', 'descripcion': 'Sistema de pasantías educativas', 'tipo_prestacion': 'Educativa', 'id': 'Pasantías'}

// NODO: Organizacion (INSTITUTO NACIONAL DE SERVICIOS SOCIALES PARA JUBILADOS Y PENSIONADOS)
MERGE (n:`Organizacion` {id: $id}) SET n += $props
// Params: {'id': 'INSTITUTO NACIONAL DE SERVICIOS SOCIALES PARA JUBILADOS Y PENSIONADOS'}

// NODO: Organizacion (FACULTAD DE MEDICINA de la UNIVERSIDAD DE BUENOS AIRES)
MERGE (n:`Organizacion` {id: $id}) SET n += $props
// Params: {'id': 'FACULTAD DE MEDICINA de la UNIVERSIDAD DE BUENOS AIRES'}
// REL: (RESOL-2024-2249-INSSJP-DE#INSSJP)-[CITA]->(Ley N° 19.032)

        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:`CITA`]->(b)
        SET r += $props
        
// Params: {}
// REL: (RESOL-2024-2249-INSSJP-DE#INSSJP)-[CITA]->(Ley N° 26.427)

        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:`CITA`]->(b)
        SET r += $props
        
// Params: {}
// REL: (RESOL-2024-2249-INSSJP-DE#INSSJP)-[CITA]->(RESOL-2020-1746-INSSJP-DE#INSSJP)

        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:`CITA`]->(b)
        SET r += $props
        
// Params: {}
// REL: (RESOL-2024-2249-INSSJP-DE#INSSJP)-[CITA]->(RESOL-2022-973-INSSJP-DE#INSSJP)

        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:`CITA`]->(b)
        SET r += $props
        
// Params: {}
// REL: (RESOL-2024-2249-INSSJP-DE#INSSJP)-[CITA]->(RESOL-2022-1085-INSSJP-DE#INSSJP)

        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:`CITA`]->(b)
        SET r += $props
        
// Params: {}
// REL: (RESOL-2024-2249-INSSJP-DE#INSSJP)-[CITA]->(RESOL-2024-1272-INSSJP-DE#INSSJP)

        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:`CITA`]->(b)
        SET r += $props
        
// Params: {}
// REL: (RESOL-2024-2249-INSSJP-DE#INSSJP)-[REGULA]->(Pasantías)

        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:`REGULA`]->(b)
        SET r += $props
        
// Params: {}
