import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def get_rank(university_name):
    try:
        logging.info(f"دریافت رتبه‌بندی SCImago برای {university_name}")
        url = "https://www.scimagoir.com/rankings.php?sector=Higher+educ."
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'lxml')
        driver.quit()

        table = soup.find('table', class_='ranking-table')  # کلاس فرضی
        if not table:
            logging.warning("جدول رتبه‌بندی SCImago یافت نشد")
            return {}

        ranks = {}
        years = [str(year) for year in range(2010, 2024)]
        for year in years:
            ranks[year] = None

        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) > 2 and university_name.lower() in cells[1].text.lower():
                for year in years:
                    year_index = years.index(year) + 2
                    if len(cells) > year_index:
                        rank = cells[year_index].text.strip()
                        ranks[year] = int(rank) if rank.isdigit() else None

        return ranks

    except Exception as e:
        logging.error(f"خطا در رتبه‌بندی SCImago برای {university_name}: {str(e)}")
        return {}