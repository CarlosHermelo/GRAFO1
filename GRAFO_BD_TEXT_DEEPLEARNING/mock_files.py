# mock_data.py
import os

def create_mock_files():
    # 1. Crear CSVs (Estructurado)
    with open("products.csv", "w") as f:
        f.write("product_id,name,cost,category\nP1,Mesa,100,Furniture\nP2,Silla,50,Furniture")
    
    with open("reviews.csv", "w") as f: # Un archivo trampa para probar al agente
        f.write("id,rating,comment\n1,5,Good\n2,1,Bad")
        
    with open("sales_2020.xlsx", "w") as f: # Archivo basura que debería ignorar
        f.write("dummy data")

    # 2. Crear Markdown (No Estructurado)
    with open("customer_feedback.md", "w") as f:
        f.write("""
        ---
        Review P1:
        La mesa es robusta pero el ensamblaje fue difícil.
        Hubo un Problema con los tornillos faltantes.
        ---
        Review P2:
        La silla es cómoda. Gran Característica: soporte lumbar.
        """)
        
    print("✅ Archivos de prueba creados: products.csv, reviews.csv, sales_2020.xlsx, customer_feedback.md")

if __name__ == "__main__":
    create_mock_files()