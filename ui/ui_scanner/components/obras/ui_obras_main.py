from tkinter import ttk
from ui.ui_scanner.components.obras.components.ui_obras_afitap import ScannerObrasAFITAP
from ui.ui_scanner.components.obras.components.ui_obras_agadu import ScannerObrasAGADU
from ui.ui_scanner.components.obras.components.ui_obras_apdayc import ScannerObrasAPDAYC
from ui.ui_scanner.components.obras.components.ui_obras_cisnet import ScannerObrasCISNET
from ui.ui_scanner.components.obras.components.ui_obras_imro import ScannerObrasIMRO
from ui.ui_scanner.components.obras.components.ui_obras_jasrac import ScannerObrasJASRAC
from ui.ui_scanner.components.obras.components.ui_obras_koda import ScannerObrasKODA
from ui.ui_scanner.components.obras.components.ui_obras_sacem import ScannerObrasSACEM
from ui.ui_scanner.components.obras.components.ui_obras_sacm import ScannerObrasSACM
from ui.ui_scanner.components.obras.components.ui_obras_sadaic import ScannerObrasSADAIC
from ui.ui_scanner.components.obras.components.ui_obras_sesac import ScannerObrasSESAC
from ui.ui_scanner.components.obras.components.ui_obras_sgae import ScannerObrasSGAE
from ui.ui_scanner.components.obras.components.ui_obras_stim import ScannerObrasSTIM
from ui.ui_scanner.components.obras.components.ui_obras_suisa import ScannerObrasSUISA
from ui.ui_scanner.components.obras.components.ui_obras_tono import ScannerObrasTONO
from ui.ui_scanner.components.obras.components.ui_obras_peer import ScannerObrasPEER
from ui.ui_scanner.components.obras.components.ui_obras_msg import ScannerObrasMSG
from ui.ui_scanner.components.obras.components.ui_obras_mesam import ScannerObrasMESAM
from ui.ui_scanner.components.obras.components.ui_obras_abramus import ScannerObrasABRAMUS
from ui.ui_scanner.components.obras.components.ui_obras_apra import ScannerObrasAPRA

class ObrasMain(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.body = ttk.Frame(self)
        self.body.grid(row=0, column=0, sticky="nsew")

        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

        self.vistas_clases = {
            "AFITAP": ScannerObrasAFITAP,
            "AGADU": ScannerObrasAGADU,
            "APDAYC": ScannerObrasAPDAYC,
            "CISNET": ScannerObrasCISNET,
            "IMRO": ScannerObrasIMRO,
            "JASRAC": ScannerObrasJASRAC,
            "KODA": ScannerObrasKODA,
            "SACEM": ScannerObrasSACEM,
            "SACM": ScannerObrasSACM,
            "SADAIC": ScannerObrasSADAIC,
            "SESAC": ScannerObrasSESAC,
            "SGAE": ScannerObrasSGAE,
            "STIM": ScannerObrasSTIM,
            "SUISA": ScannerObrasSUISA,
            "TONO": ScannerObrasTONO,
            "PEER": ScannerObrasPEER,
            "MSG": ScannerObrasMSG,
            "MESAM": ScannerObrasMESAM,
            "ABRAMUS": ScannerObrasABRAMUS,
            "APRA": ScannerObrasAPRA
        }

        self.vistas = {}

    def ocultar_todo(self):
        for vista in self.vistas.values():
            vista.grid_forget()

    def cargar(self, sociedad: str):
        self.ocultar_todo()

        clase = self.vistas_clases.get(sociedad)
        if not clase:
            return  

        if sociedad not in self.vistas:
            self.vistas[sociedad] = clase(self.body)

        vista = self.vistas[sociedad]
        vista.grid(row=0, column=0, sticky="nsew")



    