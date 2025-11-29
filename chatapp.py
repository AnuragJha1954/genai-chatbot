"""
Simple Tkinter desktop chat app for Google GenAI (gemini) using the sample code you provided.

How to use:
1. Install dependencies: pip install google-generativeai
   (or the package name you use for genai; adjust if different)
2. Replace the API_KEY value below with your API key, or set the environment variable
   GENAI_API_KEY and the app will pick it up automatically.
3. Run: python tk_genai_chat.py

Notes:
- Network calls run in a background thread so the UI doesn't freeze.
- Keep your API key private. Do not commit it into public repos.
"""

import threading
import queue
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Import the client you used in your sample code. Adjust import if your package name differs.
from google import genai

# ---------- Configuration ----------
# You can either hardcode your key here (NOT RECOMMENDED) or set the GENAI_API_KEY environment
# variable. Example (Linux/macOS): export GENAI_API_KEY="YOUR_KEY"
API_KEY = os.environ.get("GENAI_API_KEY", "AIzaSyC2z6JrSJiz2CfbACivW4l8b07wm_Ou3ZY")
MODEL_NAME = "gemini-2.5-flash"

# ---------- Chat wrapper ----------
class GenAIChat:
    def __init__(self, api_key: str, model: str = MODEL_NAME):
        if not api_key:
            raise ValueError("API key is required. Set the GENAI_API_KEY environment variable.")
        self.client = genai.Client(api_key=api_key)
        
        self.chat = self.client.chats.create(model=model)

    def send(self, text: str) -> str:
        """Send a message and return the model's text reply."""
        
        response = self.chat.send_message(text)
        
        return response.text

    def get_history(self):
        return list(self.chat.get_history())

# ---------- Tkinter UI ----------
class ChatApp(tk.Tk):
    def __init__(self, chat_client: GenAIChat):
        super().__init__()
        self.title("GenAI Chat — Tkinter")
        self.geometry("800x520")
        self.chat_client = chat_client
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Thread-safe queue for responses
        self._resp_queue = queue.Queue()

        self._build_ui()
        # Start a periodic check for results from worker threads
        self.after(100, self._poll_queue)

    def _build_ui(self):
        # Top frame for controls
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        ttk.Label(top, text="Model:").pack(side=tk.LEFT)
        self.model_label = ttk.Label(top, text=MODEL_NAME)
        self.model_label.pack(side=tk.LEFT, padx=(4, 12))

        ttk.Button(top, text="History", command=self._show_history).pack(side=tk.RIGHT)
        ttk.Button(top, text="Quit", command=self._on_close).pack(side=tk.RIGHT, padx=6)

        # Chat display
        self.chat_display = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,6))

        # Bottom frame for entry
        bottom = ttk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=6)

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(bottom, textvariable=self.entry_var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind('<Return>', lambda e: self._on_send())

        send_btn = ttk.Button(bottom, text="Send", command=self._on_send)
        send_btn.pack(side=tk.LEFT, padx=6)

    def _append_text(self, text: str, tag: str = None):
        self.chat_display.configure(state=tk.NORMAL)
        if tag:
            self.chat_display.insert(tk.END, text + "\n", tag)
        else:
            self.chat_display.insert(tk.END, text + "\n")
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _on_send(self):
        user_text = self.entry_var.get().strip()
        if not user_text:
            return
        # show in chat
        self._append_text("User: " + user_text)
        # clear entry
        self.entry_var.set("")
        # start a background thread to call the API
        threading.Thread(target=self._worker_send, args=(user_text,), daemon=True).start()

    def _worker_send(self, text: str):
        try:
            resp_text = self.chat_client.send(text)
            # put in queue to update UI from main thread
            self._resp_queue.put((True, resp_text))
        except Exception as e:
            self._resp_queue.put((False, str(e)))

    def _poll_queue(self):
        try:
            while True:
                ok, payload = self._resp_queue.get_nowait()
                if ok:
                    self._append_text("MODEL: " + payload)
                else:
                    messagebox.showerror("Error", f"Failed to get response:\n{payload}")
        except queue.Empty:
            pass
        # schedule next poll
        self.after(100, self._poll_queue)

    def _show_history(self):
        try:
            hist = self.chat_client.get_history()
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch history:\n{e}")
            return
        # Build a simple string
        s = []
        for msg in hist:
            # message may have role and parts; adapt as needed
            role = getattr(msg, 'role', 'unknown')
            text = ''
            if hasattr(msg, 'parts') and len(msg.parts) > 0:
                # parts elements may have 'text'
                part = msg.parts[0]
                text = getattr(part, 'text', str(part))
            else:
                text = str(msg)
            s.append(f"role - {role}: {text}")
        # Show in a dialog
        HistoryDialog(self, "Chat History", "\n\n".join(s))

    def _on_close(self):
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            try:
                # Optionally ask if they want to print history
                if messagebox.askyesno("History", "Print chat history to console before exit?"):
                    for message in self.chat_client.get_history():
                        try:
                            role = getattr(message, 'role', 'unknown')
                            part = message.parts[0]
                            text = getattr(part, 'text', str(part))
                            print(f'role - {role}: {text}')
                        except Exception:
                            print(message)
            except Exception:
                pass
            self.destroy()


class HistoryDialog(tk.Toplevel):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.title(title)
        self.geometry("600x400")
        txt = tk.Text(self, wrap=tk.WORD)
        txt.insert(tk.END, text)
        txt.configure(state=tk.DISABLED)
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        btn = ttk.Button(self, text="Close", command=self.destroy)
        btn.pack(pady=(0,8))


# ---------- Main ----------
def main():
    try:
        chat_client = GenAIChat(API_KEY)
    except Exception as e:
        # show a simple prompt to let user enter API key if not set
        root = tk.Tk()
        root.withdraw()
        user_key = simpledialog.askstring("API Key Required", "Enter your GenAI API key:", parent=root)
        root.destroy()
        if not user_key:
            print("No API key provided. Exiting.")
            sys.exit(1)
        chat_client = GenAIChat(user_key)

    app = ChatApp(chat_client)
    app.mainloop()


if __name__ == '__main__':
    main()
