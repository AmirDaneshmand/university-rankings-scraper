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
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import random

# تنظیم لاگ‌گیری
logging.basicConfig(
    filename='logs/isc_log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

UNIVERSITY_NAME = "Ferdowsi University of Mashhad"
MAX_RETRIES = 3
JSON_FILE = "data/university_rankings.json"
YEAR_MAPPING = {
    "1391-1392": "2",
    "1392-1393": "3",
    "1393-1394": "4",
    "1394-1395": "7",
    "1395-1396": "8",
    "1396-1397": "10",
    "1397-1398": "12",
    "1398-1399": "13",
    "1399-1400": "14",
    "1400-1401": "15",
    "1401-1402": "16"
}

def load_previous_rankings():
    """خواندن رتبه‌های قبلی از فایل JSON"""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("rankings", {}).get("isc", {})
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
    try:
        driver_path = ChromeDriverManager().install()
        return webdriver.Chrome(service=Service(driver_path), options=chrome_options)
    except PermissionError as e:
        logging.error(f"خطای دسترسی در نصب درایور کروم: {str(e)}")
        raise

def scrape_year(args):
    """اسکریپینگ رتبه برای یک سال خاص"""
    university_name, year = args
    logging.info(f"استخراج رتبه برای سال {year}")
    driver = None
    result = {year: None}
    
    for attempt in range(MAX_RETRIES):
        try:
            driver = setup_driver()
            url = "https://ur.isc.ac/Home/RankIranUniv"
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "year_list"))
            )
            time.sleep(random.uniform(10, 15))

            # انتخاب نوع دانشگاه (دانشگاه‌های جامع)
            try:
                univ_type_select = Select(driver.find_element(By.ID, "univ_type_list"))
                univ_type_select.select_by_value("2")  # دانشگاه‌های جامع
                logging.debug(f"نوع دانشگاه به 'دانشگاه‌های جامع' برای سال {year} تنظیم شد")
                time.sleep(2)
            except Exception as e:
                logging.warning(f"خطا در تنظیم نوع دانشگاه برای سال {year}: {str(e)}")
                return result

            # انتخاب سال
            try:
                year_select = Select(driver.find_element(By.ID, "year_list"))
                year_select.select_by_value(YEAR_MAPPING[year])
                logging.debug(f"سال {year} انتخاب شد")
                time.sleep(5)  # انتظار برای بارگذاری جدول
            except Exception as e:
                logging.warning(f"خطا در انتخاب سال {year}: {str(e)}")
                return result

            # جستجوی نام دانشگاه
            try:
                search_input = driver.find_element(By.ID, "filter")
                search_input.clear()
                search_input.send_keys("فردوسی")
                search_input.send_keys(Keys.RETURN)
                logging.debug(f"جستجو برای 'فردوسی' در سال {year} انجام شد")
                time.sleep(5)  # انتظار برای بارگذاری نتایج
            except Exception as e:
                logging.warning(f"خطا در جستجوی دانشگاه برای سال {year}: {str(e)}")
                return result

            # استخراج HTML
            soup = BeautifulSoup(driver.page_source, 'lxml')
            table = soup.find('table')
            if not table:
                logging.warning(f"جدول رتبه‌بندی برای سال {year} یافت نشد")
                return result

            rows = table.find_all('tr')
            logging.debug(f"تعداد ردیف‌ها در جدول سال {year}: {len(rows)}")
            found = False
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        rank_span = cells[0].find('span', class_='FractionTop')
                        rank = rank_span.text.strip() if rank_span else None
                        university_cell = cells[2].text.lower().strip() if len(cells) > 2 else ""
                        logging.debug(f"نام دانشگاه در ردیف: {university_cell}")
                        keywords = [
                            university_name.lower(), "ferdowsi univ", "ferdowsi university",
                            "ferdowsi", "mashhad", "mashhad university", "um.ac.ir",
                            "ferdosi", "ferdousi", "ferdowsi mashhad", "دانشگاه فردوسی"
                        ]
                        if any(keyword in university_cell for keyword in keywords):
                            if rank:
                                result[year] = rank  # ذخیره به صورت رشته
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
    # خواندن رتبه‌های قبلی
    previous_ranks = load_previous_rankings()
    logging.info(f"رتبه‌های قبلی لود شدند: {previous_ranks}")

    # تنظیم سال‌ها
    years = list(YEAR_MAPPING.keys())
    ranks = {year: previous_ranks.get(year, None) for year in years}  # استفاده از رتبه‌های قبلی به عنوان پایه

    # اجرای موازی
    start_time = time.time()
    with Pool(processes=2) as pool:  # ۲ فرآیند برای پایداری
        args = [(university_name, year) for year in years]
        results = pool.map(scrape_year, args)
    
    # ادغام نتایج جدید
    for result in results:
        for year, rank in result.items():
            if rank is not None:  # فقط اگر رتبه جدید پیدا شد، به‌روزرسانی کن
                ranks[year] = rank
            # اگر رتبه جدید None بود و رتبه قبلی وجود داشت، رتبه قبلی حفظ می‌شود
    
    
    logging.info(f"فایل university_rankings.json با موفقیت به‌روزرسانی شد. زمان اجرا: {time.time() - start_time:.2f} ثانیه")
    return ranks

