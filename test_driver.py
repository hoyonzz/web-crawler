from selenium import webdriver
from selenium.webdriver.chrome.options import Options

opt = Options()
opt.add_argument("--headless=new")
opt.add_argument("--no-sandbox")
opt.add_argument("--disable-dev-shm-usage")
opt.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=opt)
driver.get("https://example.com")
print("✅ 제목:", driver.title)   # "Example Domain" 나오면 성공
driver.quit()