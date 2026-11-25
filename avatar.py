"""Local silent playback of the selected Vaani reaction clips."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk


class Avatar(ttk.Label):
    def __init__(self, parent, portrait_height=320):
        super().__init__(parent, text='Vaani')
        self.portrait_height = portrait_height
        self.cap = self.timer = self.image = None
        self.state = None
        self.bind('<Destroy>', lambda _: self.stop())

    def stop(self):
        if self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.state = None

    def show_vaani_portrait(self):
        file = Path(__file__).resolve().parent / 'assets' / 'vaani-portrait.png'
        self.image = tk.PhotoImage(file=str(file)) if file.is_file() else None
        self.configure(image=self.image or '', text='' if self.image else 'Vaani')

    def show(self, role, state='idle'):
        if role != 'Vaani':
            self.stop()
            asset = Path(__file__).resolve().parent / 'assets' / ('jansen-thinking.png' if state == 'thinking' else 'jansen-anime.png')
            self.image = tk.PhotoImage(file=str(asset)) if asset.is_file() else None
            if self.image and self.image.height() > self.portrait_height:
                self.image = self.image.subsample(2, 2)
            self.configure(image=self.image or '', text='' if self.image else 'Jansen')
            return
        if state == self.state:
            return
        self.stop()
        self.state = state
        try:
            import cv2
        except ImportError:
            self.show_vaani_portrait()
            return
        asset = Path(__file__).resolve().parent / 'assets' / 'vaani' / (('thinking' if state == 'mock_gussa' else state) + '.mp4')
        cap = cv2.VideoCapture(str(asset))
        if not cap.isOpened():
            cap.release()
            self.show_vaani_portrait()
            return
        self.cap = cap
        delay = max(15, round(1000 / (cap.get(cv2.CAP_PROP_FPS) or 25)))

        def frame():
            self.timer = None
            ok, image = cap.read()
            if not ok:
                if state == 'idle':
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, image = cap.read()
                if not ok:
                    cap.release()
                    self.cap = None
                    return  # Hold the last reaction frame until the next app state.
            height = self.portrait_height
            width = round(height * 9 / 16)
            image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.image = tk.PhotoImage(data=f'P6\n{width} {height}\n255\n'.encode() + rgb.tobytes(), format='PPM')
            self.configure(image=self.image, text='')
            self.timer = self.after(delay, frame)
        frame()
