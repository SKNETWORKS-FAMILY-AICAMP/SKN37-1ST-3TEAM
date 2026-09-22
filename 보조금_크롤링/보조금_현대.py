import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def create_stealth_driver():
    """스텔스 모드 크롬 드라이버 생성"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def select_dropdown(driver, input_id, target_text):
    """지자체 드롭다운 선택"""
    wait = WebDriverWait(driver, 10)
    input_elem = wait.until(EC.presence_of_element_located((By.ID, input_id)))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", input_elem)
    time.sleep(0.4)

    option_xpath = f"//li[contains(@class, 'el-select-dropdown__item') and contains(., '{target_text}')]"
    option_elem = wait.until(EC.presence_of_element_located((By.XPATH, option_xpath)))
    driver.execute_script("arguments[0].click();", option_elem)
    time.sleep(0.4)

    try:
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except Exception:
        pass
    time.sleep(0.2)

def select_ev_tab(driver):
    """'전기차' 탭 선택"""
    wait = WebDriverWait(driver, 10)
    ev_tab_xpath = "//ul[contains(@class, 'tab-menu__icon-wrapper')]//button[.//span[text()='전기차']]"
    ev_tab_btn = wait.until(EC.presence_of_element_located((By.XPATH, ev_tab_xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", ev_tab_btn)
    time.sleep(0.8)

def open_model_modal(driver):
    """'선택하기' 또는 '변경하기' 팝업 열기"""
    time.sleep(0.4)
    success = driver.execute_script('''
        const buttons = Array.from(document.querySelectorAll('button'));
        const target = buttons.find(btn => {
            const text = (btn.textContent || '').trim();
            const linkName = (btn.getAttribute('data-link-name') || '').trim();
            return text.includes('선택하기') || text.includes('변경하기') || 
                   linkName.includes('선택하기') || linkName.includes('변경하기');
        });
        if (target) {
            target.scrollIntoView({block: 'center'});
            target.click();
            return true;
        }
        return false;
    ''')

    if not success:
        wait = WebDriverWait(driver, 5)
        target_xpath = "//button[contains(., '선택하기') or contains(., '변경하기') or contains(@data-link-name, '선택하기') or contains(@data-link-name, '변경하기')]"
        btn_elem = wait.until(EC.element_to_be_clickable((By.XPATH, target_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", btn_elem)

    time.sleep(0.6)

def select_ev_passenger_category(driver):
    """'전기승용' 카테고리 선택"""
    wait = WebDriverWait(driver, 5)
    tab_xpath = "//ul[contains(@class, 'check-list')]//button[contains(., '전기승용')]"
    tab_btn = wait.until(EC.presence_of_element_located((By.XPATH, tab_xpath)))
    driver.execute_script("arguments[0].click();", tab_btn)
    time.sleep(0.5)

def confirm_and_close_modal(driver):
    """'선택 완료' 클릭 및 팝업 닫기"""
    time.sleep(0.3)
    driver.execute_script('''
        const confirmBtn = document.querySelector('button[data-id="confirm"]') ||
                           Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('선택 완료') || b.textContent.includes('확인'));
        if (confirmBtn) {
            confirmBtn.scrollIntoView({block: 'center'});
            confirmBtn.click();
        }
    ''')
    time.sleep(1.0)  # 메인 페이지 보조금 데이터 반영 대기

def get_exact_subsidy_amount(driver):
    """'보조금 :' 타이틀을 가진 li 태그 내 price만 추출 (보조금_2.png)"""
    try:
        xpath = "//li[.//span[contains(@class, 'title') and contains(text(), '보조금')]]//span[contains(@class, 'price')]"
        elem = driver.find_element(By.XPATH, xpath)
        raw_price = elem.text.strip()
        return raw_price.replace('-', '').strip()
    except Exception:
        return ""

def select_model_by_index(driver, model_idx):
    """모달 내 지정된 model_idx번째 모델 클릭 및 모델명 반환"""
    return driver.execute_script('''
        const idx = arguments[0];
        const modelBtns = Array.from(document.querySelectorAll('div.slide-list.model-list li button, .model-list li button'));
        if (idx >= modelBtns.length) return { success: false, name: "" };

        const targetBtn = modelBtns[idx];
        const modelName = targetBtn.textContent.replace(/\\n/g, ' ').trim();

        // 모델 캐러셀 슬라이드 전환 필요 시
        const modelCarousel = targetBtn.closest('.el-carousel');
        const parentSlide = targetBtn.closest('.el-carousel__item');
        if (modelCarousel && parentSlide && parentSlide.getAttribute('aria-hidden') === 'true') {
            const rightArrow = modelCarousel.querySelector('button.el-carousel__arrow--right');
            let attempts = 0;
            while (rightArrow && parentSlide.getAttribute('aria-hidden') === 'true' && attempts < 5) {
                rightArrow.click();
                attempts++;
            }
        }

        targetBtn.scrollIntoView({block: 'center'});
        targetBtn.click();

        ['mousedown', 'mouseup', 'click'].forEach(eventType => {
            targetBtn.dispatchEvent(new MouseEvent(eventType, { bubbles: true, cancelable: true, view: window }));
        });

        return { success: true, name: modelName };
    ''', model_idx)

def select_trim_by_index(driver, trim_idx):
    """모든 슬라이드의 트림 요소를 수집하여 trim_idx번째 트림 선택"""
    return driver.execute_script('''
        const idx = arguments[0];

        // 1. 모달 전체에서 모든 트림 컨테이너(ul) 수집
        const trimContainers = Array.from(document.querySelectorAll('ul.slide-list.trim-list, ul.trim-list, .trim-list'));
        if (trimContainers.length === 0) return { success: false, name: "", count: 0 };

        // 2. 전체 슬라이드에 걸친 모든 트림 요소 수집
        let allBtns = [];
        trimContainers.forEach(container => {
            const btns = Array.from(container.querySelectorAll('li button'));
            if (btns.length > 0) {
                btns.forEach(b => allBtns.push(b));
            } else {
                const lis = Array.from(container.querySelectorAll('li'));
                lis.forEach(l => allBtns.push(l));
            }
        });

        // 복제(cloned) 요소 제거
        allBtns = allBtns.filter(item => {
            const slide = item.closest('.el-carousel__item');
            return !slide || (!slide.classList.contains('is-cloned') && !slide.classList.contains('el-carousel__item--cloned'));
        });

        if (allBtns.length === 0 || idx >= allBtns.length) {
            return { success: false, name: "", count: allBtns.length };
        }

        const targetItem = allBtns[idx];

        // 3. 트림명 추출
        let trimName = "";
        const optionElem = targetItem.querySelector('.option') || targetItem.querySelector('.name');
        if (optionElem) {
            trimName = optionElem.textContent.replace(/\\n/g, ' ').trim();
        } else {
            trimName = targetItem.textContent.replace(/\\n/g, ' ').trim();
        }

        // 4. 숨겨진 슬라이드에 위치할 경우 트림 전용 캐러셀 오른쪽 화살표 클릭
        const trimCarousel = trimContainers[0].closest('.el-carousel');
        const parentSlide = targetItem.closest('.el-carousel__item');
        if (trimCarousel && parentSlide && (parentSlide.getAttribute('aria-hidden') === 'true' || parentSlide.style.display === 'none')) {
            const rightArrow = trimCarousel.querySelector('button.el-carousel__arrow--right');
            let attempts = 0;
            while (rightArrow && (parentSlide.getAttribute('aria-hidden') === 'true' || parentSlide.style.display === 'none') && attempts < 5) {
                rightArrow.click();
                attempts++;
            }
        }

        // 5. 트림 클릭 및 마우스 이벤트 전송
        targetItem.scrollIntoView({block: 'center'});

        const btn = targetItem.tagName === 'BUTTON' ? targetItem : targetItem.querySelector('button');
        const li = targetItem.tagName === 'LI' ? targetItem : targetItem.closest('li');

        if (btn) btn.click();
        if (li && li !== btn) li.click();

        ['mouseenter', 'mousedown', 'mouseup', 'click'].forEach(eventType => {
            if (btn) btn.dispatchEvent(new MouseEvent(eventType, { bubbles: true, cancelable: true, view: window }));
            if (li && li !== btn) li.dispatchEvent(new MouseEvent(eventType, { bubbles: true, cancelable: true, view: window }));
        });

        return { success: true, name: trimName, count: allBtns.length };
    ''', trim_idx)

def main():
    target_url = "https://www.hyundai.com/kr/ko/e/vehicles/eco-incentive?utm_source=hyundaicom&utm_medium=display&utm_campaign=2023_quickwin&utm_content=gnb"
    driver = create_stealth_driver()
    data_list = []

    try:
        print(f"[+] 페이지 접속: {target_url}")
        driver.get(target_url)
        time.sleep(2.5)

        sido_name = "서울(EV FESTA)"
        sigungu_name = "서울특별시"

        # 1. 지역 선택
        print(f"[1] 시/도: {sido_name} | 시/군/구: {sigungu_name}")
        select_dropdown(driver, "subsidyAreaSelect", sido_name)
        select_dropdown(driver, "subsidyBoroughSelect", sigungu_name)

        # 2. '전기차' 탭 선택
        print("[2] 지급 현황 '전기차' 탭 선택")
        select_ev_tab(driver)

        # 3. 모델 수 파악
        open_model_modal(driver)
        select_ev_passenger_category(driver)

        model_buttons = driver.find_elements(By.CSS_SELECTOR, "div.slide-list.model-list li button, .model-list li button")
        total_models = len(model_buttons)
        print(f"[3] 수집 대상 모델 수: 총 {total_models}개")

        confirm_and_close_modal(driver)

        # 4. 모델 및 트림 순회
        for model_idx in range(total_models):
            # 모델 진입 및 총 트림 수 파악
            open_model_modal(driver)
            select_ev_passenger_category(driver)

            model_res = select_model_by_index(driver, model_idx)
            model_name = model_res.get('name', f"모델_{model_idx+1}")
            time.sleep(0.8)  # Vue 트림 렌더링 대기

            # 트림 개수 구하기
            trim_check = select_trim_by_index(driver, 0)
            total_trims = trim_check.get('count', 1)
            if total_trims == 0:
                total_trims = 1

            confirm_and_close_modal(driver)

            print(f"\n==================================================")
            print(f"▶ [{model_idx + 1}/{total_models}] 모델명: '{model_name}' (총 {total_trims}개 트림)")
            print(f"==================================================")

            # 해당 모델의 모든 트림 순차 수집
            for trim_idx in range(total_trims):
                open_model_modal(driver)
                select_ev_passenger_category(driver)

                # 현재 모델 다시 선택
                select_model_by_index(driver, model_idx)
                time.sleep(0.8)  # Vue 트림 목록 업데이트 대기

                # trim_idx번째 트림 선택
                trim_res = select_trim_by_index(driver, trim_idx)
                trim_name = trim_res.get('name', f"트림_{trim_idx + 1}")

                # '선택 완료' 클릭 후 모달 닫기
                confirm_and_close_modal(driver)

                # 메인 페이지에서 정제된 보조금 추출
                subsidy_price = get_exact_subsidy_amount(driver)

                print(f"   └ [{trim_idx + 1}/{total_trims}] 트림명: {trim_name} | 보조금: {subsidy_price}")

                data_list.append({
                    "시/도": sido_name,
                    "시/군/구": sigungu_name,
                    "모델명": model_name,
                    "트림명": trim_name,
                    "보조금": subsidy_price
                })

        # 5. CSV 저장
        if data_list:
            df = pd.DataFrame(data_list)
            df = df[["시/도", "시/군/구", "모델명", "트림명", "보조금"]]
            df.drop_duplicates(subset=["시/도", "시/군/구", "모델명", "트림명"], inplace=True)
            
            output_file = "hyundai_ev_subsidy_seoul.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n[성공] 데이터 수집 완료! 저장 경로: {output_file} (총 {len(df)}건)")
        else:
            print("\n[경고] 수집된 데이터가 없습니다.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()