import logging
import time
import json
import os
from multiprocessing import Pool
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import random
from dotenv import load_dotenv

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
MAX_RETRIES = 3
JSON_FILE = "data/university_rankings.json"

def load_previous_rankings():
    """خواندن رتبه‌های قبلی از فایل JSON"""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("rankings", {}).get("times", {})
        except Exception as e:
            logging.error(f"خطا در خواندن فایل JSON: {str(e)}")
            return {}
    return {}

def setup_driver():
    """تنظیم WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124")
    chrome_options.add_argument("--log-level=3")  # سرکوب پیام‌های کنسول WebDriver
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # غیرفعال کردن لاگ‌های DevTools
    try:
        driver_path = ChromeDriverManager().install()
        return webdriver.Chrome(service=Service(driver_path), options=chrome_options)
    except PermissionError as e:
        logging.error(f"خطای دسترسی در نصب درایور کروم: {str(e)}")
        raise

def scrape_year(args):
    """اسکریپینگ رتبه برای یک سال خاص"""
    university_name, year = args
    logging.info(f"استخراج رتبه برای سال {year} (Times Higher Education)")
    driver = None
    result = {year: None}
    
    for attempt in range(MAX_RETRIES):
        try:
            driver = setup_driver()
            url = f"https://www.timeshighereducation.com/world-university-rankings/{year}/world-ranking#!/length/25/locations/IRN/name/ferdowsi/sort_by/rank/sort_order/asc/cols/scores"
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "datatable-1"))
            )
            time.sleep(random.uniform(10, 15))

            # استخراج HTML
            soup = BeautifulSoup(driver.page_source, 'lxml')
            table = soup.find('table', id='datatable-1')
            if not table:
                logging.warning(f"جدول با id 'datatable-1' برای سال {year} یافت نشد")
                return result

            rows = table.find_all('tr')
            logging.debug(f"تعداد ردیف‌ها در جدول سال {year}: {len(rows)}")
            found = False
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        rank_cell = cells[0].get('class', [])
                        university_cell = cells[1].text.lower().strip()
                        if 'rank' in rank_cell:
                            logging.debug(f"نام دانشگاه در ردیف: {university_cell}")
                            keywords = [
                                university_name.lower(), "ferdowsi univ", "ferdowsi university",
                                "ferdowsi", "mashhad", "mashhad university", "um.ac.ir",
                                "ferdosi", "ferdousi", "ferdowsi mashhad"
                            ]
                            if any(keyword in university_cell for keyword in keywords):
                                rank = cells[0].text.strip()
                                if rank:
                                    result[year] = rank
                                    logging.info(f"رتبه برای سال {year}: {rank}")
                                    found = True
                                    break
                except Exception as e:
                    logging.error(f"خطا در پردازش ردیف برای سال {year}: {str(e)}")
                    continue

            if not found:
                logging.warning(f"دانشگاه {university_name} در سال {year} یافت نشد")
            break

        except Exception as e:
            logging.error(f"خطا در اسکریپینگ برای سال {year}، تلاش {attempt + 1}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(random.uniform(5, 10))
                continue
            else:
                logging.error(f"تلاش‌های مجدد برای سال {year} به پایان رسید")
                break
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logging.error(f"خطا در بستن WebDriver برای سال {year}: {str(e)}")

    return result

def get_rank(university_name):
    """تابع اصلی برای استخراج رتبه‌ها با ادغام نتایج قبلی"""
    previous_ranks = load_previous_rankings()
    logging.info(f"رتبه‌های قبلی لود شدند: {previous_ranks}")

    years = [str(year) for year in range(2013, 2025)]
    ranks = {year: previous_ranks.get(year, None) for year in years}

    start_time = time.time()
    with Pool(processes=2) as pool:
        args = [(university_name, year) for year in years]
        results = pool.map(scrape_year, args)
    
    for result in results:
        for year, rank in result.items():
            if rank is not None:
                ranks[year] = rank
    
    logging.info(f"استخراج رتبه‌های Times Higher Education برای {university_name} تکمیل شد. زمان اجرا: {time.time() - start_time:.2f} ثانیه")
    return ranks