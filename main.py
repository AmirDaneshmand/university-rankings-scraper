import json
import logging
from modules import leiden, scimago, isc, times, shanghai

# تنظیم لاگ‌گیری
logging.basicConfig(
    filename='logs/log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

UNIVERSITY_NAME = "Ferdowsi University of Mashhad"

def main():
    try:
        result = {
            "university": UNIVERSITY_NAME,
            "rankings": {
                "leiden": leiden.get_rank(UNIVERSITY_NAME),
                # "scimago": scimago.get_rank(UNIVERSITY_NAME),
                # "isc": isc.get_rank(UNIVERSITY_NAME),
                # "times": times.get_rank(UNIVERSITY_NAME),
                # "shanghai": shanghai.get_rank(UNIVERSITY_NAME)
            }
        }

        with open("data/university_rankings.json", "w", encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logging.info("فایل university_rankings.json با موفقیت تولید شد")
        
    except Exception as e:
        logging.error(f"خطا در اجرای اصلی: {str(e)}")

if __name__ == "__main__":
    main()