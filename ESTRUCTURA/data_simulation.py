import pandas as pd
import os

# Script auxiliar para crear datos de prueba si no tienes los tuyos
# Esto permite que el agente tenga algo que leer.

IMPORT_DIR = "./import_data"

if not os.path.exists(IMPORT_DIR):
    os.makedirs(IMPORT_DIR)

# 1. Proveedores
suppliers = [
    {"supplier_id": "SUP01", "name": "Acme Corp", "country": "USA"},
    {"supplier_id": "SUP02", "name": "Global Parts", "country": "Germany"},
]
pd.DataFrame(suppliers).to_csv(f"{IMPORT_DIR}/suppliers.csv", index=False)

# 2. Partes
parts = [
    {"part_id": "P001", "name": "Tornillo Hexagonal", "weight": 0.01},
    {"part_id": "P002", "name": "Placa de Acero", "weight": 2.5},
    {"part_id": "P003", "name": "Motor Electrico", "weight": 15.0},
]
pd.DataFrame(parts).to_csv(f"{IMPORT_DIR}/parts.csv", index=False)

# 3. Productos (Ensamblados)
products = [
    {"product_id": "PROD_A", "name": "Taladro Industrial", "price": 150},
    {"product_id": "PROD_B", "name": "Sierra de Mesa", "price": 300},
]
pd.DataFrame(products).to_csv(f"{IMPORT_DIR}/products.csv", index=False)

# 4. Relación Partes-Proveedores (Suministra)
supplies = [
    {"supplier_id": "SUP01", "part_id": "P001", "cost": 0.05},
    {"supplier_id": "SUP01", "part_id": "P002", "cost": 10.0},
    {"supplier_id": "SUP02", "part_id": "P003", "cost": 120.0},
]
pd.DataFrame(supplies).to_csv(f"{IMPORT_DIR}/part_suppliers.csv", index=False)

# 5. Relación Producto-Partes (BOM - Bill of Materials)
bom = [
    {"product_id": "PROD_A", "part_id": "P001", "quantity": 10},
    {"product_id": "PROD_A", "part_id": "P003", "quantity": 1},
    {"product_id": "PROD_B", "part_id": "P002", "quantity": 1},
]
pd.DataFrame(bom).to_csv(f"{IMPORT_DIR}/bom.csv", index=False)

print(f"Datos generados en {IMPORT_DIR}")