# import logging
# import requests
# # import pdfplumber
# import io

# def get_rank(university_name):
#     try:
#         logging.info(f"دریافت رتبه‌بندی ISC برای {university_name}")
#         url = "http://ur.isc.gov.ir/rankings.pdf"  # URL فرضی
#         response = requests.get(url)
#         response.raise_for_status()

#         pdf_file = io.BytesIO(response.content)
#         ranks = {}
#         years = [str(year) for year in range(2010, 2024)]
#         for year in years:
#             ranks[year] = None

#         with pdfplumber.open(pdf_file) as pdf:
#             for page in pdf.pages:
#                 text = page.extract_text()
#                 if not text:
#                     continue
#                 lines = text.split('\n')
#                 for line in lines:
#                     if university_name.lower() in line.lower():
#                         for year in years:
#                             if year in line:
#                                 parts = line.split()
#                                 for i, part in enumerate(parts):
#                                     if year in part and i + 1 < len(parts):
#                                         rank = parts[i + 1]
#                                         ranks[year] = int(rank) if rank.isdigit() else None

#         return ranks

#     except Exception as e:
#         logging.error(f"خطا در رتبه‌بندی ISC برای {university_name}: {str(e)}")
#         return {}