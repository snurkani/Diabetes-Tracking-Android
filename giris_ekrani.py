import customtkinter as ctk
from tkinter import messagebox
from db_manager import DatabaseManager
from doctor_panel import DoctorPanel
from patient_panel import PatientPanel
import sys
import re

# Tema ayarları
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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

        # Pencere kapatma protokolü
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        self.tc_entry.bind('<KeyRelease>', self.validate_tc)

        # Şifre
        self.password_label = ctk.CTkLabel(self.main_frame, text="Şifre:")
        self.password_label.pack(pady=(20,5))
        
        self.password_entry = ctk.CTkEntry(self.main_frame, show="*", width=200)
        self.password_entry.pack()

        # Giriş butonu
        self.login_button = ctk.CTkButton(
            self.main_frame,
            text="Giriş Yap",
            command=self.login,
            state="disabled"  # Başlangıçta devre dışı
        )
        self.login_button.pack(pady=30)

        # Tema seçimi
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.main_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_mode_menu.pack(pady=20)

        # Test kullanıcı bilgileri (geliştirme aşamasında)
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text="Test Hesapları:\nDoktor: 12345678901 / 123456\nHasta: 98765432109 / 123456",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.info_label.pack(pady=20)

        # Veritabanı bağlantısı
        try:
            self.db = DatabaseManager.get_instance()
        except Exception as e:
            self.show_message(f"Veritabanı bağlantısı kurulamadı: {str(e)}", "error")
            self.after(2000, self.destroy)

    def validate_tc(self, event=None):
        """TC Kimlik numarasını doğrula"""
        tc = self.tc_entry.get().strip()
        
        # Sadece rakam girişine izin ver
        if not tc.isdigit():
            self.tc_entry.delete(0, 'end')
            self.tc_entry.insert(0, re.sub(r'[^0-9]', '', tc))
            tc = self.tc_entry.get().strip()
        
        # 11 haneli olmalı
        is_valid = len(tc) == 11
        
        # Giriş butonunu aktif/pasif yap
        self.login_button.configure(state="normal" if is_valid else "disabled")
        
        return is_valid

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

        # TC Kimlik doğrulama
        if not self.validate_tc():
            self.show_message("Geçersiz TC Kimlik No!", "error")
            return

        try:
            # Kullanıcıyı sorgula
            user = self.db.get_user_by_tc(tc)
            
            if not user:
                self.show_message("Kullanıcı bulunamadı!", "error")
                return

            user_id, _, _, _, stored_password, user_type = user[0:6]

            # Şifre kontrolü
            if password != stored_password:  # Gerçek uygulamada hash kontrolü yapılmalı
                self.show_message("Hatalı şifre!", "error")
                return

            try:
                # Kullanıcı tipine göre panel aç
                if user_type == "doctor":
                    doctor_panel = DoctorPanel(self, user_id)
                    doctor_panel.focus_force()
                else:
                    patient_panel = PatientPanel(self, user_id)
                    patient_panel.focus_force()

                # Ana pencereyi gizle
                self.withdraw()

            except Exception as e:
                self.show_message(f"Panel açılırken hata oluştu: {str(e)}", "error")
                raise

        except Exception as e:
            self.show_message(f"Giriş yapılırken hata oluştu: {str(e)}", "error")

    def on_closing(self):
        """Pencere kapatıldığında çağrılır"""
        try:
            # Veritabanı bağlantılarını temizle
            if hasattr(self, 'db'):
                self.db.close_all()
            
            # Pencereyi kapat
            self.quit()
            self.destroy()
            sys.exit(0)
        except Exception as e:
            print(f"Kapatma sırasında hata: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        app = LoginWindow()
        app.mainloop()
    except Exception as e:
        print(f"Uygulama başlatılırken hata: {str(e)}")
        messagebox.showerror("Kritik Hata", f"Uygulama başlatılamadı: {str(e)}")
        sys.exit(1)