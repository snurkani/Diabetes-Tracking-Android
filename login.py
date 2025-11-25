# -*- coding: utf-8 -*-

import customtkinter as ctk
from tkinter import messagebox
from db_manager import DatabaseManager
from doctor_panel import DoctorPanel
from patient_panel import PatientPanel

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere ayarları
        self.title("Diyabet Takip Sistemi - Giriş")
        self.geometry("400x500")
        
        # Pencereyi merkeze konumlandır
        self.update_idletasks()
        width = 400
        height = 500
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Ana frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Başlık
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Diyabet Takip Sistemi",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)

        # TC Kimlik
        self.tc_label = ctk.CTkLabel(self.main_frame, text="TC Kimlik No:")
        self.tc_label.pack(pady=(20,5))
        
        self.tc_entry = ctk.CTkEntry(self.main_frame, width=200)
        self.tc_entry.pack()

        # Şifre
        self.password_label = ctk.CTkLabel(self.main_frame, text="Şifre:")
        self.password_label.pack(pady=(20,5))
        
        self.password_entry = ctk.CTkEntry(self.main_frame, show="*", width=200)
        self.password_entry.pack()

        # Giriş butonu
        self.login_button = ctk.CTkButton(
            self.main_frame,
            text="Giriş Yap",
            command=self.login
        )
        self.login_button.pack(pady=30)

        # Tema seçimi
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.main_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_mode_menu.pack(pady=20)

        # Veritabanı bağlantısı
        self.db = DatabaseManager.get_instance()

    def change_appearance_mode(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def show_message(self, message, message_type="info"):
        """Kullanıcıya mesaj göster"""
        if message_type == "error":
            messagebox.showerror("Hata", message)
        elif message_type == "success":
            messagebox.showinfo("Başarılı", message)
        else:
            messagebox.showinfo("Bilgi", message)

    def login(self):
        """Giriş işlemini gerçekleştir"""
        tc = self.tc_entry.get().strip()
        password = self.password_entry.get().strip()

        # Boş alan kontrolü
        if not tc or not password:
            self.show_message("TC Kimlik No ve şifre zorunludur!", "error")
            return

        try:
            # Kullanıcıyı sorgula
            query = """
                SELECT user_id, user_type, password 
                FROM users 
                WHERE tc = %s
            """
            result = self.db.execute_query(query, (tc,))

            if not result:
                self.show_message("Kullanıcı bulunamadı!", "error")
                return

            user_id, user_type, stored_password = result[0]

            # Şifre kontrolü
            if password != stored_password:  # Gerçek uygulamada hash kontrolü yapılmalı
                self.show_message("Hatalı şifre!", "error")
                return

            # Giriş başarılı
            self.withdraw()  # Ana pencereyi gizle

            # Kullanıcı tipine göre panel aç
            if user_type == "doctor":
                doctor_panel = DoctorPanel(self, tc)
                doctor_panel.focus()  # Pencereyi aktif yap
            else:
                patient_panel = PatientPanel(self, tc)
                patient_panel.focus()  # Pencereyi aktif yap

        except Exception as e:
            self.show_message(f"Giriş yapılırken hata oluştu: {str(e)}", "error")

if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop() 