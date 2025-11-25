import psycopg2
from psycopg2 import pool
import logging
from datetime import datetime

class DatabaseManager:
    _instance = None
    _pool = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    def __init__(self):
        if DatabaseManager._instance is not None:
            raise Exception("Bu sınıf bir Singleton'dır!")
        else:
            DatabaseManager._instance = self
            self._setup_logging()
            self._create_pool()

    def _setup_logging(self):
        logging.basicConfig(
            filename='database.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _create_pool(self):
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dbname="diyabet",
                user="postgres",
                password="sumeyye",
                host="127.0.0.1",
                port="5432",
                client_encoding='UTF8'
            )
            logging.info("Veritabanı bağlantı havuzu oluşturuldu")
        except Exception as e:
            logging.error(f"Veritabanı bağlantı havuzu oluşturulurken hata: {str(e)}")
            raise

    def get_connection(self):
        if self._pool:
            return self._pool.getconn()
        else:
            raise Exception("Veritabanı bağlantı havuzu bulunamadı!")

    def return_connection(self, conn):
        if self._pool:
            self._pool.putconn(conn)

    def execute_query(self, query, params=None):
        conn = None
        cur = None
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            if query.strip().upper().startswith(('SELECT', 'RETURNING')):
                result = cur.fetchall()
            else:
                result = None
                
            conn.commit()
            return result
            
        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f"Sorgu çalıştırılırken hata: {str(e)}\nSorgu: {query}\nParametreler: {params}")
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                self.return_connection(conn)

    def close_all(self):
        if self._pool:
            self._pool.closeall()
            logging.info("Tüm veritabanı bağlantıları kapatıldı")

    def get_user_by_tc(self, tc):
        query = "SELECT * FROM users WHERE tc = %s"
        result = self.execute_query(query, (tc,))
        return result[0] if result else None

    def get_user_by_id(self, user_id):
        """Kullanıcıyı ID ile getir"""
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def get_doctor_patients(self, doctor_id):
        """Doktorun hasta listesini getir"""
        query = """
            SELECT 
                u.tc,
                u.name,
                u.surname,
                u.birth_date,
                u.gender,
                u.email,
                u.phone
            FROM users u
            JOIN doctor_patient dp ON u.user_id = dp.patient_id
            WHERE dp.doctor_id = %s 
            AND dp.status = 'aktif'
            ORDER BY u.surname, u.name
        """
        return self.execute_query(query, (doctor_id,))

    def get_patient_measurements(self, patient_id, start_date=None, end_date=None):
        """Hastanın kan şekeri ölçümlerini getir"""
        query = """
            SELECT 
                id,
                sugar_level,
                measurement_time,
                notes
            FROM sugar_measurements 
            WHERE patient_id = %s
        """
        params = [patient_id]
        
        if start_date:
            query += " AND measurement_time >= %s"
            params.append(start_date)
        if end_date:
            query += " AND measurement_time <= %s"
            params.append(end_date)
            
        query += " ORDER BY measurement_time DESC"
        return self.execute_query(query, tuple(params))

    def save_sugar_measurement(self, patient_id, sugar_level, measurement_time=None, notes=None):
        """Kan şekeri ölçümünü kaydet"""
        if measurement_time is None:
            measurement_time = datetime.now()
            
        query = """
            INSERT INTO sugar_measurements 
            (patient_id, sugar_level, measurement_time, notes)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        result = self.execute_query(query, (patient_id, sugar_level, measurement_time, notes))
        return result[0][0] if result else None

    def save_diet_tracking(self, patient_id, diet_type_id, date=None, status='beklemede', notes=None):
        """Diyet takip kaydını ekle"""
        if date is None:
            date = datetime.now().date()
            
        query = """
            INSERT INTO diet_tracking 
            (patient_id, diet_type_id, date, status, notes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self.execute_query(query, (patient_id, diet_type_id, date, status, notes))
        return result[0][0] if result else None

    def save_exercise_tracking(self, patient_id, exercise_type_id, duration, date=None, status='beklemede', notes=None):
        """Egzersiz takip kaydını ekle"""
        if date is None:
            date = datetime.now().date()
            
        query = """
            INSERT INTO exercise_tracking 
            (patient_id, exercise_type_id, duration, date, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self.execute_query(query, (patient_id, exercise_type_id, duration, date, status, notes))
        return result[0][0] if result else None

    def update_diet_tracking(self, tracking_id, status, notes=None):
        """Diyet takip kaydını güncelle"""
        query = """
            UPDATE diet_tracking
            SET status = %s, notes = %s
            WHERE id = %s
        """
        self.execute_query(query, (status, notes, tracking_id))

    def update_exercise_tracking(self, tracking_id, status, notes=None):
        """Egzersiz takip kaydını güncelle"""
        query = """
            UPDATE exercise_tracking
            SET status = %s, notes = %s
            WHERE id = %s
        """
        self.execute_query(query, (status, notes, tracking_id))

    def get_diet_types(self):
        """Diyet türlerini getir"""
        query = "SELECT id, name, description FROM diet_types ORDER BY name"
        return self.execute_query(query)

    def get_exercise_types(self):
        """Egzersiz türlerini getir"""
        query = "SELECT id, name, description FROM exercise_types ORDER BY name"
        return self.execute_query(query)

    def get_daily_diet_tracking(self, patient_id, date=None):
        """Belirli bir güne ait diyet takip kayıtlarını getir"""
        if date is None:
            date = datetime.now().date()
            
        query = """
            SELECT dt.id, dty.name, dt.status, dt.notes
            FROM diet_tracking dt
            JOIN diet_types dty ON dt.diet_type_id = dty.id
            WHERE dt.patient_id = %s AND dt.date = %s
            ORDER BY dt.id DESC
        """
        return self.execute_query(query, (patient_id, date))

    def get_daily_exercise_tracking(self, patient_id, date=None):
        """Belirli bir güne ait egzersiz takip kayıtlarını getir"""
        if date is None:
            date = datetime.now().date()
            
        query = """
            SELECT et.id, ety.name, et.duration, et.status, et.notes
            FROM exercise_tracking et
            JOIN exercise_types ety ON et.exercise_type_id = ety.id
            WHERE et.patient_id = %s AND et.date = %s
            ORDER BY et.id DESC
        """
        return self.execute_query(query, (patient_id, date))

    def get_daily_measurements(self, patient_id, date=None):
        """Belirli bir güne ait kan şekeri ölçümlerini getir"""
        if date is None:
            date = datetime.now().date()
            
        query = """
            SELECT id, sugar_level, measurement_time, notes
            FROM sugar_measurements
            WHERE patient_id = %s 
            AND DATE(measurement_time) = %s
            ORDER BY measurement_time DESC
        """
        return self.execute_query(query, (patient_id, date))

    def get_measurement_statistics(self, patient_id, start_date=None, end_date=None):
        """Belirli bir tarih aralığı için ölçüm istatistiklerini getir"""
        query = """
            SELECT 
                COUNT(*) as total_measurements,
                ROUND(AVG(sugar_level)::numeric, 2) as average_level,
                MIN(sugar_level) as min_level,
                MAX(sugar_level) as max_level,
                COUNT(CASE WHEN sugar_level < 70 THEN 1 END) as low_count,
                COUNT(CASE WHEN sugar_level > 200 THEN 1 END) as high_count
            FROM sugar_measurements
            WHERE patient_id = %s
        """
        params = [patient_id]
        
        if start_date:
            query += " AND measurement_time >= %s"
            params.append(start_date)
        if end_date:
            query += " AND measurement_time <= %s"
            params.append(end_date)
            
        result = self.execute_query(query, tuple(params))
        return result[0] if result else None

    def get_patient_alerts(self, patient_id, unread_only=False):
        """Hastanın uyarılarını getir"""
        query = """
            SELECT id, alert_type, message, alert_time, priority
            FROM alerts
            WHERE patient_id = %s
        """
        if unread_only:
            query += " AND is_read = FALSE"
            
        query += " ORDER BY alert_time DESC"
        return self.execute_query(query, (patient_id,))

    def mark_alert_as_read(self, alert_id):
        """Uyarıyı okundu olarak işaretle"""
        query = """
            UPDATE alerts
            SET is_read = TRUE
            WHERE id = %s
        """
        self.execute_query(query, (alert_id,))

    def save_alert(self, patient_id, alert_type, message, priority='normal'):
        """Yeni uyarı ekle"""
        valid_types = ['şeker_ölçümü', 'diyet_hatırlatma', 'egzersiz_hatırlatma', 
                      'yüksek_şeker', 'düşük_şeker', 'genel']
        if alert_type not in valid_types:
            raise ValueError(f"Geçersiz uyarı tipi. Geçerli tipler: {', '.join(valid_types)}")
            
        query = """
            INSERT INTO alerts (patient_id, alert_type, message, priority)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        result = self.execute_query(query, (patient_id, alert_type, message, priority))
        return result[0][0] if result else None

    def get_profile_image(self, user_id):
        """Kullanıcının profil resmini getir"""
        query = """
            SELECT profile_image, profile_image_type
            FROM users
            WHERE user_id = %s
        """
        result = self.execute_query(query, (user_id,))
        if result and result[0][0] is not None:
            return result[0][0], result[0][1]  # image_data, image_type
        return None, None

    def save_profile_image(self, user_id, image_data, image_type):
        """Kullanıcının profil resmini kaydet"""
        query = """
            UPDATE users
            SET profile_image = %s, profile_image_type = %s
            WHERE user_id = %s
        """
        self.execute_query(query, (image_data, image_type, user_id))

    def delete_profile_image(self, user_id):
        """Kullanıcının profil resmini sil"""
        query = """
            UPDATE users
            SET profile_image = NULL, profile_image_type = NULL
            WHERE user_id = %s
        """
        self.execute_query(query, (user_id,))

    def get_patient_summary(self, patient_id):
        """Hastanın özet bilgilerini getir"""
        # Son 7 günlük ölçüm istatistikleri
        stats_query = """
            SELECT 
                COUNT(*) as total_measurements,
                ROUND(AVG(sugar_level)::numeric, 2) as avg_sugar_level,
                COUNT(CASE WHEN sugar_level < 70 THEN 1 END) as low_count,
                COUNT(CASE WHEN sugar_level > 200 THEN 1 END) as high_count
            FROM sugar_measurements
            WHERE patient_id = %s
            AND measurement_time >= CURRENT_DATE - INTERVAL '7 days'
        """
        
        # Son diyet ve egzersiz durumu
        diet_query = """
            SELECT 
                dt.date,
                dty.name as diet_type,
                dt.status
            FROM diet_tracking dt
            JOIN diet_types dty ON dt.diet_type_id = dty.id
            WHERE dt.patient_id = %s
            ORDER BY dt.date DESC, dt.id DESC
            LIMIT 1
        """
        
        exercise_query = """
            SELECT 
                et.date,
                ety.name as exercise_type,
                et.duration,
                et.status
            FROM exercise_tracking et
            JOIN exercise_types ety ON et.exercise_type_id = ety.id
            WHERE et.patient_id = %s
            ORDER BY et.date DESC, et.id DESC
            LIMIT 1
        """
        
        stats = self.execute_query(stats_query, (patient_id,))
        diet = self.execute_query(diet_query, (patient_id,))
        exercise = self.execute_query(exercise_query, (patient_id,))
        
        return {
            'stats': stats[0] if stats else None,
            'last_diet': diet[0] if diet else None,
            'last_exercise': exercise[0] if exercise else None
        }

    def get_doctor_patients_count(self, doctor_id):
        """Doktorun toplam hasta sayısını getir"""
        query = """
            SELECT COUNT(*)
            FROM doctor_patient
            WHERE doctor_id = %s AND status = 'aktif'
        """
        result = self.execute_query(query, (doctor_id,))
        return result[0][0] if result else 0

    def get_daily_measurements_count(self, doctor_id):
        """Doktorun hastalarının günlük toplam ölçüm sayısını getir"""
        query = """
            SELECT COUNT(*)
            FROM sugar_measurements sm
            JOIN doctor_patient dp ON sm.patient_id = dp.patient_id
            WHERE dp.doctor_id = %s 
            AND dp.status = 'aktif'
            AND DATE(sm.measurement_time) = CURRENT_DATE
        """
        result = self.execute_query(query, (doctor_id,))
        return result[0][0] if result else 0

    def get_critical_patients_count(self, doctor_id):
        """Kritik değerlerde ölçümü olan hasta sayısını getir"""
        query = """
            SELECT COUNT(DISTINCT dp.patient_id)
            FROM doctor_patient dp
            JOIN sugar_measurements sm ON dp.patient_id = sm.patient_id
            WHERE dp.doctor_id = %s 
            AND dp.status = 'aktif'
            AND sm.measurement_time >= CURRENT_DATE
            AND (sm.sugar_level < 70 OR sm.sugar_level > 180)
        """
        result = self.execute_query(query, (doctor_id,))
        return result[0][0] if result else 0

    def get_doctor_patients_weekly_averages(self, doctor_id):
        """Doktorun hastalarının haftalık ortalama şeker değerlerini getir"""
        query = """
            WITH daily_averages AS (
                SELECT 
                    DATE(sm.measurement_time) as measure_date,
                    AVG(sm.sugar_level) as avg_sugar
                FROM sugar_measurements sm
                JOIN doctor_patient dp ON sm.patient_id = dp.patient_id
                WHERE dp.doctor_id = %s 
                AND dp.status = 'aktif'
                AND sm.measurement_time >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(sm.measurement_time)
                ORDER BY DATE(sm.measurement_time)
            )
            SELECT measure_date, ROUND(avg_sugar::numeric, 2)
            FROM daily_averages
        """
        return self.execute_query(query, (doctor_id,))

    def get_doctor_recent_measurements(self, doctor_id, limit=10):
        """Doktorun hastalarının son ölçümlerini getir"""
        query = """
            SELECT 
                u.tc,
                CONCAT(u.name, ' ', u.surname) as full_name,
                sm.measurement_time,
                sm.sugar_level,
                CASE 
                    WHEN sm.sugar_level < 70 THEN 'Düşük'
                    WHEN sm.sugar_level > 180 THEN 'Yüksek'
                    ELSE 'Normal'
                END as status
            FROM sugar_measurements sm
            JOIN doctor_patient dp ON sm.patient_id = dp.patient_id
            JOIN users u ON dp.patient_id = u.user_id
            WHERE dp.doctor_id = %s 
            AND dp.status = 'aktif'
            ORDER BY sm.measurement_time DESC
            LIMIT %s
        """
        return self.execute_query(query, (doctor_id, limit))

    def get_doctor_patients_list(self, doctor_id):
        """Doktorun hasta listesini detaylı bilgilerle getir"""
        query = """
            SELECT 
                u.tc,
                u.name,
                u.surname,
                u.birth_date,
                u.gender,
                u.email,
                u.phone,
                dp.created_at as start_date
            FROM users u
            JOIN doctor_patient dp ON u.user_id = dp.patient_id
            WHERE dp.doctor_id = %s 
            AND dp.status = 'aktif'
            ORDER BY u.surname, u.name
        """
        return self.execute_query(query, (doctor_id,))