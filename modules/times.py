import logging

def get_rank(university_name):
    try:
        logging.info(f"دریافت رتبه‌بندی Times برای {university_name}")
        # داده‌های دستی به دلیل محدودیت‌های اسکرپینگ
        ranks = {}
        years = [str(year) for year in range(2010, 2024)]
        for year in years:
            ranks[year] = None
        # نمونه داده‌های دستی برای سال‌های خاص
        ranks["2022"] = "601-800"
        ranks["2023"] = "601-800"
        return ranks

    except Exception as e:
        logging.error(f"خطا در رتبه‌بندی Times برای {university_name}: {str(e)}")
        return {}