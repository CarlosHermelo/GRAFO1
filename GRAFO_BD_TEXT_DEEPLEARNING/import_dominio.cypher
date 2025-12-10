CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product) REQUIRE n.product_id IS UNIQUE;
LOAD CSV WITH HEADERS FROM 'file:/product.csv' AS row
            CALL {
                WITH row
                MERGE (n:Product { product_id: row.product_id })
                SET n += row
            } IN TRANSACTIONS OF 1000 ROWS;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Review) REQUIRE n.review_id IS UNIQUE;
LOAD CSV WITH HEADERS FROM 'file:/review.csv' AS row
            CALL {
                WITH row
                MERGE (n:Review { review_id: row.review_id })
                SET n += row
            } IN TRANSACTIONS OF 1000 ROWS;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Supplier) REQUIRE n.supplier_id IS UNIQUE;
LOAD CSV WITH HEADERS FROM 'file:/supplier.csv' AS row
            CALL {
                WITH row
                MERGE (n:Supplier { supplier_id: row.supplier_id })
                SET n += row
            } IN TRANSACTIONS OF 1000 ROWS;
LOAD CSV WITH HEADERS FROM 'file:/review.csv' AS row
            CALL {
                WITH row
                MATCH (source:Product { product_id: row.product_id })
                MATCH (target:Review { review_id: row.review_id })
                MERGE (source)-[r:HAS_REVIEW]->(target)
                SET r += row
            } IN TRANSACTIONS OF 1000 ROWS;
LOAD CSV WITH HEADERS FROM 'file:/supplier_product.csv' AS row
            CALL {
                WITH row
                MATCH (source:Supplier { supplier_id: row.supplier_id })
                MATCH (target:Product { product_id: row.product_id })
                MERGE (source)-[r:SUPPLIES]->(target)
                SET r += row
            } IN TRANSACTIONS OF 1000 ROWS;
