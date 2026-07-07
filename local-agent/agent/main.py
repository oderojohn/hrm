import tkinter as tk

from agent.ui import SyncAgentApp


def main():
    root = tk.Tk()
    app = SyncAgentApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_loop(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
