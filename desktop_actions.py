"""Validated voice actions: model output is data, never executable code."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode, urlsplit, parse_qs
import re
import webbrowser

APPS = {'notepad': 'notepad.exe', 'calculator': 'calc.exe', 'explorer': 'explorer.exe'}
SETTINGS = {'display': 'ms-settings:display', 'sound': 'ms-settings:sound', 'accessibility': 'ms-settings:easeofaccess'}


def parse_action(raw):
    data = json.loads(raw)
    if not isinstance(data, dict) or set(data) != {'action', 'value'}:
        raise ValueError('Invalid action format')
    action, value = data['action'], data['value']
    if not isinstance(action, str) or not isinstance(value, str) or len(value) > 2000:
        raise ValueError('Invalid action fields')
    value = value.strip()
    if action == 'switch' and value in {'Vaani', 'Jansen'}:
        return action, value
    if action == 'chat' or (action == 'camera' and not value):
        return action, ''
    if action == 'open' and value in APPS or action == 'settings' and value in SETTINGS or action in {'note', 'search', 'youtube'} and value:
        return action, value
    raise ValueError('Unsupported action')


def youtube_url(value):
    text = value.strip()
    link = urlsplit(text) if text.startswith('https://') else None
    if link and not link.username and not link.password:
        video = ''
        if link.netloc.lower() == 'youtu.be':
            video = link.path.strip('/')
        elif link.netloc.lower() in {'youtube.com', 'www.youtube.com', 'm.youtube.com'}:
            if link.path == '/watch':
                video = parse_qs(link.query).get('v', [''])[0]
            elif link.path.startswith('/shorts/'):
                video = link.path.split('/')[2]
        if re.fullmatch(r'[A-Za-z0-9_-]{11}', video):
            return 'https://www.youtube.com/watch?' + urlencode({'v': video})
    return 'https://www.youtube.com/results?' + urlencode({'search_query': text})


def execute(action, value):
    if sys.platform != 'win32':
        raise OSError('Desktop actions require Windows')
    if action == 'open':
        subprocess.Popen([APPS[value]])
    elif action == 'settings':
        os.startfile(SETTINGS[value])
    elif action == 'note':
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', prefix='jarvis-note-', delete=False) as f:
            f.write(value)
        subprocess.Popen(['notepad.exe', str(Path(f.name))])
    elif action == 'youtube':
        if not webbrowser.open(youtube_url(value)):
            raise OSError('Browser launch failed')
    elif action == 'search':
        if not webbrowser.open('https://www.google.com/search?' + urlencode({'q': value})):
            raise OSError('Browser launch failed')
    else:
        raise ValueError('Unsupported action')
