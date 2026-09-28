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
    """봇 탐지 우회를 위한 강력한 Chrome Driver 생성"""
    options = Options()
    
    # 기본 가상화 및 백그라운드 옵션
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
    
    # navigator.webdriver 속성 재정의 (봇 감지 피함)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    return driver

def scrape_current_page(driver, data_list):
    """현재 페이지의 모든 질문 항목을 클릭하여 질문 및 답변 수집"""
    # faq-question 클래스를 가진 요소 탐색
    questions = driver.find_elements(By.CSS_SELECTOR, "div.faq-question")
    
    for idx, q_elem in enumerate(questions):
        try:
            # 질문 위치로 스크롤 후 클릭 (답변 활성화)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", q_elem)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", q_elem)
            time.sleep(0.4)
            
            # 1. 질문 텍스트 추출 (div.faq-question-text)
            try:
                q_text_elem = q_elem.find_element(By.CSS_SELECTOR, "div.faq-question-text")
                question_text = q_text_elem.text.strip()
            except Exception:
                question_text = q_elem.text.strip()
                
            if not question_text:
                continue

            # 2. 답변 텍스트 추출 (div.faq-answer-content)
            # 질문 요소와 연결된 답변 부모 영역 찾기
            try:
                # 질문 상위 요소(faq-item 등) 내의 faq-answer-content 탐색
                parent_item = q_elem.find_element(By.XPATH, "./..")
                answer_elem = parent_item.find_element(By.CSS_SELECTOR, "div.faq-answer-content")
                answer_text = answer_elem.text.strip()
            except Exception:
                # 페이지 전체에서 현재 열린 답변 영역 탐색 (Fallback)
                answers = driver.find_elements(By.CSS_SELECTOR, "div.faq-answer-content")
                if idx < len(answers):
                    answer_text = answers[idx].text.strip()
                else:
                    answer_text = ""

            data_list.append({
                "질문": question_text,
                "답변": answer_text
            })
            
        except Exception as e:
            print(f"    - 항목 수집 중 예외 발생: {e}")

def process_all_pages(driver, data_list):
    """'충전기 사용' 탭 내의 전체 페이지 순회 수집"""
    current_page = 1
    
    while True:
        print(f"  * {current_page}페이지 수집 진행 중...")
        time.sleep(1)
        scrape_current_page(driver, data_list)
        
        next_page_num = current_page + 1
        
        # 페이지네이션 버튼 탐색 (숫자 버튼 또는 다음 페이지 화살표)
        next_page_xpath = f"//div[contains(@class, 'pagination') or contains(@id, 'pagination')]//a[text()='{next_page_num}'] | //button[text()='{next_page_num}']"
        next_links = driver.find_elements(By.XPATH, next_page_xpath)
        
        if next_links and next_links[0].is_displayed():
            next_btn = next_links[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(1.5)
            current_page += 1
        else:
            # 다음 블록 화살표 검사 (예: 'next', '>' 형태의 버튼)
            next_group_xpath = "//a[contains(@class, 'next') or contains(@class, 'btn-next')] | //button[contains(@class, 'next')]"
            next_group_btns = driver.find_elements(By.XPATH, next_group_xpath)
            
            if next_group_btns and next_group_btns[0].is_displayed() and next_group_btns[0].is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_group_btns[0])
                driver.execute_script("arguments[0].click();", next_group_btns[0])
                time.sleep(1.5)
                current_page += 1
            else:
                print(f"  * 마지막 페이지({current_page}p)까지 수집 완수.")
                break

def main():
    target_url = "https://www.gschargev.co.kr/faq.html"
    driver = create_stealth_driver()
    data_list = []

    try:
        print(f"[+] 접속 중: {target_url}")
        driver.get(target_url)
        wait = WebDriverWait(driver, 15)
        time.sleep(2)

        # 1. '충전기 사용' 탭 찾기 및 클릭
        print("[+] '충전기 사용' 탭 탐색 중...")
        tab_xpath = "//div[@id='categoryButtons']//button[contains(@class, 'category-btn') and contains(text(), '충전기 사용')]"
        
        try:
            tab_btn = wait.until(EC.element_to_be_clickable((By.XPATH, tab_xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab_btn)
            driver.execute_script("arguments[0].click();", tab_btn)
            print("[+] '충전기 사용' 탭 클릭 완료")
            time.sleep(2)
        except Exception as e:
            print(f"[오류] '충전기 사용' 탭을 클릭할 수 없습니다: {e}")
            return

        # 2. 전 페이지 데이터 수집 진행
        process_all_pages(driver, data_list)

        # 3. CSV 파일 저장
        if data_list:
            df = pd.DataFrame(data_list)
            df.drop_duplicates(subset=["질문", "답변"], inplace=True)
            
            output_filename = "gschargev_faq_충전기사용.csv"
            df.to_csv(output_filename, index=False, encoding='utf-8-sig')
            print(f"\n[성공] 데이터 수집 및 CSV 저장 완료!")
            print(f"  - 파일명: {output_filename}")
            print(f"  - 총 수집 건수: {len(df)}건")
        else:
            print("\n[경고] 수집된 데이터가 없습니다.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()