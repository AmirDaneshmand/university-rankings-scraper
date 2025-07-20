import json
import logging
import os
from dotenv import load_dotenv
from modules import leiden, scimago, times, shanghai, isc

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیم لاگ‌گیری
os.makedirs('logs', exist_ok=True)  # ایجاد پوشه logs در صورت عدم وجود
logging.basicConfig(
    filename='logs/log.txt',
    level=logging.DEBUG if os.getenv('DEBUG') == 'True' else logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

UNIVERSITY_NAME = "Ferdowsi University of Mashhad"
JSON_FILE = "data/university_rankings.json"

def load_previous_rankings():
    """خواندن رتبه‌های قبلی از فایل JSON"""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get("rankings", {})
        except Exception as e:
            logging.error(f"خطا در خواندن فایل JSON: {str(e)}")
            return {}
    return {}

def main():
    try:
        # خواندن رتبه‌های قبلی
        previous_ranks = load_previous_rankings()

        # جمع‌آوری رتبه‌ها از هر نظام
        result = {
            "university": UNIVERSITY_NAME,
            "rankings": {
                "leiden": leiden.get_rank(UNIVERSITY_NAME),
                "scimago": scimago.get_rank(UNIVERSITY_NAME),
                "isc": isc.get_rank(UNIVERSITY_NAME),
                "times": times.get_rank(UNIVERSITY_NAME),
                "shanghai": shanghai.get_rank(UNIVERSITY_NAME)
            }
        }

        # ادغام با رتبه‌های قبلی
        for system in result["rankings"]:
            if system in previous_ranks:
                for year, rank in previous_ranks[system].items():
                    if year not in result["rankings"][system] or result["rankings"][system][year] is None:
                        result["rankings"][system][year] = rank

        # ذخیره خروجی
        os.makedirs(os.path.dirname(JSON_FILE), exist_ok=True)
        with open(JSON_FILE, "w", encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logging.error(f"خطا در اجرای اصلی: {str(e)}")

if __name__ == "__main__":
    main()