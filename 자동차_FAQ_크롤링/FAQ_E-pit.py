import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def create_stealth_driver():
    """봇 탐지 우회를 위한 Chrome Driver 설정"""
    options = Options()
    
    # 보안 및 기본 옵션
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # 봇 탐지 방지 핵심 옵션
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
    
    # navigator.webdriver 속성 비활성화
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    return driver

def scrape_current_page(driver, data_list):
    """현재 페이지의 질문 요소를 클릭하여 질문 및 답변 수집"""
    # p.title 요소들을 탐색
    title_elements = driver.find_elements(By.CSS_SELECTOR, "p.title")
    
    for title_elem in title_elements:
        try:
            # 1. 질문 요소 위치로 스크롤 및 클릭 (아코디언 펼침)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", title_elem)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", title_elem)
            time.sleep(0.4)
            
            # 질문 텍스트 추출 (개행 문자 정리)
            question_text = " ".join(title_elem.text.split())
            if not question_text:
                continue

            # 2. 답변 영역(div.desc) 추출
            # 질문 요소의 상위 아코디언 컨테이너에서 div.desc 탐색
            try:
                # 상위 부모 요소를 거슬러 올라가 div.desc 찾기
                parent_box = title_elem.find_element(By.XPATH, "./ancestor::*[contains(@class, 'faq') or contains(@class, 'item') or contains(@class, 'accordion')][1]")
                desc_elem = parent_box.find_element(By.CSS_SELECTOR, "div.desc")
                answer_text = desc_elem.text.strip()
            except Exception:
                # 직접 부모 탐색 실패 시 가장 가까운 하위/인접 div.desc 탐색
                try:
                    desc_elem = title_elem.find_element(By.XPATH, "./following::div[contains(@class, 'desc')][1]")
                    answer_text = desc_elem.text.strip()
                except Exception:
                    answer_text = ""

            data_list.append({
                "질문": question_text,
                "답변": answer_text
            })
            
        except Exception as e:
            print(f"    - 항목 추출 중 예외 발생: {e}")

def process_all_pages(driver, data_list):
    """'충전소 기본 이용' 탭 내 전체 페이지 순회"""
    current_page = 1
    
    while True:
        print(f"  * {current_page}페이지 수집 진행 중...")
        time.sleep(1)
        scrape_current_page(driver, data_list)
        
        next_page_num = current_page + 1
        
        # 페이지네이션 버튼 탐색
        page_btn_xpath = f"//ul[contains(@class, 'pagination') or contains(@class, 'paging')]//a[text()='{next_page_num}'] | //button[text()='{next_page_num}']"
        next_links = driver.find_elements(By.XPATH, page_btn_xpath)
        
        if next_links and next_links[0].is_displayed():
            next_btn = next_links[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(1.5)
            current_page += 1
        else:
            # 다음 페이지 블록 버튼 ('>' 화살표 등) 검사
            next_arrow_xpath = "//a[contains(@class, 'next') or contains(@class, 'btn-next')] | //button[contains(@class, 'next')]"
            arrow_btns = driver.find_elements(By.XPATH, next_arrow_xpath)
            
            if arrow_btns and arrow_btns[0].is_displayed() and arrow_btns[0].is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", arrow_btns[0])
                driver.execute_script("arguments[0].click();", arrow_btns[0])
                time.sleep(1.5)
                current_page += 1
            else:
                print(f"  * 마지막 페이지({current_page}p)까지 수집 완료.")
                break

def main():
    target_url = "https://www.e-pit.co.kr/brand-web/support/faq"
    driver = create_stealth_driver()
    data_list = []

    try:
        print(f"[+] 페이지 접속 중: {target_url}")
        driver.get(target_url)
        wait = WebDriverWait(driver, 15)
        time.sleep(2)

        # 1. '충전소 기본 이용' 탭 클릭 (ul.tab-list 내 li.tab)
        print("[+] '충전소 기본 이용' 탭 탐색 중...")
        tab_xpath = "//ul[contains(@class, 'tab-list')]//li[contains(@class, 'tab') and contains(text(), '충전소 기본 이용')]"
        
        try:
            tab_btn = wait.until(EC.element_to_be_clickable((By.XPATH, tab_xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab_btn)
            driver.execute_script("arguments[0].click();", tab_btn)
            print("[+] '충전소 기본 이용' 탭 선택 완료")
            time.sleep(2)
        except Exception as e:
            print(f"[오류] '충전소 기본 이용' 탭을 찾을 수 없습니다: {e}")
            return

        # 2. 전체 페이지 순회 및 수집
        process_all_pages(driver, data_list)

        # 3. CSV 파일 저장 (utf-8-sig)
        if data_list:
            df = pd.DataFrame(data_list)
            df.drop_duplicates(subset=["질문", "답변"], inplace=True)
            
            output_filename = "epit_faq_충전소기본이용.csv"
            df.to_csv(output_filename, index=False, encoding='utf-8-sig')
            print(f"\n[성공] 크롤링 및 저장 완료!")
            print(f"  - 저장 파일명: {output_filename}")
            print(f"  - 총 수집 건수: {len(df)}건")
        else:
            print("\n[경고] 수집된 데이터가 없습니다.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()