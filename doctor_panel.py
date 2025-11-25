# -*- coding: utf-8 -*-

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
from PIL import Image, ImageTk
import io
import os
matplotlib.use('TkAgg')
from datetime import datetime, timedelta
from db_manager import DatabaseManager
import sys

class DoctorPanel(ctk.CTkToplevel):
    def __init__(self, parent, doctor_tc):
        try:
            print("DoctorPanel başlatılıyor...")  # Debug log
            super().__init__(parent)
            self.parent = parent
            self.doctor_tc = doctor_tc

            # Pencere ayarları
            self.title("Doktor Paneli")
            self.geometry("1200x800")
            self.state('zoomed')

            # Pencereyi merkeze konumlandır
            self.update_idletasks()
            width = 1200
            height = 800
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f'{width}x{height}+{x}+{y}')

            print("Pencere ayarları tamamlandı")  # Debug log

            # Pencere kapatma protokolü
            self.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Ana grid yapılandırması
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=1)

            # Sol sidebar
            self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.sidebar.grid_rowconfigure(4, weight=1)

            print("Sidebar oluşturuldu")  # Debug log

            # Sidebar başlık
            self.logo_label = ctk.CTkLabel(
                self.sidebar, text="Doktor Paneli",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

            # Sidebar butonları
            self.dash_button = ctk.CTkButton(
                self.sidebar, text="Dashboard",
                command=self.show_dashboard
            )
            self.dash_button.grid(row=1, column=0, padx=20, pady=10)

            self.patients_button = ctk.CTkButton(
                self.sidebar, text="Hasta Listesi",
                command=self.show_patients
            )
            self.patients_button.grid(row=2, column=0, padx=20, pady=10)

            self.reports_button = ctk.CTkButton(
                self.sidebar, text="Raporlar",
                command=self.show_reports
            )
            self.reports_button.grid(row=3, column=0, padx=20, pady=10)

            print("Butonlar oluşturuldu")  # Debug log

            # Tema değiştirme
            self.appearance_mode_menu = ctk.CTkOptionMenu(
                self.sidebar,
                values=["Light", "Dark", "System"],
                command=self.change_appearance_mode
            )
            self.appearance_mode_menu.grid(row=5, column=0, padx=20, pady=(10, 20))

            # Ana içerik alanı
            self.main_frame = ctk.CTkFrame(self, corner_radius=0)
            self.main_frame.grid(row=0, column=1, sticky="nsew")
            self.main_frame.grid_rowconfigure(0, weight=1)
            self.main_frame.grid_columnconfigure(0, weight=1)

            print("Ana frame oluşturuldu")  # Debug log

            # Veritabanı bağlantısı
            self.db = DatabaseManager.get_instance()
            
            # Profil resmi için değişkenler
            self.profile_image = None
            self.profile_photo = None
            
            # Kullanıcı bilgilerini yükle
            self.load_user_info()

            print("Kullanıcı bilgileri yüklendi")  # Debug log

            # Varsayılan olarak dashboard'u göster
            self.show_dashboard()

            print("Dashboard gösterildi")  # Debug log

            # Pencereyi ön plana getir
            self.lift()
            self.focus_force()

        except Exception as e:
            print(f"DoctorPanel başlatılırken hata: {str(e)}")  # Debug log
            if hasattr(self, 'show_message'):
                self.show_message(f"Panel başlatılırken hata oluştu: {str(e)}", "error")
            else:
                messagebox.showerror("Hata", f"Panel başlatılırken hata oluştu: {str(e)}")
            raise

    def change_appearance_mode(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_frame()

        # İstatistik kartları için frame
        stats_frame = ctk.CTkFrame(self.main_frame)
        stats_frame.pack(fill="x", padx=20, pady=20)
        stats_frame.grid_columnconfigure((0,1,2), weight=1)

        try:
            # Toplam hasta sayısı
            total_patients = self.db.get_doctor_patients_count(self.doctor_id)
            self.create_stat_card(
                stats_frame, "Toplam Hasta",
                str(total_patients),
                0, 0
            )

            # Günlük ölçüm sayısı
            daily_measurements = self.db.get_daily_measurements_count(self.doctor_id)
            self.create_stat_card(
                stats_frame, "Günlük Ölçüm",
                str(daily_measurements),
                0, 1
            )

            # Kritik hasta sayısı
            critical_patients = self.db.get_critical_patients_count(self.doctor_id)
            self.create_stat_card(
                stats_frame, "Kritik Hastalar",
                str(critical_patients),
                0, 2,
                text_color="red" if critical_patients > 0 else None
            )

            # Haftalık ortalama grafiği
            weekly_data = self.db.get_doctor_patients_weekly_averages(self.doctor_id)
            if weekly_data:
                graph_frame = ctk.CTkFrame(self.main_frame)
                graph_frame.pack(fill="both", expand=True, padx=20, pady=10)

                dates = [row[0] for row in weekly_data]
                averages = [float(row[1]) for row in weekly_data]

                fig = Figure(figsize=(10, 4))
                ax = fig.add_subplot(111)
                ax.plot(dates, averages, 'b-', marker='o')
                ax.set_title('Haftalık Ortalama Şeker Seviyeleri')
                ax.set_xlabel('Tarih')
                ax.set_ylabel('Şeker Seviyesi (mg/dL)')
                
                # Referans çizgileri
                ax.axhline(y=70, color='r', linestyle='--', alpha=0.5)
                ax.axhline(y=180, color='r', linestyle='--', alpha=0.5)
                
                # Tarihleri döndür
                plt.xticks(rotation=45)
                
                canvas = FigureCanvasTkAgg(fig, master=graph_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

            # Son ölçümler tablosu
            measurements_frame = ctk.CTkFrame(self.main_frame)
            measurements_frame.pack(fill="both", expand=True, padx=20, pady=10)

            ctk.CTkLabel(
                measurements_frame,
                text="Son Ölçümler",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=10)

            # Tablo
            columns = ('TC', 'Ad Soyad', 'Son Ölçüm', 'Değer', 'Durum')
            tree = ttk.Treeview(measurements_frame, columns=columns, show='headings')

            # Sütun başlıkları
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)

            # Verileri ekle
            recent_measurements = self.db.get_doctor_recent_measurements(self.doctor_id)
            for measurement in recent_measurements:
                tc, name, time, value, status = measurement
                tree.insert('', 'end', values=(
                    tc,
                    name,
                    time.strftime('%Y-%m-%d %H:%M'),
                    f"{value} mg/dL",
                    status
                ))

            tree.pack(fill='both', expand=True, padx=10, pady=10)

        except Exception as e:
            self.show_message(f"Dashboard yüklenirken hata: {str(e)}", "error")

    def show_patients(self):
        self.clear_main_frame()

        # Hasta listesi frame
        patients_frame = ctk.CTkFrame(self.main_frame)
        patients_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Başlık
        ctk.CTkLabel(
            patients_frame,
            text="Hasta Listesi",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)

        # Tablo
        columns = ('TC', 'Ad', 'Soyad', 'Doğum Tarihi', 'Cinsiyet', 'E-posta', 'Telefon', 'Başlangıç')
        tree = ttk.Treeview(patients_frame, columns=columns, show='headings')

        # Sütun başlıkları
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Verileri ekle
        patients = self.db.get_doctor_patients_list(self.doctor_id)
        for patient in patients:
            tree.insert('', 'end', values=(
                patient[0],  # TC
                patient[1],  # Ad
                patient[2],  # Soyad
                patient[3].strftime('%Y-%m-%d'),  # Doğum tarihi
                patient[4],  # Cinsiyet
                patient[5],  # E-posta
                patient[6],  # Telefon
                patient[7].strftime('%Y-%m-%d')  # Başlangıç tarihi
            ))

        tree.pack(fill='both', expand=True, padx=10, pady=10)

    def show_reports(self):
        self.clear_main_frame()
        # Raporlar özelliği daha sonra eklenecek
        ctk.CTkLabel(
            self.main_frame,
            text="Raporlar özelliği yakında eklenecek...",
            font=ctk.CTkFont(size=20)
        ).pack(pady=20)

    def create_stat_card(self, parent, title, value, row, col, text_color=None):
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=14)
        ).pack(pady=(10,0))
        
        value_label = ctk.CTkLabel(
            card, text=value,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        if text_color:
            value_label.configure(text_color=text_color)
        value_label.pack(pady=(0,10))

    def show_message(self, message, message_type="info"):
        """Kullanıcıya mesaj göster"""
        if message_type == "error":
            messagebox.showerror("Hata", message)
        elif message_type == "success":
            messagebox.showinfo("Başarılı", message)
        else:
            messagebox.showinfo("Bilgi", message)

    def on_closing(self):
        """Pencere kapatıldığında çağrılır"""
        try:
            print("Doktor paneli kapatılıyor...")  # Debug log
            
            # Veritabanı bağlantılarını temizle
            if hasattr(self, 'db'):
                self.db.close_all()
            
            # Pencereyi kapat
            self.destroy()
            
            # Ana pencereyi de kapat
            if self.parent:
                self.parent.destroy()
            
            print("Uygulama başarıyla kapatıldı")  # Debug log
            sys.exit(0)
        except Exception as e:
            print(f"Kapatma sırasında hata: {str(e)}")  # Debug log
            sys.exit(1)

    def load_user_info(self):
        """Kullanıcı bilgilerini ve profil resmini yükle"""
        try:
            user = self.db.get_user_by_tc(self.doctor_tc)
            if not user:
                self.show_message("Doktor bilgisi bulunamadı!", "error")
                self.destroy()
                return
                
            self.doctor_id = user[0]
            
            # Profil resmini yükle
            image_data, image_type = self.db.get_profile_image(self.doctor_id)
            if image_data:
                self.load_profile_image(image_data)
                
            # Sidebar'a profil resmi ekle
            self.add_profile_to_sidebar()

        except Exception as e:
            self.show_message(f"Kullanıcı bilgileri yüklenirken hata: {str(e)}", "error")

    def add_profile_to_sidebar(self):
        """Sidebar'a profil resmi ve düzenleme butonları ekle"""
        profile_frame = ctk.CTkFrame(self.sidebar)
        profile_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        # Profil resmi
        if self.profile_photo:
            profile_label = ctk.CTkLabel(
                profile_frame,
                image=self.profile_photo,
                text=""
            )
        else:
            profile_label = ctk.CTkLabel(
                profile_frame,
                text="Profil\nResmi\nYok",
                width=100,
                height=100
            )
        profile_label.pack(pady=10)

        # Profil resmi düzenleme butonları
        buttons_frame = ctk.CTkFrame(profile_frame)
        buttons_frame.pack(fill="x", pady=5)

        ctk.CTkButton(
            buttons_frame,
            text="Resim Seç",
            command=self.select_profile_image,
            width=70
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            buttons_frame,
            text="Sil",
            command=self.delete_profile_image,
            width=70,
            fg_color="red",
            hover_color="darkred"
        ).pack(side="right", padx=2)

        # Logo label'ı yeni konumuna taşı
        self.logo_label.grid(row=1, column=0, padx=20, pady=(20, 10))
        
        # Diğer butonların grid pozisyonlarını güncelle
        self.dash_button.grid(row=2, column=0, padx=20, pady=10)
        self.patients_button.grid(row=3, column=0, padx=20, pady=10)
        self.reports_button.grid(row=4, column=0, padx=20, pady=10)
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=(10, 20))

    def select_profile_image(self):
        """Profil resmi seçme dialog'unu göster"""
        file_types = [
            ('PNG files', '*.png'),
            ('JPEG files', '*.jpg;*.jpeg'),
            ('All files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Profil Resmi Seç",
            filetypes=file_types
        )
        
        if filename:
            try:
                # Resmi yükle ve boyutlandır
                with Image.open(filename) as img:
                    # En boy oranını koru ve 200x200 boyutuna getir
                    img.thumbnail((200, 200))
                    
                    # Resmi byte dizisine dönüştür
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format=img.format)
                    img_byte_arr = img_byte_arr.getvalue()

                    # Veritabanına kaydet
                    self.db.save_profile_image(
                        self.doctor_id,
                        img_byte_arr,
                        os.path.splitext(filename)[1][1:].lower()
                    )

                    # Arayüzü güncelle
                    self.load_profile_image(img_byte_arr)
                    self.add_profile_to_sidebar()
                    
                    self.show_message("Profil resmi güncellendi!", "success")

            except Exception as e:
                self.show_message(f"Resim yüklenirken hata: {str(e)}", "error")

    def load_profile_image(self, image_data):
        """Profil resmini yükle ve görüntüle"""
        try:
            # Byte dizisinden PIL Image oluştur
            image = Image.open(io.BytesIO(image_data))
            
            # CustomTkinter için PhotoImage oluştur
            self.profile_photo = ImageTk.PhotoImage(image)
            
        except Exception as e:
            self.show_message(f"Profil resmi yüklenirken hata: {str(e)}", "error")
            self.profile_photo = None

    def delete_profile_image(self):
        """Profil resmini sil"""
        try:
            self.db.delete_profile_image(self.doctor_id)
            
            self.profile_photo = None
            self.add_profile_to_sidebar()
            
            self.show_message("Profil resmi silindi!", "success")
            
        except Exception as e:
            self.show_message(f"Profil resmi silinirken hata: {str(e)}", "error")

if __name__ == "__main__":
    app = ctk.CTk()
    doctor_panel = DoctorPanel(app, "12345678901")  # Test TC
    app.mainloop()