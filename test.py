import logging
import time
import json
from multiprocessing import Pool
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pathlib import Path
import os

# تنظیم لاگ‌گیری
logging.basicConfig(
    filename='logs/times_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

UNIVERSITY_NAME = "Ferdowsi University of Mashhad"

def setup_driver():
    """تنظیم WebDriver برای هر فرآیند"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124")
    
    # تنظیم مسیر درایور با دسترسی مناسب
    try:
        driver_path = ChromeDriverManager().install()
        return webdriver.Chrome(service=Service(driver_path), options=chrome_options)
    except PermissionError as e:
        logging.error(f"خطای دسترسی در نصب درایور کروم: {str(e)}")
        raise

def scrape_year(year):
    """اسکریپینگ رتبه برای یک سال خاص"""
    logging.info(f"استخراج رتبه برای سال {year}")
    driver = None
    result = {year: None}
    
    try:
        driver = setup_driver()
        url = f"https://www.timeshighereducation.com/world-university-rankings/{year}/world-ranking#!/length/25/locations/IRN/name/ferdowsi/sort_by/rank/sort_order/asc/cols/scores"
        driver.get(url)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "datatable-1"))
        )
        time.sleep(12)  # تاخیر برای اطمینان از بارگذاری کامل

        # استخراج HTML
        soup = BeautifulSoup(driver.page_source, 'lxml')
        table = soup.find('table', id='datatable-1')
        if not table:
            logging.warning(f"جدول با id 'datatable-1' برای سال {year} یافت نشد")
            return result

        rows = table.find_all('tr')
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    rank_cell = cells[0].get('class', [])
                    university_cell = cells[1].text.lower().strip()
                    if 'rank' in rank_cell:
                        if any(keyword in university_cell for keyword in 
                               [UNIVERSITY_NAME.lower(), "ferdowsi univ", "ferdowsi university", 
                                "ferdowsi", "mashhad", "mashhad university", "um.ac.ir", 
                                "ferdosi", "ferdousi", "ferdowsi mashhad"]):
                            rank = cells[0].text.strip()
                            if rank:
                                result[year] = rank
                                logging.info(f"رتبه برای سال {year}: {rank}")
                                break
            except Exception as e:
                logging.error(f"خطا در پردازش ردیف برای سال {year}: {str(e)}")
                continue

        if not result[year]:
            logging.warning(f"دانشگاه {UNIVERSITY_NAME} در سال {year} یافت نشد")

    except Exception as e:
        logging.error(f"خطا در اسکریپینگ برای سال {year}: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logging.error(f"خطا در بستن WebDriver برای سال {year}: {str(e)}")

    return result

def main():
    # ایجاد پوشه logs و data
    Path('logs').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    
    # تنظیم سال‌ها
    years = [str(year) for year in range(2013, 2025)]
    ranks = {year: None for year in years}
    
    # سال‌هایی که اسکریپینگ می‌شوند
    scrape_years = [year for year in years]
    
    # اجرای موازی
    start_time = time.time()
    with Pool(processes=3) as pool:  # کاهش به ۳ فرآیند برای کاهش بار
        results = pool.map(scrape_year, scrape_years)
    
    # جمع‌آوری نتایج
    for result in results:
        ranks.update(result)
    
    # ذخیره خروجی در فایل JSON
    result = {
        "university": UNIVERSITY_NAME,
        "times_rankings": ranks
    }
    with open("data/times_rankings.json", "w", encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logging.info(f"فایل times_rankings.json با موفقیت تولید شد. زمان اجرا: {time.time() - start_time:.2f} ثانیه")

if __name__ == "__main__":
    main()