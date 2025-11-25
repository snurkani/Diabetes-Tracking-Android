# -*- coding: utf-8 -*-

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import io
import os
import psycopg2
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
import sys
from db_manager import DatabaseManager
matplotlib.use('TkAgg')

class PatientPanel(ctk.CTkToplevel):
    def __init__(self, parent, tc):
        try:
            print("PatientPanel başlatılıyor...")  # Debug log
            super().__init__(parent)
            self.parent = parent
            self.tc = tc

            # Pencere ayarları
            self.title("Hasta Paneli")
            self.geometry("1200x800")
            self.state('zoomed')

            # Pencereyi merkeze konumlandır
            self.update_idletasks()
            width = 1200
            height = 800
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f'{width}x{height}+{x}+{y}')

            # Pencere kapatma protokolü
            self.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Ana grid yapılandırması
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=1)

            # Sol sidebar
            self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.sidebar.grid_rowconfigure(5, weight=1)

            # Sidebar başlık
            self.logo_label = ctk.CTkLabel(
                self.sidebar, text="Hasta Paneli",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

            # Sidebar butonları
            self.dash_button = ctk.CTkButton(
                self.sidebar, text="Ana Sayfa",
                command=self.show_dashboard
            )
            self.dash_button.grid(row=1, column=0, padx=20, pady=10)

            self.measurement_button = ctk.CTkButton(
                self.sidebar, text="Ölçüm Gir",
                command=self.show_measurement
            )
            self.measurement_button.grid(row=2, column=0, padx=20, pady=10)

            self.diet_button = ctk.CTkButton(
                self.sidebar, text="Diyet Takip",
                command=self.show_diet
            )
            self.diet_button.grid(row=3, column=0, padx=20, pady=10)

            self.exercise_button = ctk.CTkButton(
                self.sidebar, text="Egzersiz Takip",
                command=self.show_exercise
            )
            self.exercise_button.grid(row=4, column=0, padx=20, pady=10)

            # Tema değiştirme
            self.appearance_mode_menu = ctk.CTkOptionMenu(
                self.sidebar,
                values=["Light", "Dark", "System"],
                command=self.change_appearance_mode
            )
            self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=(10, 20))

            # Ana içerik alanı
            self.main_frame = ctk.CTkFrame(self, corner_radius=0)
            self.main_frame.grid(row=0, column=1, sticky="nsew")
            self.main_frame.grid_rowconfigure(0, weight=1)
            self.main_frame.grid_columnconfigure(0, weight=1)

            # Dashboard frame'i oluştur
            self.dashboard_frame = ctk.CTkFrame(self.main_frame)
            self.dashboard_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

            # Profil resmi için değişkenler
            self.profile_image = None
            self.profile_photo = None
            
            # Kullanıcı bilgilerini yükle
            self.load_user_info()

            # Varsayılan olarak dashboard'u göster
            self.show_dashboard()

            print("Panel başarıyla başlatıldı")  # Debug log

        except Exception as e:
            print(f"Panel başlatılırken hata: {str(e)}")  # Debug log
            self.show_message(f"Panel başlatılırken hata oluştu: {str(e)}", "error")
            raise

    def change_appearance_mode(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        try:
            # Veritabanı bağlantısı
            db = DatabaseManager.get_instance()

            # Kullanıcı ID'sini al
            user = db.get_user_by_tc(self.tc)
            if not user:
                self.show_message("Kullanıcı bulunamadı!", "error")
                return

            user_id = user[0]  # user_id ilk sırada

            # Son 7 günlük ölçümler
            measurements = db.get_patient_measurements(
                user_id, 
                start_date=datetime.now() - timedelta(days=7)
            )

            # Son diyet ve egzersiz kayıtları
            diet_records = db.get_patient_diet_tracking(
                user_id,
                start_date=datetime.now() - timedelta(days=7)
            )
            exercise_records = db.get_patient_exercise_tracking(
                user_id,
                start_date=datetime.now() - timedelta(days=7)
            )

            # Okunmamış uyarılar
            alerts = db.get_patient_alerts(user_id, unread_only=True)

            # İnsülin kayıtları
            insulin_records = db.get_patient_insulin_history(
                user_id,
                start_date=datetime.now() - timedelta(days=7)
            )

            # Dashboard frame'i temizle
            for widget in self.dashboard_frame.winfo_children():
                widget.destroy()

            # İstatistikleri göster
            stats_frame = ctk.CTkFrame(self.dashboard_frame)
            stats_frame.pack(fill="x", padx=10, pady=5)

            if measurements:
                levels = [m[0] for m in measurements]
                avg_level = sum(levels) / len(levels)
                min_level = min(levels)
                max_level = max(levels)

                ctk.CTkLabel(stats_frame, text=f"Son 7 Gün İstatistikleri:").pack()
                ctk.CTkLabel(stats_frame, text=f"Ortalama: {avg_level:.1f} mg/dL").pack()
                ctk.CTkLabel(stats_frame, text=f"En Düşük: {min_level:.1f} mg/dL").pack()
                ctk.CTkLabel(stats_frame, text=f"En Yüksek: {max_level:.1f} mg/dL").pack()

                # Grafik
                fig = Figure(figsize=(6, 4))
                ax = fig.add_subplot(111)
                
                dates = [m[1] for m in measurements]
                ax.plot(dates, levels, 'b-')
                ax.set_title('Şeker Seviyesi Grafiği')
                ax.set_xlabel('Tarih')
                ax.set_ylabel('mg/dL')
                
                # Referans aralıkları
                ax.axhline(y=70, color='r', linestyle='--', alpha=0.5)
                ax.axhline(y=180, color='r', linestyle='--', alpha=0.5)
                
                canvas = FigureCanvasTkAgg(fig, master=self.dashboard_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

            # Diyet ve egzersiz özeti
            summary_frame = ctk.CTkFrame(self.dashboard_frame)
            summary_frame.pack(fill="x", padx=10, pady=5)

            if diet_records:
                diet_text = "Son Diyet Kayıtları:\n"
                for date, name, status in diet_records[:3]:  # Son 3 kayıt
                    diet_text += f"{date}: {name} ({status})\n"
                ctk.CTkLabel(summary_frame, text=diet_text).pack()

            if exercise_records:
                exercise_text = "\nSon Egzersiz Kayıtları:\n"
                for date, name, duration, status in exercise_records[:3]:  # Son 3 kayıt
                    exercise_text += f"{date}: {name} - {duration} dk ({status})\n"
                ctk.CTkLabel(summary_frame, text=exercise_text).pack()

            # İnsülin kayıtları
            if insulin_records:
                insulin_frame = ctk.CTkFrame(self.dashboard_frame)
                insulin_frame.pack(fill="x", padx=10, pady=5)
                
                ctk.CTkLabel(
                    insulin_frame,
                    text="Son İnsülin Kayıtları:",
                    font=ctk.CTkFont(size=14, weight="bold")
                ).pack(pady=5)

                for record in insulin_records[:5]:  # Son 5 kayıt
                    given_time, insulin_type, units, sugar_level, notes = record
                    record_text = (
                        f"{given_time.strftime('%Y-%m-%d %H:%M')} - "
                        f"{insulin_type}: {units} ünite"
                    )
                    if sugar_level:
                        record_text += f" (Şeker: {sugar_level} mg/dL)"
                    if notes:
                        record_text += f"\nNot: {notes}"
                    
                    ctk.CTkLabel(
                        insulin_frame,
                        text=record_text,
                        font=ctk.CTkFont(size=12)
                    ).pack(pady=2)

            # Uyarılar
            if alerts:
                alerts_frame = ctk.CTkFrame(self.dashboard_frame)
                alerts_frame.pack(fill="x", padx=10, pady=5)
                
                ctk.CTkLabel(alerts_frame, text="Okunmamış Uyarılar:").pack()
                for alert_type, message, created_at, _ in alerts:
                    alert_text = f"{created_at.strftime('%Y-%m-%d %H:%M')}: {message}"
                    ctk.CTkLabel(alerts_frame, text=alert_text).pack()

        except Exception as e:
            self.show_message(f"Dashboard güncellenirken hata: {str(e)}", "error")

    def create_info_card(self, parent, title, value, row, col):
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=14)
        ).grid(row=0, column=0, padx=10, pady=(10,0))
        
        ctk.CTkLabel(
            card, text=value,
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=1, column=0, padx=10, pady=(0,10))

    def create_sugar_graph(self, parent):
        graph_frame = ctk.CTkFrame(parent)
        graph_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        fig, ax = plt.subplots(figsize=(10, 4))
        dates = [datetime.now() - timedelta(days=x) for x in range(7)]
        values = [120, 140, 110, 130, 150, 125, 135]
        
        ax.plot(dates, values)
        ax.set_title('7 Günlük Şeker Seviyesi Takibi')
        ax.set_xlabel('Tarih')
        ax.set_ylabel('Şeker Seviyesi (mg/dL)')
        
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_doctor_messages(self, parent):
        messages_frame = ctk.CTkFrame(parent)
        messages_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            messages_frame, text="Doktor Mesajları",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        messages = [
            "Akşam ölçümlerinizi düzenli yapın.",
            "Egzersiz programınıza devam edin.",
            "Diyet planınıza uyduğunuz için tebrikler!"
        ]
        
        for msg in messages:
            msg_label = ctk.CTkLabel(
                messages_frame, text=msg,
                font=ctk.CTkFont(size=12)
            )
            msg_label.pack(pady=5)

    def show_measurement(self):
        self.clear_main_frame()
        
        measurement_frame = ctk.CTkFrame(self.main_frame)
        measurement_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Başlık
        ctk.CTkLabel(
            measurement_frame, text="Yeni Ölçüm Girişi",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        # Ölçüm formu
        form_frame = ctk.CTkFrame(measurement_frame)
        form_frame.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            form_frame, text="Şeker Seviyesi (mg/dL):"
        ).pack(pady=(10,0))
        
        sugar_entry = ctk.CTkEntry(form_frame)
        sugar_entry.pack(pady=10)
        
        ctk.CTkButton(
            form_frame, text="Kaydet",
            command=lambda: self.save_measurement(sugar_entry.get())
        ).pack(pady=10)

    def show_diet(self):
        self.clear_main_frame()
        
        diet_frame = ctk.CTkFrame(self.main_frame)
        diet_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(
            diet_frame, text="Diyet Takibi",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        # Diyet seçenekleri
        options = ["Az Şekerli Diyet", "Şekersiz Diyet", "Dengeli Beslenme"]
        diet_var = ctk.StringVar(value=options[0])
        
        for option in options:
            ctk.CTkRadioButton(
                diet_frame, text=option,
                variable=diet_var, value=option
            ).pack(pady=10)
        
        ctk.CTkButton(
            diet_frame, text="Kaydet",
            command=lambda: self.save_diet(diet_var.get())
        ).pack(pady=20)

    def show_exercise(self):
        self.clear_main_frame()
        
        exercise_frame = ctk.CTkFrame(self.main_frame)
        exercise_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(
            exercise_frame, text="Egzersiz Takibi",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        # Egzersiz seçenekleri
        options = ["Yürüyüş", "Koşu", "Yüzme", "Bisiklet"]
        exercise_var = ctk.StringVar(value=options[0])
        
        for option in options:
            ctk.CTkRadioButton(
                exercise_frame, text=option,
                variable=exercise_var, value=option
            ).pack(pady=10)
        
        duration_frame = ctk.CTkFrame(exercise_frame)
        duration_frame.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            duration_frame, text="Süre (dakika):"
        ).pack(side='left', padx=10)
        
        duration_entry = ctk.CTkEntry(duration_frame)
        duration_entry.pack(side='left', padx=10)
        
        ctk.CTkButton(
            exercise_frame, text="Kaydet",
            command=lambda: self.save_exercise(exercise_var.get(), duration_entry.get())
        ).pack(pady=20)

    def save_measurement(self, value):
        try:
            # Değer kontrolü
            if not value:
                self.show_message("Lütfen bir değer girin!", "error")
                return

            value = float(value)
            
            # Negatif değer kontrolü
            if value < 0:
                self.show_message("Şeker seviyesi negatif olamaz!", "error")
                return

            # Mantıksız değer kontrolü
            if value > 600:  # Maksimum makul değer
                self.show_message("Geçersiz şeker seviyesi! Lütfen kontrol edin.", "error")
                return

            # Şu anki saat
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute

            # Ölçüm zamanı kontrolü
            valid_times = [
                ((7, 0), (8, 0), "Sabah"),
                ((12, 0), (13, 0), "Öğle"),
                ((15, 0), (16, 0), "İkindi"),
                ((18, 0), (19, 0), "Akşam"),
                ((22, 0), (23, 0), "Gece")
            ]

            is_valid_time = False
            measurement_period = None
            for (start_h, start_m), (end_h, end_m), period in valid_times:
                if (current_hour > start_h or (current_hour == start_h and current_minute >= start_m)) and \
                   (current_hour < end_h or (current_hour == end_h and current_minute <= end_m)):
                    is_valid_time = True
                    measurement_period = period
                    break

            try:
                db = DatabaseManager.get_instance()
                user = db.get_user_by_tc(self.tc)
                if not user:
                    self.show_message("Kullanıcı bulunamadı!", "error")
                    return

                user_id = user[0]

                # Ölçümü kaydet
                measurement_query = """
                    INSERT INTO sugar_measurements (patient_id, sugar_level, measurement_time)
                    VALUES (%s, %s, %s) RETURNING id
                """
                measurement_result = db.execute_query(measurement_query, (user_id, value, current_time))
                measurement_id = measurement_result[0][0]

                # İnsülin önerisi al
                meal_time = 'açlık'  # Varsayılan olarak açlık
                if current_hour >= 11:  # 11:00'dan sonraki ölçümler tokluk sayılır
                    meal_time = 'tokluk'

                recommendation = db.get_insulin_recommendation(value, meal_time)
                
                if recommendation:
                    insulin_type, base_units, unit_per_carb, notes = recommendation[0]
                    
                    # İnsülin önerisi penceresini göster
                    self.show_insulin_recommendation(
                        measurement_id,
                        user_id,
                        value,
                        insulin_type,
                        base_units,
                        unit_per_carb,
                        notes
                    )

                # Uyarı kontrolü ve kaydetme
                alert_message = None
                alert_type = None

                if value < 70:
                    alert_type = "hipoglisemi"
                    alert_message = "Hipoglisemi riski! Acil müdahale gerekebilir."
                elif value > 200:
                    alert_type = "hiperglisemi"
                    alert_message = "Hiperglisemi durumu! Acil müdahale gerekebilir."

                if alert_message:
                    db.execute_query("""
                        INSERT INTO alerts (patient_id, alert_type, message)
                        VALUES (%s, %s, %s)
                    """, (user_id, alert_type, alert_message))

                if not is_valid_time:
                    db.execute_query("""
                        INSERT INTO alerts (patient_id, alert_type, message)
                        VALUES (%s, %s, %s)
                    """, (user_id, "zaman_uyarisi", 
                          "Ölçüm standart saatler dışında yapıldı. Lütfen belirtilen saatlerde ölçüm yapın."))

                # Başarı mesajı
                success_msg = f"Ölçüm kaydedildi: {value} mg/dL"
                if not is_valid_time:
                    success_msg += "\nUyarı: Ölçüm standart saatler dışında yapıldı."
                if alert_message:
                    success_msg += f"\nUyarı: {alert_message}"

                self.show_message(success_msg, "success")
                
                # Dashboard'u güncelle
                self.show_dashboard()

            except Exception as e:
                self.show_message(f"Veritabanı hatası: {str(e)}", "error")

        except ValueError:
            self.show_message("Lütfen geçerli bir sayı girin!", "error")

    def show_insulin_recommendation(self, measurement_id, patient_id, sugar_level, 
                                  insulin_type, base_units, unit_per_carb, notes):
        """İnsülin önerisi penceresini göster"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("İnsülin Önerisi")
        dialog.geometry("400x500")
        
        # Pencereyi merkeze konumlandır
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Şeker seviyesi bilgisi
        ctk.CTkLabel(
            dialog,
            text=f"Şeker Seviyesi: {sugar_level} mg/dL",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # İnsülin önerisi
        recommendation_frame = ctk.CTkFrame(dialog)
        recommendation_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            recommendation_frame,
            text=f"Önerilen İnsülin Türü: {insulin_type}",
            font=ctk.CTkFont(size=14)
        ).pack(pady=5)
        
        ctk.CTkLabel(
            recommendation_frame,
            text=f"Temel Doz: {base_units} ünite",
            font=ctk.CTkFont(size=14)
        ).pack(pady=5)
        
        if unit_per_carb > 0:
            ctk.CTkLabel(
                recommendation_frame,
                text=f"Karbonhidrat Başına: {unit_per_carb} ünite",
                font=ctk.CTkFont(size=14)
            ).pack(pady=5)
        
        if notes:
            ctk.CTkLabel(
                recommendation_frame,
                text=f"Not: {notes}",
                font=ctk.CTkFont(size=12)
            ).pack(pady=5)
        
        # Karbonhidrat girişi
        carb_frame = ctk.CTkFrame(dialog)
        carb_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            carb_frame,
            text="Alınacak Karbonhidrat (gram):"
        ).pack(pady=5)
        
        carb_entry = ctk.CTkEntry(carb_frame)
        carb_entry.pack(pady=5)
        
        # Toplam insülin hesaplama
        def calculate_total_insulin():
            try:
                carbs = float(carb_entry.get() or 0)
                total = base_units + (carbs * unit_per_carb)
                total_label.configure(
                    text=f"Toplam Önerilen İnsülin: {total:.1f} ünite"
                )
                save_button.configure(state="normal")
                return total
            except ValueError:
                self.show_message("Geçerli bir karbonhidrat değeri girin!", "error")
                save_button.configure(state="disabled")
                return None
        
        calc_button = ctk.CTkButton(
            dialog,
            text="Hesapla",
            command=calculate_total_insulin
        )
        calc_button.pack(pady=10)
        
        total_label = ctk.CTkLabel(
            dialog,
            text="Toplam Önerilen İnsülin: -- ünite",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        total_label.pack(pady=10)
        
        # Notlar
        ctk.CTkLabel(dialog, text="Notlar:").pack(pady=5)
        notes_entry = ctk.CTkTextbox(dialog, height=100)
        notes_entry.pack(padx=20, pady=5, fill="x")
        
        # Kaydetme
        def save_insulin_record():
            total = calculate_total_insulin()
            if total is not None:
                try:
                    db = DatabaseManager.get_instance()
                    db.save_insulin_record(
                        patient_id,
                        measurement_id,
                        insulin_type,
                        total,
                        notes_entry.get("1.0", "end-1c")
                    )
                    self.show_message("İnsülin kaydı başarıyla eklendi!", "success")
                    dialog.destroy()
                    self.show_dashboard()  # Dashboard'u güncelle
                except Exception as e:
                    self.show_message(f"Kayıt hatası: {str(e)}", "error")
        
        save_button = ctk.CTkButton(
            dialog,
            text="Kaydet",
            command=save_insulin_record,
            state="disabled"
        )
        save_button.pack(pady=20)

    def show_message(self, message, message_type="info"):
        """Kullanıcıya mesaj göster"""
        if message_type == "error":
            messagebox.showerror("Hata", message)
        elif message_type == "success":
            messagebox.showinfo("Başarılı", message)
        else:
            messagebox.showinfo("Bilgi", message)

    def save_diet(self, diet_type):
        try:
            db = DatabaseManager.get_instance()

            # Kullanıcı ID'sini al
            user = db.get_user_by_tc(self.tc)
            if not user:
                self.show_message("Kullanıcı bulunamadı!", "error")
                return

            user_id = user[0]

            # Diyet türü ID'sini al
            diet_types = db.execute_query(
                "SELECT id FROM diet_types WHERE name = %s",
                (diet_type,)
            )
            
            if not diet_types:
                self.show_message("Diyet türü bulunamadı!", "error")
                return

            diet_type_id = diet_types[0][0]

            # Bugün için kayıt var mı kontrol et
            existing = db.execute_query("""
                SELECT id FROM diet_tracking 
                WHERE patient_id = %s AND date = CURRENT_DATE
            """, (user_id,))

            if existing:
                # Güncelle
                db.execute_query("""
                    UPDATE diet_tracking 
                    SET diet_type_id = %s, status = 'uygulandı'
                    WHERE patient_id = %s AND date = CURRENT_DATE
                """, (diet_type_id, user_id))
            else:
                # Yeni kayıt
                db.execute_query("""
                    INSERT INTO diet_tracking (patient_id, date, diet_type_id, status)
                    VALUES (%s, CURRENT_DATE, %s, 'uygulandı')
                """, (user_id, diet_type_id))

            self.show_message("Diyet kaydedildi!", "success")
            
            # Dashboard'u güncelle
            self.show_dashboard()

        except Exception as e:
            self.show_message(f"Diyet kaydedilirken hata: {str(e)}", "error")
            print(f"Diyet kaydetme hatası: {str(e)}")  # Debug log

    def save_exercise(self, exercise_type, duration):
        try:
            # Süre kontrolü
            if not duration:
                self.show_message("Lütfen süre girin!", "error")
                return

            duration = int(duration)
            
            # Mantıksız süre kontrolü
            if duration <= 0:
                self.show_message("Süre 0'dan büyük olmalıdır!", "error")
                return
            if duration > 240:  # 4 saatten fazla egzersiz mantıksız
                self.show_message("Geçersiz süre! Lütfen kontrol edin.", "error")
                return

            db = DatabaseManager.get_instance()

            # Kullanıcı ID'sini al
            user = db.get_user_by_tc(self.tc)
            if not user:
                self.show_message("Kullanıcı bulunamadı!", "error")
                return

            user_id = user[0]

            # Egzersiz türü ID'sini al
            exercise_types = db.execute_query(
                "SELECT id FROM exercise_types WHERE name = %s",
                (exercise_type,)
            )
            
            if not exercise_types:
                self.show_message("Egzersiz türü bulunamadı!", "error")
                return

            exercise_type_id = exercise_types[0][0]

            # Bugün için kayıt var mı kontrol et
            existing = db.execute_query("""
                SELECT id FROM exercise_tracking 
                WHERE patient_id = %s AND date = CURRENT_DATE
            """, (user_id,))

            if existing:
                # Güncelle
                db.execute_query("""
                    UPDATE exercise_tracking 
                    SET exercise_type_id = %s, duration = %s, status = 'yapıldı'
                    WHERE patient_id = %s AND date = CURRENT_DATE
                """, (exercise_type_id, duration, user_id))
            else:
                # Yeni kayıt
                db.execute_query("""
                    INSERT INTO exercise_tracking (patient_id, date, exercise_type_id, duration, status)
                    VALUES (%s, CURRENT_DATE, %s, %s, 'yapıldı')
                """, (user_id, exercise_type_id, duration))

            self.show_message(f"Egzersiz kaydedildi! Süre: {duration} dakika", "success")
            
            # Dashboard'u güncelle
            self.show_dashboard()

        except ValueError:
            self.show_message("Lütfen geçerli bir süre girin!", "error")
        except Exception as e:
            self.show_message(f"Egzersiz kaydedilirken hata: {str(e)}", "error")
            print(f"Egzersiz kaydetme hatası: {str(e)}")  # Debug log

    def on_closing(self):
        """Pencere kapatıldığında çağrılır"""
        try:
            self.destroy()  # Bu pencereyi kapat
            self.parent.destroy()  # Ana pencereyi kapat
            sys.exit(0)
        except:
            sys.exit(0)

    def load_user_info(self):
        """Kullanıcı bilgilerini ve profil resmini yükle"""
        try:
            db = DatabaseManager.get_instance()
            user = db.get_user_by_tc(self.tc)
            if not user:
                self.show_message("Kullanıcı bulunamadı!", "error")
                return

            self.user_id = user[0]
            
            # Profil resmini yükle
            image_data, image_type = db.get_profile_image(self.user_id)
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
                    db = DatabaseManager.get_instance()
                    db.save_profile_image(
                        self.user_id,
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
            db = DatabaseManager.get_instance()
            db.delete_profile_image(self.user_id)
            
            self.profile_photo = None
            self.add_profile_to_sidebar()
            
            self.show_message("Profil resmi silindi!", "success")
            
        except Exception as e:
            self.show_message(f"Profil resmi silinirken hata: {str(e)}", "error")

if __name__ == "__main__":
    app = ctk.CTk()
    patient_panel = PatientPanel(app, "12345678901")
    app.mainloop()