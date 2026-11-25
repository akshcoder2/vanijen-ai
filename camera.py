"""User-initiated, local-only webcam preview."""
import threading
import tkinter as tk

from vision import describe
from tkinter import messagebox, ttk


def open_camera(root, role, get_key, speak, auto_analyze=False, report=None):
    try:
        import cv2
    except ImportError:
        messagebox.showerror('Camera', 'Run setup.bat to install camera support.', parent=root)
        return
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        messagebox.showerror('Camera', 'Camera unavailable. Check Windows camera privacy settings or close other camera apps.', parent=root)
        return
    win = tk.Toplevel(root)
    win.title('Camera • Vanijen AI')
    ttk.Label(win, text='Camera is on • sending one snapshot only' if auto_analyze else 'Camera is on • preview stays on this laptop').pack(pady=6)
    preview = ttk.Label(win)
    preview.pack()
    timer = None
    latest = None
    closed = threading.Event()

    def close():
        closed.set()
        if timer is not None:
            win.after_cancel(timer)
        cap.release()
        win.destroy()

    def update():
        nonlocal timer, latest
        timer = None
        ok, frame = cap.read()
        if not ok:
            close()
            messagebox.showwarning('Camera', 'Camera stopped delivering video.', parent=root)
            return
        latest = frame
        h, w = frame.shape[:2]
        scale = min(640 / w, 480 / h, 1)
        frame = cv2.resize(frame, (max(1, int(w * scale)), max(1, int(h * scale))))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:2]
        preview.image = tk.PhotoImage(data=f'P6\n{w} {h}\n255\n'.encode() + frame.tobytes(), format='PPM')
        preview.configure(image=preview.image)
        timer = win.after(55, update)

    result = ttk.Label(win, text='', wraplength=460)
    result.pack(padx=10)

    def analyze():
        if latest is None:
            return
        key = get_key()
        if not key:
            messagebox.showinfo('Camera analysis', 'Set your Sarvam key first.', parent=win)
            return
        h, w = latest.shape[:2]
        scale = min(1, 768 / max(h, w))
        snapshot = cv2.resize(latest, (max(1, int(w*scale)), max(1, int(h*scale))))
        ok, encoded = cv2.imencode('.jpg', snapshot)
        if not ok or (not auto_analyze and not messagebox.askokcancel('Send one snapshot',
                'Send one webcam frame to Sarvam for analysis? Make sure everyone in view agrees. No video stream is sent.', parent=win)):
            return
        button.configure(state='disabled')
        result.configure(text='Analyzing one snapshot…')

        def display(text):
            if not closed.is_set():
                result.configure(text=text)

        def worker():
            try:
                answer = describe(encoded.tobytes(), key, role)
                root.after(0, display, answer)
                if report is not None and not closed.is_set():
                    root.after(0, report, role, answer)
                if not closed.is_set():
                    speak(role, answer)
            except Exception:
                root.after(0, display, 'Camera reply unavailable. Check internet and Sarvam credits.')
            finally:
                root.after(0, lambda: button.configure(state='normal') if not closed.is_set() else None)

        threading.Thread(target=worker, daemon=True).start()

    button = ttk.Button(win, text=f'Ask {role} about this frame', command=analyze)
    if not auto_analyze:
        button.pack(pady=5)
    ttk.Button(win, text='Stop camera', command=close).pack(pady=8)
    win.protocol('WM_DELETE_WINDOW', close)
    win.bind('<Destroy>', lambda event: (closed.set(), cap.release()) if event.widget is win else None)
    update()
    if auto_analyze and not closed.is_set():
        win.after(350, analyze)
