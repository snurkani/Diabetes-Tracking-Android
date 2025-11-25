# -*- coding: utf-8 -*-

import schedule
import time
from db_manager import DatabaseManager
import logging

def setup_logging():
    logging.basicConfig(
        filename='scheduler.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def send_weekly_reports():
    """Haftalık raporları gönder"""
    try:
        db = DatabaseManager.get_instance()
        db.send_weekly_reports()
        logging.info("Haftalık raporlar gönderildi")
    except Exception as e:
        logging.error(f"Haftalık rapor gönderimi sırasında hata: {str(e)}")

def send_measurement_reminders():
    """Ölçüm hatırlatmalarını gönder"""
    try:
        db = DatabaseManager.get_instance()
        db.send_measurement_reminders()
        logging.info("Ölçüm hatırlatmaları gönderildi")
    except Exception as e:
        logging.error(f"Ölçüm hatırlatması gönderimi sırasında hata: {str(e)}")

def main():
    setup_logging()
    logging.info("Bildirim zamanlayıcısı başlatıldı")

    # Haftalık raporları her Pazartesi saat 09:00'da gönder
    schedule.every().monday.at("09:00").do(send_weekly_reports)

    # Ölçüm hatırlatmalarını her gün belirli saatlerde gönder
    schedule.every().day.at("07:00").do(send_measurement_reminders)  # Sabah
    schedule.every().day.at("12:00").do(send_measurement_reminders)  # Öğle
    schedule.every().day.at("18:00").do(send_measurement_reminders)  # Akşam

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et
        except Exception as e:
            logging.error(f"Zamanlayıcı döngüsünde hata: {str(e)}")
            time.sleep(300)  # Hata durumunda 5 dakika bekle

if __name__ == "__main__":
    main() 