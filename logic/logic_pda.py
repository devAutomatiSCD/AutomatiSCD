from openpyxl import Workbook
import os
from datetime import datetime


def find(c, ruta):
    c = int(c)
    
    PDAs = []

    print(ruta)
    
    with open(ruta, "r") as f:
        PDA = int(f.readline().strip())
        
    print(PDA)
    
    PDAFinal = PDA + 1
    
    print(PDAFinal)

    if c > 0:
        PDAs = [PDAFinal + i for i in range(c)]
        print(PDAs[-1])   
    else:
        print("No se generaron PDAs (c <= 0)")
    
    return PDAs


def save(valor, ruta):
    with open(ruta, "r") as f:
        lineas = f.readlines()
        
    if not valor:
        return False

    ultimo = valor[-1]
    
    
    if not lineas:
        lineas = [f"{ultimo}\n"]
    else:
        lineas[0] = f"{ultimo}\n"

    with open(ruta, "w") as f:
        f.writelines(lineas)
        
    return True

def firstPDA(ruta):
    with open(ruta, "r") as f:
        linea = f.readlines()
    
    if not linea:
        return 0;
    
    texto = linea[0].strip()
    return texto

def exportarExcel(lista_pdas, ruta):
    
    if not ruta:
        return False
    
    ruta_final = os.path.join(
    ruta,
    f"PDAs-{datetime.now().strftime('%d-%m_%H-%M-%S')}.xlsx"
    )
    
    wb = Workbook()
    ws = wb.active

    for i, valor in enumerate(lista_pdas, start=1):
        ws.cell(row=i, column=1, value=valor)

    wb.save(ruta_final)
    
    return True
    
def crearRegistro(ruta, texto):
    with open(ruta, "a") as f:
        f.write(texto + "\n")
        
    