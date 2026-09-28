import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def create_stealth_driver():
    """봇 탐지 우회 및 데스크톱 해상도가 고정된 Chrome Driver 생성"""
    options = Options()
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    return driver

def find_main_tabs(driver):
    """메인 탭 요소들을 유연하게 탐색"""
    candidate_xpaths = [
        "//div[contains(@class, 'cmp-faq-search-tab')]//ul[not(contains(@class, 'sub'))]/li/*[self::button or self::a]",
        "//div[contains(@class, 'cmp-faq-search-tab')]//button[contains(@class, 'btn') and not(contains(@class, 'sub'))]",
        "//button[contains(@class, 'cmp-faq-search-tab') and not(contains(@class, 'sub'))]",
        "//div[contains(@class, 'cmp-tabs')]//button"
    ]
    
    for xpath in candidate_xpaths:
        elements = driver.find_elements(By.XPATH, xpath)
        valid_elements = [
            e for e in elements 
            if e.is_displayed() 
            and e.text.strip() 
            and "sub" not in (e.get_attribute("class") or "").lower()
        ]
        if valid_elements:
            return valid_elements
            
    all_buttons = driver.find_elements(By.XPATH, "//button | //a")
    fallback = []
    for btn in all_buttons:
        cls = btn.get_attribute("class") or ""
        text = btn.text.strip()
        if btn.is_displayed() and text and ("tab" in cls.lower() or "faq" in cls.lower()) and "sub" not in cls.lower():
            fallback.append(btn)
    return fallback

def scrape_current_page_faqs(driver, data_list):
    """현재 페이지의 질문과 답변 추출"""
    question_buttons = driver.find_elements(By.CSS_SELECTOR, "button.cmp-accordion__button, button[class*='accordion__button']")
    
    for btn in question_buttons:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.2)
            
            # 질문 추출
            try:
                title_elem = btn.find_element(By.CSS_SELECTOR, "span.cmp-accordion__title, [class*='accordion__title']")
                question_text = title_elem.text.strip()
            except Exception:
                question_text = btn.text.strip()
            
            if not question_text:
                continue

            panel_id = btn.get_attribute("aria-controls")
            expanded = btn.get_attribute("aria-expanded")
            
            # 아코디언 펼치기
            if expanded != "true":
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.3)
            
            # 답변 추출
            if panel_id:
                try:
                    panel_elem = driver.find_element(By.ID, panel_id)
                    answer_text = panel_elem.text.strip()
                except Exception:
                    answer_text = ""
            else:
                answer_text = ""
                
            data_list.append({
                "질문": question_text,
                "답변": answer_text
            })
        except Exception:
            pass

def process_all_pages(driver, data_list):
    """현재 선택된 탭 영역 내 모든 페이지 순회"""
    current_page = 1
    
    while True:
        time.sleep(1)
        scrape_current_page_faqs(driver, data_list)
        
        next_page_num = current_page + 1
        page_xpath = f"//div[contains(@class, 'cmp-pagination')]//ul[contains(@class, 'paging-list')]//a[text()='{next_page_num}'] | //ul[contains(@class, 'paging-list')]//a[text()='{next_page_num}']"
        next_links = driver.find_elements(By.XPATH, page_xpath)
        
        if next_links:
            next_btn = next_links[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(1.5)
            current_page += 1
        else:
            # 그룹 이동 화살표 검사
            next_group = driver.find_elements(By.XPATH, "//a[contains(@class, 'cmp-pagination__btn--next') or contains(@class, 'paging-next')]")
            if next_group and next_group[0].is_enabled() and next_group[0].is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_group[0])
                driver.execute_script("arguments[0].click();", next_group[0])
                time.sleep(1.5)
                current_page += 1
            else:
                print(f"    - 마지막 페이지({current_page}p)까지 수집 완료")
                break

def click_tab_and_scrape(driver, main_tab_keyword, sub_tab_keyword, target_data_list):
    """지정한 메인 탭과 하위 탭으로 이동하여 수집 진행"""
    main_tabs = find_main_tabs(driver)
    
    target_main_btn = None
    for mt in main_tabs:
        if main_tab_keyword in mt.text.strip():
            target_main_btn = mt
            break
            
    if not target_main_btn:
        print(f"[오류] '{main_tab_keyword}' 메인 탭을 찾을 수 없습니다.")
        return False

    print(f"\n==========================================")
    print(f"[+] '{main_tab_keyword}' > '{sub_tab_keyword}' 탭 수집 시작")
    print(f"==========================================")
    
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_main_btn)
    driver.execute_script("arguments[0].click();", target_main_btn)
    time.sleep(2)

    # 하위 탭 검색
    sub_xpath = "//div[contains(@class, 'cmp-faq-search-tab__sub')]//button[contains(@class, 'cmp-faq-search-tab__sub-btn')] | //ul[contains(@class, 'cmp-faq-search-tab__sub-list')]//button"
    sub_tabs = [st for st in driver.find_elements(By.XPATH, sub_xpath) if st.is_displayed() and st.text.strip()]

    if sub_tabs:
        sub_found = False
        for sub_btn in sub_tabs:
            sub_name = sub_btn.text.strip()
            if sub_tab_keyword in sub_name:
                print(f"  - [{main_tab_keyword} > {sub_name}] 하위 탭 진입")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sub_btn)
                driver.execute_script("arguments[0].click();", sub_btn)
                time.sleep(1.5)
                
                process_all_pages(driver, target_data_list)
                sub_found = True
                break
                
        if not sub_found:
            print(f"  - [경고] '{sub_tab_keyword}' 하위 탭을 찾지 못했습니다.")
            return False
    else:
        process_all_pages(driver, target_data_list)
        
    return True

def main():
    target_url = "https://www.kia.com/kr/customer-service/center/faq"
    driver = create_stealth_driver()

    try:
        print(f"[+] 페이지 접속 중: {target_url}")
        driver.get(target_url)
        
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 400);")
        time.sleep(1)

        # ---------------------------------------------------------
        # 1. '차량 정비' - '전체' 수집 및 '전기차' 키워드 분리
        # ---------------------------------------------------------
        car_maint_raw = []
        click_tab_and_scrape(driver, "차량 정비", "전체", car_maint_raw)

        car_maint_normal = []  # 전기차가 포함되지 않은 일반 차량 정비 데이터
        car_maint_ev = []      # '전기차' 키워드가 들어간 차량 정비 데이터

        for item in car_maint_raw:
            # 질문 또는 답변에 '전기차' 포함 여부 검사
            if "전기차" in item["질문"] or "전기차" in item["답변"]:
                car_maint_ev.append(item)
            else:
                car_maint_normal.append(item)

        print(f"  * 차량 정비(전체) 분류 결과:")
        print(f"    - 일반 차량 정비 데이터: {len(car_maint_normal)}건")
        print(f"    - '전기차' 관련 정비 데이터: {len(car_maint_ev)}건")

        # ---------------------------------------------------------
        # 2. '기타' - '충전' 수집
        # ---------------------------------------------------------
        charging_raw = []
        click_tab_and_scrape(driver, "기타", "충전", charging_raw)

        # ---------------------------------------------------------
        # 3. CSV 파일 별도 저장 처리
        # ---------------------------------------------------------
        # CSV 1: 차량 정비(전체) - 일반 데이터
        if car_maint_normal:
            df_normal = pd.DataFrame(car_maint_normal)
            df_normal.drop_duplicates(subset=["질문", "답변"], inplace=True)
            file_normal = "kia_faq_차량정비_전체_일반.csv"
            df_normal.to_csv(file_normal, index=False, encoding='utf-8-sig')
            print(f"\n[성공] '{file_normal}' 저장 완료 (총 {len(df_normal)}건)")

        # CSV 2: 기타(충전) + 차량 정비(전기차) 통합 데이터
        combined_data = charging_raw + car_maint_ev
        if combined_data:
            df_combined = pd.DataFrame(combined_data)
            df_combined.drop_duplicates(subset=["질문", "답변"], inplace=True)
            file_combined = "kia_faq_기타충전_및_전기차정비.csv"
            df_combined.to_csv(file_combined, index=False, encoding='utf-8-sig')
            print(f"[성공] '{file_combined}' 저장 완료 (총 {len(df_combined)}건 - 기타(충전): {len(charging_raw)}건 + 전기차정비: {len(car_maint_ev)}건)")

        print("\n[+] 모든 요청 조건에 따른 추출 및 저장 작업이 완료되었습니다.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()