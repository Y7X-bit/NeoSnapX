import cv2
import os
import datetime
import threading
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

class HoverButton(ctk.CTkButton):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_fg = self.cget("fg_color")
        self.default_border = self.cget("border_width")
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event=None):
        self.configure(fg_color="#1a0000", border_color="red", border_width=2)

    def on_leave(self, event=None):
        self.configure(fg_color=self.default_fg, border_width=self.default_border)

class SelfieApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NeoSnapX")
        self.geometry("880x750")
        self.resizable(False, False)
        self.configure(fg_color="#000000")

        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.save_path = os.path.join(os.getcwd(), "selfies")
        os.makedirs(self.save_path, exist_ok=True)
        self.countdown_seconds = 3

        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="#000000", border_color="red", border_width=2)
        self.main_frame.place(relx=0.5, rely=0.48, anchor="center")

        self.title_label = ctk.CTkLabel(self.main_frame, text="📸 NeoSnapX", text_color="red", font=("Arial Rounded MT Bold", 24))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(25, 10))

        self.video_frame = ctk.CTkFrame(self.main_frame, width=720, height=400, fg_color="black", corner_radius=12, border_color="red", border_width=2)
        self.video_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=20)

        self.video_label = ctk.CTkLabel(self.video_frame, text="", width=712, height=392, fg_color="black")
        self.video_label.place(relx=0.5, rely=0.5, anchor="center")

        self.path_label = ctk.CTkLabel(self.main_frame, text=f"📁 Saving to: {self.save_path}", font=("Arial", 11), text_color="white")
        self.path_label.grid(row=2, column=0, columnspan=2, pady=(5, 10))

        self.dropdown_frame = ctk.CTkFrame(self.main_frame, fg_color="#000000", corner_radius=12, border_color="red", border_width=2)
        self.dropdown_frame.grid(row=3, column=0, padx=15, pady=8, sticky="e")

        self.filter_mode = ctk.StringVar(value="None")
        self.filter_dropdown = ctk.CTkOptionMenu(self.dropdown_frame, values=["None", "Gray", "Sketch"], variable=self.filter_mode, width=150, text_color="red", fg_color="#000000", button_color="#000000", font=("Arial", 13), corner_radius=12)
        self.filter_dropdown.pack(padx=3, pady=3)

        self.folder_btn = HoverButton(self.main_frame, text="📂 Choose Folder", command=self.choose_folder, fg_color="#000000", text_color="red", corner_radius=20, height=42, width=180, font=("Arial Rounded MT Bold", 13), border_color="red", border_width=1)
        self.folder_btn.grid(row=3, column=1, padx=15, pady=8, sticky="w")

        self.capture_btn = HoverButton(self.main_frame, text="📸 Capture Selfie", command=self.capture_selfie, fg_color="#000000", text_color="red", height=50, corner_radius=25, width=320, font=("Arial Rounded MT Bold", 16), border_color="red", border_width=2)
        self.capture_btn.grid(row=4, column=0, columnspan=2, padx=40, pady=(20, 20), sticky="ew")

        self.footer = ctk.CTkLabel(self, text="🔎 Powered by Y7X 💗", font=("Arial", 14), text_color="red")
        self.footer.place(relx=0.5, rely=0.975, anchor="center")

        self.video_thread = threading.Thread(target=self.update_video)
        self.video_thread.daemon = True
        self.video_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path = folder
            self.path_label.configure(text=f"📁 Saving to: {self.save_path}")

    def apply_filter(self, frame):
        mode = self.filter_mode.get().lower()
        if mode == "gray":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif mode == "sketch":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            inv = 255 - gray
            blur = cv2.medianBlur(inv, 5)
            sketch = cv2.divide(gray, 255 - blur, scale=256.0)
            return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        return frame

    def update_video(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            frame = self.apply_filter(frame)

            frame_height, frame_width = frame.shape[:2]
            target_aspect_ratio = 720 / 400
            current_aspect_ratio = frame_width / frame_height

            if current_aspect_ratio > target_aspect_ratio:
                new_width = int(frame_height * target_aspect_ratio)
                x_start = (frame_width - new_width) // 2
                frame = frame[:, x_start:x_start + new_width]
            elif current_aspect_ratio < target_aspect_ratio:
                new_height = int(frame_width / target_aspect_ratio)
                y_start = (frame_height - new_height) // 2
                frame = frame[y_start:y_start + new_height]

            frame_resized = cv2.resize(frame, (720, 400), interpolation=cv2.INTER_AREA)
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)

            self.video_label.configure(image=img_tk)
            self.video_label.image = img_tk

    def capture_selfie(self):
        def countdown_and_capture():
            for i in reversed(range(1, self.countdown_seconds + 1)):
                logging.info(f"📢 Capturing in {i}s...")
                time.sleep(1)

            ret, frame = self.cap.read()
            if not ret:
                logging.error("❌ Failed to capture frame.")
                return

            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

            if len(faces) == 0:
                logging.warning("😕 No face detected. Selfie not saved.")
                return

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

            cv2.putText(frame, "📸 NeoSnapX by Y7X", (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"selfie_{len(faces)}face_{timestamp}.jpg"
            filepath = os.path.join(self.save_path, filename)
            cv2.imwrite(filepath, frame)
            logging.info(f"✅ Selfie saved: {filepath}")

        threading.Thread(target=countdown_and_capture, daemon=True).start()

    def on_close(self):
        self.running = False
        self.cap.release()
        self.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = SelfieApp()
    app.mainloop()