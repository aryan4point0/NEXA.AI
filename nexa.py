import speech_recognition as sr
import webbrowser
import pyttsx3
import importlib.util
import sys
import logging
import os
import time
import pygame
import requests
import difflib
from urllib.parse import quote_plus
import tkinter as tk
from tkinter import messagebox, scrolledtext

# ---------------------------
# CONFIG
# ---------------------------
MUSIC_LIB_PATH = r"c:\Users\aryan\OneDrive\Desktop\Python\Mega Project Jarvis\musicLibrary.py"
OPENAI_API_KEY = None  # optional
_music_map = {}

# ---------------------------
# Helpers
# ---------------------------
def is_url(s):
    return isinstance(s, str) and (s.startswith("http://") or s.startswith("https://"))

def load_music():
    """Force-load musicLibrary.py and build lowercase music map."""
    global _music_map
    try:
        if not os.path.exists(MUSIC_LIB_PATH):
            print("❌ Music library not found:", MUSIC_LIB_PATH)
            _music_map = {}
            return False, "File not found"

        if "musicLibrary" in sys.modules:
            del sys.modules["musicLibrary"]

        spec = importlib.util.spec_from_file_location("musicLibrary", MUSIC_LIB_PATH)
        musicLibrary = importlib.util.module_from_spec(spec)
        sys.modules["musicLibrary"] = musicLibrary
        spec.loader.exec_module(musicLibrary)

        music_dict = getattr(musicLibrary, "music", None)
        if not isinstance(music_dict, dict):
            _music_map = {}
            return False, "Invalid or missing 'music' dictionary."

        _music_map = {k.lower(): v for k, v in music_dict.items()}
        print(f"✅ Loaded musicLibrary from: {MUSIC_LIB_PATH}")
        print("🎵 Songs found:", list(_music_map.keys()))
        return True, None
    except Exception as e:
        print(f"❌ Error loading music library: {e}")
        _music_map = {}
        return False, e

# initial
load_music()

# ---------------------------
# Text-to-Speech
# ---------------------------
def init_speech_engine():
    try:
        engine = pyttsx3.init("sapi5")
    except Exception:
        engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    if voices:
        engine.setProperty("voice", voices[0].id)
    engine.setProperty("rate", 175)
    return engine

engine = init_speech_engine()

def speak(text):
    global engine
    """Speak text aloud and print it."""
    print("NEXA:", text)
    try:
        engine.stop()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        engine = init_speech_engine()
        engine.say(text)
        engine.runAndWait()

# ---------------------------
# Playback
# ---------------------------
def play_local_song(song_path):
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play()
        speak(f"Playing {os.path.basename(song_path)}")
        while pygame.mixer.music.get_busy():
            time.sleep(1)
    except Exception as e:
        speak(f"Error playing the song: {e}")

# ---------------------------
# Search / Play helpers
# ---------------------------
def find_song_in_library(query):
    query = query.lower().strip()
    for key in _music_map.keys():
        if query == key or query in key or key in query:
            return key
    matches = difflib.get_close_matches(query, list(_music_map.keys()), n=1, cutoff=0.6)
    return matches[0] if matches else None

def open_youtube_search(query):
    webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")

def open_spotify_search(query):
    webbrowser.open(f"https://open.spotify.com/search/{quote_plus(query)}")

def try_play_song(query):
    if not query:
        speak("Please specify a song name.")
        return

    if is_url(query):
        speak("Opening the provided link.")
        webbrowser.open(query)
        return

    key = find_song_in_library(query)
    if key:
        path = _music_map[key]
        if os.path.exists(path) and path.lower().endswith(".mp3"):
            speak(f"Playing {key} from your local library.")
            play_local_song(path)
            return
        if is_url(path):
            speak(f"Playing {key} from your library.")
            webbrowser.open(path)
            return

    speak(f"I couldn't find {query} in your library. Opening YouTube and Spotify search results.")
    open_youtube_search(query)
    open_spotify_search(query)

# ---------------------------
# Command processing
# ---------------------------
def processCommand(c):
    if not c:
        return
    cl = c.lower().strip()

    # --- Reload music ---
    if "reload music" in cl:
        ok, _ = load_music()
        speak("Music library reloaded." if ok else "Failed to reload library.")
        return

    # --- Play a song ---
    if cl.startswith("play "):
        query = cl.replace("play", "", 1).strip()
        load_music()
        try_play_song(query)
        return

    # --- Open websites ---
    sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "spotify": "https://open.spotify.com/collection/tracks",
        "netflix": "https://www.netflix.com/browse",
        "linkedin": "https://www.linkedin.com/in/aryan-singh-876b13255/",
        "instagram": "https://www.instagram.com",
        "github": "https://github.com/aryan4point0",
        "whatsapp": "https://web.whatsapp.com",
        "chatgpt": "https://chat.openai.com",
        "facebook": "https://www.facebook.com",
        "twitter": "https://x.com/AryanSi63952748",
        "gdg":"https://www.skills.google/profile/activity",
        "forage":"https://www.theforage.com/dashboard",
        "gmail":"https://mail.google.com/mail/u/0/?tab=rm&ogbl#inbox",
    }

    for name, url in sites.items():
        if f"open {name}" in cl or cl == name:
            speak(f"Opening {name}.")
            webbrowser.open(url)
            return

    # --- Search command ---
    if cl.startswith("search "):
        query = cl.replace("search", "", 1).strip()
        if query:
            speak(f"Searching for {query}.")
            webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
        else:
            speak("Please specify what to search for.")
        return

    # --- Sports scores and news ---
    if "cricket score" in cl or "cricket scores" in cl:
        speak("Searching for the latest cricket scores.")
        webbrowser.open("https://www.google.com/search?q=latest+cricket+scores")
        return

    if "football score" in cl or "football scores" in cl:
        speak("Searching for the latest football scores.")
        webbrowser.open("https://www.google.com/search?q=latest+football+scores")
        return

    if "daily news" in cl or "india news" in cl or "current affairs" in cl:
        speak("Opening today's daily India news headlines.")
        webbrowser.open("https://www.google.com/search?q=daily+india+news+headlines")
        return

    # --- Fallback ---
    speak("Sorry, I didn’t understand that command.")

# ---------------------------
# HUD GUI
# ---------------------------
def create_hud():
    BG = "#0b0f18"
    FG = "#8be9ff"
    ACCENT = "#00eaff"
    BTN_BG = "#111421"
    ENTRY_BG = "#0e1218"
    ENTRY_FG = "#e6f7ff"

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    try:
        root.attributes("-alpha", 0.88)
    except Exception:
        pass
    root.geometry("520x380+100+100")
    root.configure(bg=BG)

    def start_move(event): root.x, root.y = event.x, event.y
    def stop_move(event): root.x = root.y = None
    def do_move(event): root.geometry(f"+{event.x_root - root.x}+{event.y_root - root.y}")

    header = tk.Frame(root, bg=BG, height=44)
    header.pack(fill="x")
    for bind in ("<ButtonPress-1>", "<ButtonRelease-1>", "<B1-Motion>"):
        header.bind(bind, {"<ButtonPress-1>": start_move, "<ButtonRelease-1>": stop_move, "<B1-Motion>": do_move}[bind])

    title = tk.Label(header, text="🎛️ NEXA HUD", bg=BG, fg=FG, font=("Segoe UI", 13, "bold"))
    title.pack(side="left", padx=12, pady=8)
    for bind in ("<ButtonPress-1>", "<ButtonRelease-1>", "<B1-Motion>"):
        title.bind(bind, {"<ButtonPress-1>": start_move, "<ButtonRelease-1>": stop_move, "<B1-Motion>": do_move}[bind])

    btn_frame = tk.Frame(header, bg=BG)
    btn_frame.pack(side="right", padx=8)

    def toggle_top():
        current = bool(root.attributes("-topmost"))
        root.attributes("-topmost", not current)
        top_btn.config(text="📌" if not current else "📍")

    top_btn = tk.Button(btn_frame, text="📌", command=toggle_top, bg=BTN_BG, fg=ACCENT,
                         relief="flat", width=3, highlightthickness=0)
    top_btn.pack(side="left", padx=4, pady=6)

    def close_hud():
        if messagebox.askyesno("Exit NEXA", "Close NEXA HUD and stop voice listening?"):
            root.destroy()
            os._exit(0)

    close_btn = tk.Button(btn_frame, text="✖", command=close_hud, bg="#2a2a2a", fg="#ff6b6b",
                          relief="flat", width=3)
    close_btn.pack(side="left", padx=4, pady=6)

    body = tk.Frame(root, bg=BG)
    body.pack(fill="both", expand=True, padx=12, pady=(6,12))

    controls = tk.Frame(body, bg=BG)
    controls.pack(fill="x", pady=(6,6))

    def reload_and_update():
        ok, _ = load_music()
        if ok:
            messagebox.showinfo("NEXA", "✅ Music library reloaded successfully!")
            fill_song_list()
        else:
            messagebox.showerror("NEXA", "❌ Failed to reload music library.")

    reload_btn = tk.Button(controls, text="Reload Library", command=reload_and_update,
                           bg=BTN_BG, fg=ACCENT, relief="flat", padx=8, pady=6)
    reload_btn.pack(side="left", padx=(0,8))

    entry_frame = tk.Frame(controls, bg=BG)
    entry_frame.pack(side="left", fill="x", expand=True)

    song_entry = tk.Entry(entry_frame, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG, relief="flat", width=36)
    song_entry.pack(side="left", padx=(0,8), pady=2)

    def play_from_input():
        q = song_entry.get().strip()
        if not q:
            messagebox.showwarning("NEXA", "Please enter a song name.")
            return
        speak(f"Searching for {q}.")
        try_play_song(q)

    play_btn = tk.Button(entry_frame, text="Play", command=play_from_input,
                          bg=ACCENT, fg=BG, relief="flat", padx=10)
    play_btn.pack(side="left")

    list_frame = tk.Frame(body, bg=BG)
    list_frame.pack(fill="both", expand=True, pady=(8,0))

    song_box = scrolledtext.ScrolledText(list_frame, wrap=tk.WORD, bg="#071018", fg="#9ff6ff",
                                         insertbackground=ACCENT, relief="flat", font=("Consolas",10))
    song_box.pack(fill="both", expand=True)

    def fill_song_list():
        song_box.config(state="normal")
        song_box.delete("1.0", tk.END)
        if _music_map:
            for i, s in enumerate(_music_map.keys(), 1):
                song_box.insert(tk.END, f"{i}. {s}\n")
        else:
            song_box.insert(tk.END, "No songs found.\n")
        song_box.config(state="disabled")

    fill_song_list()

    hint = tk.Label(root, text="Say: 'NEXA play <song>' or 'NEXA open <website>' or 'NEXA cricket scores'",
                     bg=BG, fg="#6fd6ff", font=("Segoe UI", 8))
    hint.pack(side="bottom", pady=(0,8))

    def toggle_alpha(e=None):
        try:
            cur = float(root.attributes("-alpha"))
            root.attributes("-alpha", 0.52 if cur >= 0.85 else 0.92)
        except Exception:
            pass

    header.bind("<Double-Button-1>", toggle_alpha)
    title.bind("<Double-Button-1>", toggle_alpha)

    root.update_idletasks()
    return root

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    speak("Initializing NEXA HUD.")
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

    import threading
    hud_root = None
    def gui_thread():
        global hud_root
        hud_root = create_hud()
        hud_root.mainloop()

    t = threading.Thread(target=gui_thread, daemon=True)
    t.start()

    recognizer = sr.Recognizer()
    TIMEOUT = 10
    PHRASE_TIME_LIMIT = 7

    while True:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                print("\n🎤 Listening for wake word ('NEXA')...")
                audio = recognizer.listen(source, timeout=TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
                command = recognizer.recognize_google(audio)
                normalized = ''.join(ch for ch in command.lower().strip() if ch.isalnum() or ch.isspace())
                print("🗣️ Heard:", normalized)

                if "nexa" in normalized:
                    speak("Yes?")
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    print("🎧 NEXA Active... Listening for your command...")
                    audio2 = recognizer.listen(source, timeout=TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
                    try:
                        command2 = recognizer.recognize_google(audio2)
                        print("🗣️ Command received:", command2)
                        processCommand(command2)
                    except sr.UnknownValueError:
                        speak("Sorry, I didn’t catch that.")
                        continue

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as error:
                logging.exception("An error occurred:")
                print("❌ Error:", error)
                continue

