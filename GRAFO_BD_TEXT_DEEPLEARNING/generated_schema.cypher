// === Constraints de nodos ===

CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product) REQUIRE n.product_id IS NOT NULL;

CREATE CONSTRAINT IF NOT EXISTS FOR (n:Review) REQUIRE n.review_id IS NOT NULL;

CREATE CONSTRAINT IF NOT EXISTS FOR (n:Supplier) REQUIRE n.supplier_id IS NOT NULL;

CREATE CONSTRAINT IF NOT EXISTS FOR (n:SupplierProduct) REQUIRE n.supplier_id IS NOT NULL;


// === LOAD CSV para nodos ===

// Carga de nodos :Product desde product.csv
LOAD CSV WITH HEADERS FROM 'file:///product.csv' AS row
MERGE (n:Product { product_id: row.product_id })
SET n.name = row.name, n.category = row.category
;

// Carga de nodos :Review desde review.csv
LOAD CSV WITH HEADERS FROM 'file:///review.csv' AS row
MERGE (n:Review { review_id: row.review_id })
SET n.product_id = row.product_id, n.rating = row.rating, n.comment = row.comment
;

// Carga de nodos :Supplier desde supplier.csv
LOAD CSV WITH HEADERS FROM 'file:///supplier.csv' AS row
MERGE (n:Supplier { supplier_id: row.supplier_id })
SET n.name = row.name, n.country = row.country
;

// Carga de nodos :SupplierProduct desde supplier_product.csv
LOAD CSV WITH HEADERS FROM 'file:///supplier_product.csv' AS row
MERGE (n:SupplierProduct { supplier_id: row.supplier_id })
SET n.lead_time_days = row.lead_time_days, n.product_id = row.product_id
;


// === LOAD CSV para relaciones ===

// Carga de relaciones :HAS_REVIEW desde review.csv
LOAD CSV WITH HEADERS FROM 'file:///review.csv' AS row
MATCH (from:Product { product_id: row.product_id })
MATCH (to:Review { product_id: row.product_id })
MERGE (from)-[r:HAS_REVIEW]->(to)

;

// Carga de relaciones :SUPPLIES_PRODUCT desde supplier_product.csv
LOAD CSV WITH HEADERS FROM 'file:///supplier_product.csv' AS row
MATCH (from:Supplier { supplier_id: row.supplier_id })
MATCH (to:SupplierProduct { supplier_id: row.supplier_id })
MERGE (from)-[r:SUPPLIES_PRODUCT]->(to)

;

// Carga de relaciones :PRODUCT_SUPPLIED desde supplier_product.csv
LOAD CSV WITH HEADERS FROM 'file:///supplier_product.csv' AS row
MATCH (from:SupplierProduct { product_id: row.product_id })
MATCH (to:Product { product_id: row.product_id })
MERGE (from)-[r:PRODUCT_SUPPLIED]->(to)

;