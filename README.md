# Vanijen AI

Vanijen AI is a Windows desktop companion with Vaani and Jansen, voice chat powered by Sarvam, a compact desktop widget, and a full chat panel. The original source is MIT-licensed. Sarvam is a hosted service; voice requires an API key, internet and available credits.

## Run from VS Code on Windows

Open this folder in VS Code. In its terminal run:

```powershell
py -m pip install -r requirements.txt
py jarvis.py
```

Alternatively, run `Setup.vbs` to install dependencies and create the **Vanijen AI** desktop shortcut. On first launch enter a Sarvam key in the app. The key is stored in a local `.env`. Use **Show widget** to enable compact startup, or **Keep full app** to disable it.

Tap **Start mic** once. Pausing ends a turn and sends it to Sarvam; the microphone stays open and ignores input during the reply, then resumes listening until you turn it off. Transcripts are displayed after speech-to-text completes. The transcript panel is session-only. The command-entry section is intentionally absent; supported voice actions include opening selected apps and browser searches. YouTube titles open search results, exact supported video links open a watch page. Cloud camera analysis is opt-in and sends one snapshot per explicit camera request after being enabled, not a video stream.

Vaani uses a still portrait by default. Optional local idle/listening/thinking videos can be added by the user. Jansen uses still normal/thinking portraits. When media is present, the compact widget shows the active character's eyes and a sideways reveal. If a portrait is missing, the panel falls back to the character name.

## Build a standalone Windows app

On a Windows build machine with Python and the approved `assets/` folder, run `Build-Windows-App.bat`. The build produces `dist/Vanijen AI/Vanijen AI.exe`. Distribute the entire `dist/Vanijen AI` folder, including `_internal`. Users of that bundle do not need to install Python. This is a portable app bundle, not an MSI installer.

After publishing the repo, open **Actions → Build Windows desktop app → Run workflow**. Download the `Vanijen-AI-Windows` artifact and verify it on Windows before publishing a release. The build workflow does not need any Sarvam API key.

## Source and assets

Never commit `.env`, recordings or user preferences. The MIT license covers original code; it does not grant redistribution rights for third-party assets or hosted models. The public-source package includes still artwork, not the privately supplied videos. See `ASSETS.md` for provenance, optional clip locations, and redistribution notes. No `.env` is shipped; the app creates it locally only if the user saves a key.

## Publish on GitHub

1. Extract the source ZIP. Create an empty public repository named `vanijen-ai`.
2. Upload the extracted source, including `.github/` and `.gitignore`. Do not upload any local `.env`.
3. Run the Windows build workflow, test the extracted artifact on Windows 10/11, then attach that artifact ZIP to a GitHub Release. Users download the release ZIP, extract the whole archive, and launch `Vanijen AI.exe`. They only need their own Sarvam key for voice features.
