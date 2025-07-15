import logging
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pathlib import Path

# تنظیم لاگ‌گیری
logging.basicConfig(
    filename='logs/log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

UNIVERSITY_NAME = "Ferdowsi University of Mashhad"
FIELD = "All sciences"

def scrape_leiden_ranks(university_name):
    # تنظیم سال‌ها
    years = ["2011_2012"] + [str(year) for year in range(2013, 2025)]
    years = [str(year) for year in range(2017, 2025)]
    ranks = {year: None for year in years}

    # تنظیم Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        for year in years:
            logging.info(f"استخراج رتبه برای سال {year}")
            url = f"https://www.leidenranking.com/ranking/{year}/list"
            try:
                driver.get(url)
                WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "pagedtable.ranking"))
                )
                time.sleep(12)  # تاخیر برای اطمینان از بارگذاری کامل همه جداول
            except Exception as e:
                logging.warning(f"جداول برای سال {year} بارگذاری نشدند: {str(e)}")
                logging.info(f"برای سال {year}، آرشیو Zenodo را بررسی کنید: https://zenodo.org/records/8027120")
                continue

            # انتخاب شاخص PP(top 10%) اگر لازم باشد
            try:
                from selenium.webdriver.support.ui import Select
                select = driver.find_element(By.ID, 'indicator_select')
                Select(select).select_by_value('PP(top 10%)')
                time.sleep(10)  # انتظار برای به‌روزرسانی جدول
            except Exception as e:
                logging.info(f"شاخص PP(top 10%) به‌صورت پیش‌فرض انتخاب شده یا منو یافت نشد: {str(e)}")

            # استخراج HTML
            soup = BeautifulSoup(driver.page_source, 'lxml')
            tables = soup.find_all('table', class_='pagedtable ranking')

            if not tables:
                logging.warning(f"جداول با کلاس 'pagedtable ranking' برای سال {year} یافت نشدند")
                continue

            # جستجو در تمام جداول
            found = False
            for table in tables:
                try:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 5:
                            rank_cell = cells[0].get('class', [])
                            university_cell = cells[1].get('class', [])
                            if 'rank' in rank_cell and 'university' in university_cell:
                                university_span = cells[1].find('span', {'data-tooltip': True})
                                university_text = cells[1].text.lower().strip()
                                university_tooltip = university_span['data-tooltip'].lower().strip() if university_span else ""
                                if any(keyword in university_text or keyword in university_tooltip for keyword in 
                                       [university_name.lower(), "ferdowsi univ", "ferdowsi university"]):
                                    rank = cells[0].text.strip() if cells[0].text.strip().isdigit() else None
                                    pp_top10 = cells[4].text.strip()
                                    if rank:
                                        ranks[year] = int(rank)
                                        logging.info(f"رتبه برای سال {year}: {ranks[year]} (PP(top 10%): {pp_top10})")
                                        found = True
                                        break
                    if found:
                        break
                except Exception as e:
                    logging.error(f"خطا در پردازش جدول برای سال {year}: {str(e)}")
                    continue

            if not found:
                logging.warning(f"دانشگاه {university_name} در سال {year} یافت نشد")

    except Exception as e:
        logging.error(f"خطا در اسکریپینگ برای {university_name}: {str(e)}")
    finally:
        try:
            driver.quit()
        except Exception as e:
            logging.error(f"خطا در بستن WebDriver: {str(e)}")

    return ranks

def main():
    # ایجاد پوشه logs و data
    Path('logs').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    
    # دریافت رتبه‌بندی
    ranks = scrape_leiden_ranks(UNIVERSITY_NAME)
    
    # ذخیره خروجی در فایل JSON
    result = {
        "university": UNIVERSITY_NAME,
        "leiden_rankings": ranks
    }
    with open("data/leiden_rankings.json", "w", encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logging.info("فایل leiden_rankings.json با موفقیت تولید شد")

if __name__ == "__main__":
    main()