from crawlers.wanted_crawler import WantedCrawler

# 1. WantedCrawler 객체 생성
crawler = WantedCrawler()

# 2. Notion 로직 없이, crawl 메서드 직접 호출
crawled_data = []
try:
    # crawl() 메서드가 반환하는 값을 변수에 저장
    crawled_data = crawler.crawl(keyword='Python')
except Exception as e:
    print(f"테스트 중 오류 발생: {e}")
finally:
    crawler.close_driver()
    print("테스트 종료. 드라이버가 종료되었습니다.")

# 3. 크롤링 결과를 화면에 직접 출력하여 확인
if crawled_data:
    print(f"\n[크롤링 결과 (총 { len(crawled_data)}개)]")
    # 상위 5개 결과만 샘플로 출력
    for i, item in enumerate(crawled_data[:5]):
        print(f" {i+1}, {item['title']} @ {item['company']}")
else:
    print("\n[크롤링 결과]")
    print(" 데이터를 가져오지 못했습니다.")