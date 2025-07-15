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

# تنظیم لاگ‌گیری
logging.basicConfig(
    filename='logs/log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

FIELD = "All sciences"
MAX_RETRIES = 3
JSON_FILE = "data/university_rankings.json"

def load_previous_rankings():
    """خواندن رتبه‌های قبلی از فایل JSON"""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("rankings", {}).get("leiden", {})
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
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_year(args):
    """اسکریپینگ رتبه برای یک سال خاص"""
    university_name, year = args
    logging.info(f"استخراج رتبه برای سال {year}")
    driver = None
    result = {year: None}
    
    for attempt in range(MAX_RETRIES):
        try:
            driver = setup_driver()
            url = f"https://www.leidenranking.com/ranking/{year}"
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "pagedtable.ranking"))
            )
            time.sleep(random.uniform(10, 15))

            # تلاش برای انتخاب شاخص PP(top 10%)
            try:
                from selenium.webdriver.support.ui import Select
                select = driver.find_element(By.ID, 'indicator_select')
                Select(select).select_by_value('PP(top 10%)')
                time.sleep(5)
            except Exception as e:
                logging.info(f"شاخص PP(top 10%) به‌صورت پیش‌فرض انتخاب شده یا منو یافت نشد در سال {year}: {str(e)}")

            # استخراج HTML
            soup = BeautifulSoup(driver.page_source, 'lxml')
            tables = soup.find_all('table', class_='pagedtable ranking')
            if not tables:
                logging.warning(f"جداول با کلاس 'pagedtable ranking' برای سال {year} یافت نشدند")
                return result

            # جستجوی گسترده‌تر
            found = False
            for table in tables:
                try:
                    rows = table.find_all('tr')
                    logging.debug(f"تعداد ردیف‌ها در جدول سال {year}: {len(rows)}")
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 5:
                            rank_cell = cells[0].get('class', [])
                            university_cell = cells[1].get('class', [])
                            if 'rank' in rank_cell and 'university' in university_cell:
                                university_span = cells[1].find('span', {'data-tooltip': True})
                                university_text = cells[1].text.lower().strip()
                                university_tooltip = university_span['data-tooltip'].lower().strip() if university_span else ""
                                logging.debug(f"نام دانشگاه در ردیف: {university_text}, تولتیپ: {university_tooltip}")
                                keywords = [
                                    university_name.lower(), "ferdowsi univ", "ferdowsi university",
                                    "ferdowsi", "mashhad", "mashhad university", "um.ac.ir",
                                    "ferdosi", "ferdousi", "ferdowsi mashhad"
                                ]
                                if any(keyword in university_text or keyword in university_tooltip for keyword in keywords):
                                    rank = cells[0].text.strip() if cells[0].text.strip().isdigit() else None
                                    pp_top10 = cells[4].text.strip()
                                    if rank:
                                        result[year] = int(rank)
                                        logging.info(f"رتبه برای سال {year}: {result[year]} (PP(top 10%): {pp_top10})")
                                        found = True
                                        break
                    if found:
                        break
                except Exception as e:
                    logging.error(f"خطا در پردازش جدول برای سال {year}: {str(e)}")
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
    years = [str(year) for year in range(2013, 2025)]
    ranks = {year: previous_ranks.get(year, None) for year in years}  # استفاده از رتبه‌های قبلی به عنوان پایه

    # اجرای موازی
    start_time = time.time()
    with Pool(processes=3) as pool:
        args = [(university_name, year) for year in years]
        results = pool.map(scrape_year, args)
    
    # ادغام نتایج جدید
    for result in results:
        for year, rank in result.items():
            if rank is not None:  # فقط اگر رتبه جدید پیدا شد، به‌روزرسانی کن
                ranks[year] = rank
            # اگر رتبه جدید None بود و رتبه قبلی وجود داشت، رتبه قبلی حفظ می‌شود
    
    logging.info(f"استخراج رتبه‌های Leiden برای {university_name} تکمیل شد. زمان اجرا: {time.time() - start_time:.2f} ثانیه")
    return ranks