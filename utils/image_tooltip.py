import tkinter as tk
from tkinter import ttk

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except Exception:
    PIL_OK = False


class ImageTooltip:
    def __init__(
        self,
        widget,
        image_path=None,
        photo=None,
        text=None,
        max_size=(520, 320),
        pad=(10, 6),
        image_path_getter=None,
        text_getter=None  
    ):
        self.widget = widget
        self.image_path = image_path
        self.image_path_getter = image_path_getter  # <-- NUEVO
        self.photo = photo
        self.text = text
        self.text_getter = text_getter
        self.max_size = max_size
        self.pad = pad

        self._tw = None
        self._img_ref = None

        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<Motion>", self._move, add="+")

    def set_image_path(self, image_path: str):
        """Opcional: cambiar imagen manualmente."""
        self.image_path = image_path
        self.photo = None
        self._img_ref = None

    def _current_image_path(self):
        if callable(self.image_path_getter):
            try:
                return self.image_path_getter()
            except Exception:
                return None
        return self.image_path

    def _load_image(self):
        if self.photo is not None:
            self._img_ref = self.photo
            return self._img_ref

        path = self._current_image_path()
        if not path:
            return None

        if path.lower().endswith(".gif"):
            self._img_ref = tk.PhotoImage(file=path)
            return self._img_ref

        if not PIL_OK:
            return None

        img = Image.open(path)
        img.thumbnail(self.max_size)
        self._img_ref = ImageTk.PhotoImage(img)
        return self._img_ref

    def _show(self, _event=None):
        if self._tw is not None:
            return

        self._tw = tk.Toplevel(self.widget)
        self._tw.wm_overrideredirect(True)
        self._tw.attributes("-topmost", True)

        frm = ttk.Frame(self._tw, padding=self.pad, relief="solid", borderwidth=1)
        frm.pack()

        txt = self._current_text()
        if txt:
            ttk.Label(frm, text=txt, justify="left").pack(anchor="w", pady=(0, 6))

        img = self._load_image()
        if img is not None:
            ttk.Label(frm, image=img).pack()
        else:
            ttk.Label(frm, text="(No se pudo cargar la imagen de ayuda)").pack(anchor="w")

        self._position()

    def _move(self, _event=None):
        if self._tw is not None:
            self._position()

    def _position(self):
        x = self.widget.winfo_pointerx() + 12
        y = self.widget.winfo_pointery() + 12
        self._tw.geometry(f"+{x}+{y}")

    def _hide(self, _event=None):
        if self._tw is not None:
            self._tw.destroy()
            self._tw = None
            
    def _current_text(self):
        if callable(self.text_getter):
            try:
                return self.text_getter()
            except Exception:
                return ""
        return self.text