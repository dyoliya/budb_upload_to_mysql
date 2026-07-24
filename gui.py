import os
import sys
import threading
import subprocess
import io
import customtkinter as ctk
import tkinter as tk 
from tkinter import messagebox
from main import main as budb_upload_to_mysql

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class MinimalToolUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Version
        with open("version.txt", "r") as f:
            version = f.read().strip()

        self.title(f"BUDB Upload to MySQL {version}")
        self.geometry("480x620")
        self.configure(fg_color="#273946")

        # Dots animation
        self.dots_running = False
        self.dots_count = 0
        self.wait_dots_running = False
        self.wait_popup_dots = 0

        # Database folder
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.database_folder = os.path.join(base_dir, "database")
        os.makedirs(self.database_folder, exist_ok=True)

        # Title label
        self.title_label = ctk.CTkLabel(
            self,
            text="BUDB Upload to MySQL",
            text_color="#fff6de",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        self.title_label.pack(pady=(20, 5))

        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color="#273946", corner_radius=0)
        btn_frame.pack(pady=5)

        self.open_db_btn = ctk.CTkButton(
            btn_frame,
            text="Open database folder",
            fg_color="#CB1F47",
            hover_color="#ffab4c",
            command=self.open_database_folder
        )
        self.open_db_btn.pack(side="left", padx=5)

        self.refresh_btn = ctk.CTkButton(
            btn_frame,
            text="Refresh",
            fg_color="#CB1F47",
            hover_color="#ffab4c",
            command=self.refresh_all
        )
        self.refresh_btn.pack(side="left", padx=5)

        # Listbox container
        self.list_container = ctk.CTkFrame(self, fg_color="#273946", corner_radius=0)
        self.list_container.pack(padx=20, pady=10, fill="x")

        self.file_text = tk.Text(
            self.list_container,
            height=8,
            bg="#fff6de",
            fg="#273946",
            font=("Segoe UI", 11),
            highlightthickness=0,
            relief="flat",
            wrap="none"
        )
        self.file_text.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)

        scrollbar = tk.Scrollbar(self.list_container, command=self.file_text.yview)
        scrollbar.pack(side="right", fill="y", padx=(0,5), pady=5)
        self.file_text.config(yscrollcommand=scrollbar.set)

        self.file_text.tag_configure("header", font=("Segoe UI", 11, "bold"))
        self.file_text.tag_configure("italic", font=("Segoe UI", 11, "italic"))

        # Instruction & message
        self.instruction_label = ctk.CTkLabel(
            self,
            text="",
            text_color="#BBB8A6",
            wraplength=550,
            justify="center",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.instruction_label.pack(pady=5)

        self.message_label = ctk.CTkLabel(
            self,
            text="Waiting to start...",
            text_color="#BBB8A6",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.message_label.pack(pady=5)

        # Progress details frame
        self.details_frame = ctk.CTkFrame(self, fg_color="#273946", corner_radius=0)
        self.details_frame.pack(padx=40, pady=(5, 0), fill="x")

        self.status_detail = ctk.CTkLabel(self.details_frame, text="Status: Waiting", text_color="#fff6de", anchor="w")
        self.status_detail.pack(fill="x")

        self.rows_detail = ctk.CTkLabel(self.details_frame, text="Processed: 0 / 0 rows", text_color="#fff6de", anchor="w")
        self.rows_detail.pack(fill="x")

        self.batch_detail = ctk.CTkLabel(self.details_frame, text="Batch Size: -", text_color="#fff6de", anchor="w")
        self.batch_detail.pack(fill="x")

        self.checkpoint_detail = ctk.CTkLabel(self.details_frame, text="Checkpoint: -", text_color="#fff6de", anchor="w")
        self.checkpoint_detail.pack(fill="x")

        self.elapsed_detail = ctk.CTkLabel(self.details_frame, text="Elapsed Time: 00:00:00", text_color="#fff6de", anchor="w")
        self.elapsed_detail.pack(fill="x")

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            self,
            width=300,
            fg_color="#444444",
            progress_color="#CB1F47"
        )
        self.progress.set(0)
        self.progress.pack(pady=10)

        # Run button
        self.run_btn = ctk.CTkButton(
            self,
            text="UPLOAD BUDB",
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#CB1F47",
            hover_color="#ffab4c",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.run_tool
        )
        self.run_btn.pack(pady=15)

        # Refresh file list
        self.refresh_all()


    # ---------------- Folder functions ----------------
    def open_database_folder(self):
        folder = self.database_folder
        if os.path.isdir(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        else:
            messagebox.showerror("Error", f"Database folder not found:\n{folder}")

    def open_folder(self, folder):
        if os.path.isdir(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        else:
            messagebox.showerror("Error", f"Folder not found:\n{folder}")

    def load_folder_files(self, folder, exts):
        if not os.path.isdir(folder):
            return []
        return sorted(
            f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(exts)
        )

    # ---------------- Refresh GUI ----------------
    def refresh_all(self):
        self.message_label.configure(text="Waiting to start...")
        self.progress.set(0)

        self.status_detail.configure(text="Status: Waiting")
        self.rows_detail.configure(text="Processed: 0 / 0 rows")
        self.batch_detail.configure(text="Batch Size: -")
        self.checkpoint_detail.configure(text="Checkpoint: -")
        self.elapsed_detail.configure(text="Elapsed Time: 00:00:00")

        self.dots_running = False
        if hasattr(self, "wait_popup"):
            self.close_wait_popup()

        self.file_text.configure(state="normal")
        self.file_text.delete("1.0", "end")

        # Load .db files
        self.db_files = self.load_folder_files(self.database_folder, (".db",))

        self.file_text.insert("end", "Bottoms-up Database File:\n", "header")
        if self.db_files:
            for f in self.db_files:
                self.file_text.insert("end", f + "\n")
        else:
            self.file_text.insert("end", "  No database file found\n", "italic")

        self.file_text.configure(state="disabled")
        self.check_files_ready()


    def check_files_ready(self):
        db_ok = bool(self.db_files)
        if db_ok:
            self.run_btn.configure(state="normal")
            self.instruction_label.configure(
                text="Ready! Click UPLOAD BUDB."
            )
        else:
            self.run_btn.configure(state="disabled")
            self.instruction_label.configure(
                text="No database file found. Add a .db file and click Refresh."
            )

    # ---------------- Logging & Progress ----------------
    def log_message(self, message):
        self.message_label.configure(text=message)
        self.update_idletasks()

    def update_progress(
        self,
        fraction,
        filename=None,
        processed_rows=0,
        total_rows=0,
        batch_size=None,
        checkpoint=None,
        elapsed_time=None
    ):
        self.progress.set(fraction)

        percent = int(fraction * 100)
        self.message_label.configure(text=f"{percent}% completed")

        self.status_detail.configure(text=f"Status: Uploading... {percent}%")
        self.rows_detail.configure(text=f"Processed: {processed_rows:,} / {total_rows:,} rows")
        self.batch_detail.configure(text=f"Batch Size: {batch_size:,} rows" if batch_size else "Batch Size: -")
        self.checkpoint_detail.configure(text=f"Checkpoint: ID > {checkpoint:,}" if checkpoint else "Checkpoint: -")
        self.elapsed_detail.configure(text=f"Elapsed Time: {elapsed_time}" if elapsed_time else "Elapsed Time: 00:00:00")

        if filename and getattr(self, "wait_label", None) and self.wait_label.winfo_exists():
            self.wait_popup_filename = filename
            dots = "." * self.wait_popup_dots
            short_name = os.path.basename(self.wait_popup_filename)
            self.wait_label.configure(text=f"Uploading{dots}\n{short_name}")

    # ---------------- Wait popup ----------------
    def show_wait_popup(self, filename=None):
        self.wait_popup = ctk.CTkToplevel(self)
        self.wait_popup.title("Please Wait")
        self.wait_popup.geometry("300x100")
        self.wait_popup.resizable(False, False)
        self.wait_popup.transient(self)
        self.wait_popup.grab_set()

        self.wait_popup_filename = filename
        short_name = os.path.basename(filename) if filename else ""
        display_text = f"Uploading\n{short_name}" if filename else "Uploading..."
        self.wait_label = ctk.CTkLabel(
            self.wait_popup,
            text=display_text,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            wraplength=250,
            justify="center"
        )
        self.wait_label.pack(expand=True, pady=20)

        self.wait_dots_running = True
        self.animate_wait_popup()

    def animate_wait_popup(self):
        if not getattr(self, "wait_dots_running", False):
            return
        if not getattr(self, "wait_label", None) or not self.wait_label.winfo_exists():
            return
        self.wait_popup_dots = (self.wait_popup_dots + 1) % 4
        dots = "." * self.wait_popup_dots
        current_text = self.wait_label.cget("text")
        if "\n" in current_text:
            parts = current_text.split("\n", 1)
            self.wait_label.configure(text=f"Uploading{dots}\n{parts[1]}")
        else:
            self.wait_label.configure(text=f"Uploading{dots}...")
        self.wait_label.after(500, self.animate_wait_popup)

    def close_wait_popup(self):
        if getattr(self, "wait_popup", None) is not None:
            try:
                if self.wait_popup.winfo_exists():
                    self.wait_popup.destroy()
            except Exception:
                pass
            finally:
                self.wait_popup = None

    # ---------------- Run Main ----------------
    def run_tool(self):
        if not self.db_files:
            messagebox.showerror("Error", "No database file found.")
            return
        self.instruction_label.configure(text="Please do not close the window")
        self.progress.set(0)
        self.run_btn.configure(state="disabled")
        threading.Thread(target=self.run_main_process, daemon=True).start()

    def run_main_process(self):
        try:
            if sys.stdout is None:
                sys.stdout = io.StringIO()
            if sys.stderr is None:
                sys.stderr = io.StringIO()

            truncate = messagebox.askyesno(
                "Truncate MySQL Table?",
                "MySQL table is not empty. Do you want to truncate before importing?"
            )

            db_file = self.db_files[0]
            self.show_wait_popup(filename=db_file)

            budb_upload_to_mysql(
                BOTTOMS_UP_FOLDER=self.database_folder,
                logger=self.log_message,
                progress_callback=self.update_progress,
                truncate=truncate
            )

            self.dots_running = False
            self.close_wait_popup()
            self.run_btn.configure(state="normal")
            self.update_message("Upload finished successfully!")
            self.progress.set(1.0)

        except Exception as e:
            self.dots_running = False
            self.wait_dots_running = False
            self.close_wait_popup()
            self.run_btn.configure(state="normal")
            self.update_message(f"Failed to upload BUDB.\n\n{e}")
            messagebox.showerror("Error", f"Upload failed:\n{e}")
        finally:
            self.instruction_label.configure(
                text="Ready! Click GENERATE RESULTS."
            )

    def update_message(self, text):
        self.message_label.after(0, lambda: self.message_label.configure(text=text))


if __name__ == "__main__":
    app = MinimalToolUI()
    app.mainloop()
