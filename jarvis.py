"""Windows desktop Jarvis starter. Run with py jarvis.py."""
import base64
from array import array
import os
from pathlib import Path
from app_paths import APP_HOME
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from urllib.parse import urlencode
from news import headlines
from camera import open_camera
from voice_activity import EndOfTurn
from avatar import Avatar
import webbrowser

VOICES = {'Vaani': 'sarika_hi_conversation', 'Jansen': 'shubh_enhi_companion'}
APPS = {'notepad': ['notepad.exe'], 'calculator': ['calc.exe'],
        'explorer': ['explorer.exe']}
SETTINGS = {'display': 'ms-settings:display', 'sound': 'ms-settings:sound',
            'accessibility': 'ms-settings:easeofaccess'}


def parse(text):
    action, _, value = text.strip().partition(' ')
    return action.casefold(), value.strip()


def sarvam_key():
    key = os.environ.get('SARVAM_API_KEY', '').strip()
    config = APP_HOME / '.env'
    if not key and config.is_file():
        for line in config.read_text(encoding='utf-8-sig').splitlines():
            name, _, value = line.partition('=')
            if name.strip() == 'SARVAM_API_KEY':
                key = value.strip()
                break
    return key


def speak(role, text):
    import winsound
    from sarvamai import SarvamAI
    key = sarvam_key()
    if not key:
        raise ValueError('No key')
    audio = SarvamAI(api_subscription_key=key).text_to_speech.convert(
        text=text, language_code='hi-IN', model='bulbul:v4-flash',
        speaker=VOICES[role], output_audio_codec='wav')
    winsound.PlaySound(base64.b64decode(audio.audios[0]), winsound.SND_MEMORY)


def run():
    root = tk.Tk()
    root.title('Vanijen AI')
    app_assets = Path(__file__).resolve().parent / 'assets'
    if sys.platform == 'win32' and (app_assets / 'vanijen-icon.ico').is_file():
        root.iconbitmap(str(app_assets / 'vanijen-icon.ico'))
    root.configure(bg='#17151d')
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background='#17151d', foreground='#f4eaf3', font=('Segoe UI', 10))
    style.configure('TButton', background='#302838', foreground='#faf2f8', padding=(10, 5), borderwidth=0)
    style.map('TButton', background=[('active', '#49364f'), ('disabled', '#221f29')])
    style.configure('TEntry', fieldbackground='#24202b', foreground='#faf2f8', insertcolor='white', padding=6)
    style.configure('TCombobox', fieldbackground='#302838', foreground='#faf2f8', arrowcolor='#faf2f8')
    style.map('TCombobox', fieldbackground=[('readonly','#302838')], foreground=[('readonly','#faf2f8')])
    root.geometry('900x780')
    role = tk.StringVar(value='Vaani')
    status = tk.StringVar(value='Ready')
    credit = tk.StringVar(value='Mujhe Akshii ne banaya hai.')
    style.configure('Stage.TFrame', background='#221e2b')
    style.configure('Stage.TLabel', background='#221e2b', foreground='#f4eaf3')
    style.configure('Accent.TButton', background='#e9b1d0', foreground='#221626')
    style.map('Accent.TButton', background=[('active', '#f1c3dd')])
    stage = ttk.Frame(root, style='Stage.TFrame')
    stage.pack(fill='x', padx=18, pady=(16, 0))
    ttk.Label(stage, text='V A N I J E N   A I   /   C O M P A N I O N', style='Stage.TLabel',
              font=('Segoe UI', 9, 'bold')).pack(pady=(10, 5))
    avatar = Avatar(stage, portrait_height=275)
    avatar.configure(style='Stage.TLabel')
    avatar.pack()
    avatar.show(role.get())
    ttk.Label(stage, textvariable=role, style='Stage.TLabel', font=('Segoe UI', 18, 'bold')).pack(pady=(4,0))
    ttk.Label(stage, textvariable=credit, style='Stage.TLabel').pack(pady=(0,9))

    frame = ttk.Frame(root, padding=18)
    frame.pack(fill='both', expand=True)
    header = ttk.Frame(frame)
    header.pack(fill='x')
    ttk.Label(header, text='Conversation', font=('Segoe UI', 16, 'bold')).pack(side='left')
    picker = ttk.Combobox(header, textvariable=role, values=list(VOICES), state='readonly', width=8)
    picker.pack(side='right')
    ttk.Label(frame, text='Session chat  ·  Voice transcripts appear here').pack(anchor='w', pady=(5, 13))
    chat = tk.Text(frame, height=5, wrap='word', state='disabled', bg='#24202b',
                   fg='#f4eaf3', relief='flat', font=('Segoe UI', 10), padx=10, pady=8)
    chat.pack(fill='both', expand=True)
    chat.tag_configure('speaker', foreground='#f4aab9')
    stop_audio = threading.Event()

    def add_chat(speaker, text):
        chat.configure(state='normal')
        chat.insert('end', speaker + '\n', 'speaker')
        chat.insert('end', text + '\n\n')
        chat.configure(state='disabled')
        chat.see('end')

    tools = ttk.Frame(frame)
    tools.pack(fill='x', pady=(8, 0))
    audio_controls = ttk.Frame(frame)
    audio_controls.pack(fill='x', pady=(8, 0))
    recording = None
    cloud_camera = tk.BooleanVar(value=False)
    detector = None
    checked_frames = 0
    frames = []
    histories = {name: [] for name in VOICES}
    capture = threading.Event()
    other_audio = threading.Event()
    turn_busy = False

    def play_other(agent, text):
        other_audio.set()
        try:
            speak(agent, text)
        finally:
            other_audio.clear()

    def confirm_camera(selected=None):
        selected = selected or role.get()
        enabled = cloud_camera.get()
        status.set('Camera: one snapshot for analysis.' if enabled else 'Camera: local preview only. Enable camera analysis to auto-send one frame.')
        open_camera(root, selected, sarvam_key, play_other, auto_analyze=enabled, report=add_chat)

    def camera_choice():
        if cloud_camera.get() and not messagebox.askyesno('Camera analysis',
                'For this session, send one snapshot to Sarvam whenever you explicitly open Camera or request it by voice? Only enable when everyone in view agrees.', parent=root):
            cloud_camera.set(False)


    def reset_turn():
        nonlocal detector, checked_frames
        frames.clear()
        detector, checked_frames = EndOfTurn(pause_seconds=0.95), 0

    def mic():
        nonlocal recording
        if recording is not None:
            capture.clear()
            recording.stop()
            recording.close()
            recording = None
            reset_turn()
            stop_audio.set()
            mic_button.configure(text='Start mic')
            status.set('Mic off')
            if not collapsed:
                avatar.show(role.get())
            return
        if not sarvam_key():
            status.set('Add your Sarvam key before starting voice chat.')
            return
        try:
            import sounddevice as sd
            def receive(data, *_):
                if capture.is_set() and not other_audio.is_set():
                    frames.append(bytes(data))
            reset_turn()
            recording = sd.RawInputStream(samplerate=16000, channels=1, dtype='int16', callback=receive)
            recording.start()
            if not turn_busy:
                capture.set()
        except Exception as exc:
            if recording is not None:
                recording.close()
            recording = None
            status.set(f'Microphone unavailable ({type(exc).__name__}).')
            return
        mic_button.configure(text='Mic off')
        status.set('Mic on · listening for your next turn')
        if not collapsed:
            avatar.show(role.get(), 'listening')

    def send_turn():
        nonlocal turn_busy
        capture.clear()
        audio = b''.join(frames)
        reset_turn()
        if not audio:
            capture.set()
            return
        turn_busy = True
        selected = role.get()
        status.set('Sending voice…')
        if not collapsed:
            avatar.show(selected, 'thinking')
        stop_audio.clear()

        def done():
            nonlocal turn_busy
            turn_busy = False
            end_speech()
            if recording is not None:
                reset_turn()
                capture.set()
                if not status.get().startswith('Voice chat failed'):
                    status.set('Mic on · listening for your next turn')
                if not collapsed:
                    avatar.show(role.get(), 'listening')
            else:
                if not collapsed:
                    avatar.show(role.get())

        def worker():
            try:
                from voice_chat import converse
                converse(selected, VOICES[selected], audio, histories[selected],
                         lambda msg: root.after(0, status.set, msg),
                         lambda agent: root.after(0, confirm_camera, agent),
                         lambda target: root.after(0, switch_agent, target),
                         lambda speaker, mood: root.after(0, show_speech_popup, speaker, mood),
                         lambda speaker, text: root.after(0, add_chat, speaker, text), stop_audio)
            except Exception as exc:
                root.after(0, status.set, f'Voice chat failed ({type(exc).__name__}). Check key, internet and credits.')
            finally:
                root.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def show_news(query=''):
        panel = tk.Toplevel(root)
        panel.title('Research headlines' if query else 'Jansen | News briefing')
        panel.geometry('700x360')
        body = ttk.Frame(panel, padding=14)
        body.pack(fill='both', expand=True)
        label = ttk.Label(body, text='Fetching public headlines…', wraplength=650)
        label.pack(anchor='w')

        def render(items):
            if not panel.winfo_exists():
                return
            label.configure(text='Headline research • Google News India' if items else 'No headlines available right now.')
            for title, link, source, published in items:
                text = f'{title} | {source} {published}'
                line = ttk.Label(body, text=text, wraplength=650, cursor='hand2', foreground='#1759aa')
                line.pack(anchor='w', pady=5)
                line.bind('<Button-1>', lambda _event, url=link: webbrowser.open(url))
            if items and not query:
                def read():
                    def audio():
                        try:
                            play_other('Jansen', 'सर, मुझे Aksh sir ने बनाया है। आज की headlines। ' + '। '.join(row[0] for row in items[:3]))
                        except Exception:
                            root.after(0, status.set, 'News voice failed. Check Sarvam key and credits.')
                    threading.Thread(target=audio, daemon=True).start()
                ttk.Button(body, text='Jansen: Read top 3', command=read).pack(anchor='w', pady=8)

        def worker():
            try:
                items = headlines(query)
            except Exception:
                items = []
            root.after(0, render, items)
        threading.Thread(target=worker, daemon=True).start()

    def select_role(_event=None):
        if not collapsed:
            avatar.show(role.get())
        if role.get() == 'Jansen':
            credit.set('Sir, mujhe Aksh sir ne banaya hai.')
            show_news()
        else:
            credit.set('Mujhe Akshii ne banaya hai.')

    def switch_agent(target):
        if role.get() != target:
            role.set(target)
            select_role()

    def research_topic():
        query = simpledialog.askstring('Research', 'Topic to look up:', parent=root)
        if query and query.strip():
            show_news(query.strip())

    picker.bind('<<ComboboxSelected>>', select_role)
    ttk.Button(tools, text='Research', command=lambda: research_topic()).pack(side='left', padx=(0,6))
    ttk.Button(tools, text='Camera', command=confirm_camera).pack(side='left', padx=(0,6))
    ttk.Button(tools, text='News briefing', command=show_news).pack(side='left', padx=(0,6))

    def branded_key_dialog():
        popup = tk.Toplevel(root, bg='#17151d')
        popup.title('Vanijen AI · Voice setup')
        popup.transient(root)
        popup.resizable(False, False)
        panel = ttk.Frame(popup, padding=22)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='Connect Sarvam', font=('Segoe UI', 19, 'bold')).pack(anchor='w')
        ttk.Label(panel, text='One key for both agents. Saved only on this device.').pack(anchor='w', pady=(4, 10))
        field = ttk.Entry(panel, width=43, show='•')
        field.pack(fill='x')
        result = []
        def save(_event=None):
            result.append(field.get())
            popup.destroy()
        row = ttk.Frame(panel)
        row.pack(fill='x', pady=(12, 0))
        ttk.Button(row, text='Save key', command=save, style='Accent.TButton').pack(side='right')
        ttk.Button(row, text='Skip', command=popup.destroy).pack(side='right', padx=6)
        popup.bind('<Return>', save)
        popup.grab_set()
        field.focus_set()
        root.wait_window(popup)
        return result[0] if result else None

    def setup_key(quiet=False):
        config = APP_HOME / '.env'
        try:
            lines = config.read_text(encoding='utf-8-sig').splitlines() if config.is_file() else []
            if quiet and (os.getenv('SARVAM_API_KEY', '').strip() or any(
                name.strip() == 'SARVAM_API_KEY' and value.strip()
                for name, _, value in (line.partition('=') for line in lines)
            )):
                return
            key = branded_key_dialog()
            if key is None:
                return
            key = key.strip()
            if not key or any(char.isspace() for char in key):
                messagebox.showwarning('Sarvam setup', 'Paste a non-empty key without spaces.', parent=root)
                return
            lines = [line for line in lines if line.partition('=')[0].strip() != 'SARVAM_API_KEY']
            config.write_text('\n'.join([*lines, 'SARVAM_API_KEY=' + key]) + '\n', encoding='utf-8')
            os.environ['SARVAM_API_KEY'] = key
            status.set('Sarvam key saved locally. Try Start mic.')
        except OSError:
            messagebox.showerror('Sarvam setup', 'Could not save the key. Move the app to a writable folder.', parent=root)

    ttk.Button(tools, text='API key', command=setup_key).pack(side='right')

    mic_button = ttk.Button(audio_controls, text='Start mic', command=mic, style='Accent.TButton')
    mic_button.pack(side='left', padx=(0,6))
    ttk.Button(audio_controls, text='Stop reply', command=stop_audio.set).pack(side='left')
    ttk.Checkbutton(tools, text='Camera analysis', variable=cloud_camera, command=camera_choice).pack(side='left', padx=5)
    ttk.Label(audio_controls, textvariable=status, wraplength=470).pack(side='left', padx=12)
    # The desktop shortcut starts this small companion window; expand reuses the same session.
    widget = ttk.Frame(root, padding=3)
    collapsed = False
    eyes = {name: tk.PhotoImage(file=str(app_assets / (name.lower() + '-eyes.png')))
            for name in VOICES if (app_assets / (name.lower() + '-eyes.png')).is_file()}
    strip = tk.Frame(widget, bg='#17151c', padx=5, pady=2, highlightthickness=1, highlightbackground='#f8f5fa')
    style.configure('Dock.TFrame', background='#17151c')
    widget.configure(style='Dock.TFrame')
    def mini_button(text, command, image=None):
        button = tk.Button(strip, text=text, image=image, command=command,
                           bg='#241e29', fg='#f4e7ef', activebackground='#493747',
                           activeforeground='#ffffff', bd=0, highlightthickness=0, cursor='hand2')
        button.pack(side='left', padx=2)
        return button

    mini_button('⇄', lambda: swap_widget_agent())
    eye_button = mini_button('Open Vanijen', lambda: toggle_widget(False), eyes.get(role.get()))
    mic_meter = tk.Canvas(strip, width=36, height=28, bg='#17151c', bd=0,
                          highlightthickness=1, highlightbackground='#928c99', cursor='hand2')
    mic_meter.pack(side='left', padx=3)
    meter_bars = [mic_meter.create_line(7 + i*6, 12, 7 + i*6, 17,
                                       fill='#f7f3fa', width=2, capstyle='round') for i in range(5)]
    mic_meter.bind('<Button-1>', lambda _event: mic())
    mini_button('↗', lambda: toggle_widget(False))

    def update_meter():
        nonlocal checked_frames
        level = 0.0
        if recording is not None and frames:
            samples = array('h', frames[-1])
            level = min(1.0, max((abs(n) for n in samples), default=0) / 10000)
        for i, bar in enumerate(meter_bars):
            weight = (1.0 - .23 * abs(i-2))
            half = 2 + (1 + 9*level) * weight
            x = 7 + i*6
            mic_meter.coords(bar, x, 14-half, x, 14+half)
            mic_meter.itemconfigure(bar, fill='#ffffff' if recording is not None else '#a9a0af')
        if recording is not None and capture.is_set() and detector is not None:
            count = len(frames)
            ended = any(detector.feed(block) for block in frames[checked_frames:count])
            checked_frames = count
            if ended or (detector.voiced >= 2400 and len(frames) > 1 and sum(map(len, frames)) >= 24*32000):
                send_turn()
            elif detector.voiced < 2400 and detector.quiet >= 32000:
                reset_turn()
        root.after(45, update_meter)

    update_meter()

    def swap_widget_agent():
        close_speech_popup()
        role.set('Jansen' if role.get() == 'Vaani' else 'Vaani')
        credit.set('Sir, mujhe Aksh sir ne banaya hai.' if role.get() == 'Jansen' else 'Mujhe Akshii ne banaya hai.')
        if hovering or speaking:
            reveal_cutout(role.get())

    role.trace_add('write', lambda *_: eye_button.configure(image=eyes.get(role.get()) or ''))

    def toggle_widget(compact):
        nonlocal collapsed, hovering
        collapsed = compact
        if compact:
            avatar.stop()
            stage.pack_forget()
            frame.pack_forget()
            widget.pack(fill='both', expand=True)
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            x = max(0, (root.winfo_screenwidth() - 249) // 2)
            y = 8
            root.geometry(f'249x53+{x}+{y}')
            if speaking:
                reveal_cutout(role.get())
        else:
            hovering = False
            close_speech_popup()
            widget.pack_forget()
            root.overrideredirect(False)
            root.attributes('-topmost', False)
            root.geometry('900x780')
            root.update_idletasks()
            root.geometry('+%d+%d' % (max(0, (root.winfo_screenwidth()-900)//2), max(0, (root.winfo_screenheight()-780)//2)))
            stage.pack(fill='x', padx=18, pady=(16, 0))
            frame.pack(fill='both', expand=True)
            avatar.show(role.get())

    speech_popup = None
    hovering = speaking = False
    shift = 0
    shift_generation = 0

    def move_strip(target):
        nonlocal shift_generation
        shift_generation += 1
        generation, start = shift_generation, shift
        def step(n=0):
            nonlocal shift
            if generation != shift_generation:
                return
            shift = start + (target - start) * (1 - (1 - n / 9) ** 3)
            strip.place(relx=.5, y=2+round(shift), anchor='n')
            if n < 9:
                root.after(16, step, n + 1)
        step()

    move_strip(0)
    cutouts = {name: tk.PhotoImage(file=str(app_assets / (name.lower() + '-clean-cutout.png')))
               for name in VOICES if (app_assets / (name.lower() + '-clean-cutout.png')).is_file()}

    def reveal_cutout(speaker):
        nonlocal speech_popup
        if not collapsed or speaker not in cutouts or speech_popup is not None:
            return
        move_strip(6)
        picture = cutouts[speaker]
        speech_popup = popup = tk.Toplevel(root)
        popup.overrideredirect(True)
        popup.attributes('-topmost', True)
        chroma = '#010203'
        popup.configure(bg=chroma)
        if sys.platform == 'win32':
            popup.wm_attributes('-transparentcolor', chroma)
        tk.Label(popup, image=picture, bg=chroma, bd=0).pack()
        width, height = picture.width(), picture.height()
        x = max(0, (root.winfo_screenwidth() - width) // 2)
        side = -1
        root.lift()  # Keep the microphone strip in front during the reveal.
        def glide(step=0):
            if speech_popup is not popup:
                return
            eased = 1 - (1 - step / 30) ** 4
            slide_x = max(0, min(root.winfo_screenwidth() - width, round(x + side * 151 * eased)))
            popup.geometry(f'{width}x{height}+{slide_x}+{round(8 + 16 * eased)}')
            if step < 30:
                root.after(16, glide, step + 1)
        glide()

    def show_speech_popup(speaker, mood):
        nonlocal speaking
        if role.get() != speaker:
            return
        status.set(speaker + ' is speaking…')
        speaking = True
        if collapsed:
            reveal_cutout(speaker)
        else:
            avatar.show(speaker, mood)

    def close_speech_popup():
        nonlocal speech_popup
        if speech_popup is not None and speech_popup.winfo_exists():
            speech_popup.destroy()
        speech_popup = None
        move_strip(0)

    def end_speech():
        nonlocal speaking
        speaking = False
        if status.get().endswith('is speaking…'):
            status.set('Ready' if not stop_audio.is_set() else 'Playback stopped.')
        if not hovering:
            close_speech_popup()

    def hover_enter(_event):
        nonlocal hovering
        hovering = True
        reveal_cutout(role.get())

    def hover_leave(_event):
        def settle():
            nonlocal hovering
            if not collapsed:
                hovering = False
                return
            x, y = root.winfo_pointerxy()
            hovering = (root.winfo_rootx() <= x < root.winfo_rootx()+root.winfo_width()
                        and root.winfo_rooty() <= y < root.winfo_rooty()+root.winfo_height())
            if not hovering and not speaking:
                close_speech_popup()
        root.after(90, settle)


    for part in (widget, strip, *strip.winfo_children()):
        part.bind('<Enter>', hover_enter, add='+')
        part.bind('<Leave>', hover_leave, add='+')

    preference = APP_HOME / 'widget.preference'

    def save_widget(allowed):
        try:
            preference.write_text('on' if allowed else 'off', encoding='utf-8')
        except OSError:
            status.set('Could not save widget preference; it applies for this session.')
        if allowed:
            toggle_widget(True)

    def first_launch():
        setup_key(quiet=True)
        if not sarvam_key():
            status.set('Add a Sarvam key to enable voice chat.')
            return
        if preference.is_file() and preference.read_text(encoding='utf-8').strip() == 'on':
            toggle_widget(True)

    ttk.Button(tools, text='Show widget', command=lambda: save_widget(True)).pack(side='left', padx=(0,6))
    ttk.Button(tools, text='Keep full app', command=lambda: save_widget(False)).pack(side='left')
    root.after(200, first_launch)

    def shutdown():
        if recording is not None:
            mic()
        stop_audio.set()
        root.destroy()
    root.protocol('WM_DELETE_WINDOW', shutdown)
    root.mainloop()


if __name__ == '__main__':
    run()
