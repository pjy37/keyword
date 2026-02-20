"""네이버 검색광고 키워드 도구에서 인구통계 차트를 스크래핑한다.

Playwright를 사용하여 네이버 로그인 → 검색광고 → 키워드 도구 → 차트 캡처.
사용자 제공 검증 코드 기반.
로그인 입력은 macOS osascript를 사용하여 실제 키보드 입력으로 처리 (봇 감지 우회).
"""
import asyncio
import os
import subprocess
import traceback
from io import BytesIO

from PIL import Image


def _type_with_applescript(text):
    """macOS AppleScript로 실제 키보드 타이핑한다. (봇 감지 완전 우회)"""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    script = 'tell application "System Events" to keystroke "{}"'.format(escaped)
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)


def _cmd_v_with_applescript():
    """macOS AppleScript로 Cmd+V 붙여넣기한다."""
    script = 'tell application "System Events" to keystroke "v" using command down'
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)


def _cmd_a_with_applescript():
    """macOS AppleScript로 Cmd+A 전체선택한다."""
    script = 'tell application "System Events" to keystroke "a" using command down'
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)


def _set_clipboard(text):
    """macOS pbcopy로 클립보드에 텍스트를 설정한다."""
    process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    process.communicate(text.encode("utf-8"))


def _press_delete_with_applescript():
    """macOS AppleScript로 Delete 키를 누른다."""
    script = 'tell application "System Events" to key code 51'
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)


def _press_tab_with_applescript():
    """macOS AppleScript로 Tab 키를 누른다."""
    script = 'tell application "System Events" to key code 48'
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


async def _scrape_keyword_charts(keyword, naver_id, naver_pw, num_keywords=3, progress_callback=None):
    """네이버 검색광고 키워드 도구에서 차트를 스크래핑한다."""
    from playwright.async_api import async_playwright

    def log(msg):
        if progress_callback:
            progress_callback(msg)

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. 네이버 광고 사이트 접속
            log("1. 네이버 광고 사이트 접속...")
            await page.goto("https://ads.naver.com/")
            await page.wait_for_load_state("networkidle")

            # 2. 팝업 처리
            log("2. 팝업 처리 중...")
            for _ in range(3):
                try:
                    popup_selector = "button.Button_btn___t8GZ.primary"
                    await page.wait_for_selector(popup_selector, timeout=2000)
                    await page.click(popup_selector)
                    await asyncio.sleep(0.5)
                except Exception:
                    break

            # 모든 종류의 팝업/오버레이 닫기
            await page.evaluate("""
                () => {
                    // 닫기/확인/X 버튼 클릭
                    const btns = document.querySelectorAll('button, a');
                    for (let b of btns) {
                        const t = b.textContent.trim();
                        if ((t === '닫기' || t === '확인' || t === '다음에 하기'
                             || t === '건너뛰기' || t === 'X')
                            && b.offsetParent !== null) {
                            b.click();
                        }
                    }
                    // close 버튼
                    document.querySelectorAll(
                        'button.close, [aria-label="Close"], [aria-label="닫기"], button[class*="close"]'
                    ).forEach(b => { if (b.offsetParent !== null) b.click(); });
                }
            """)
            await asyncio.sleep(1)

            # 3. 로그인 여부 확인
            log("3. 로그인 상태 확인...")
            login_btn = await page.query_selector("a.AccountBox_login__No4av")
            need_login = False
            if login_btn:
                btn_text = await login_btn.text_content()
                if "로그인" in (btn_text or ""):
                    need_login = True

            if need_login:
                # 로그인 필요 — 로그인 버튼 클릭
                log("   로그인 필요. 로그인 버튼 클릭...")
                await page.click("a.AccountBox_login__No4av")
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(1)

                # 4. 아이디 입력 (macOS osascript — 실제 키보드 입력으로 봇 감지 완전 우회)
                log("4. 로그인 정보 입력 (OS 키보드 방식)...")
                await page.click("#id")
                await asyncio.sleep(0.3)

                # Cmd+A → Delete로 기존 내용 지우기
                _cmd_a_with_applescript()
                await asyncio.sleep(0.1)
                _press_delete_with_applescript()
                await asyncio.sleep(0.1)

                # pbcopy + Cmd+V로 아이디 붙여넣기
                _set_clipboard(naver_id)
                await asyncio.sleep(0.1)
                _cmd_v_with_applescript()
                await asyncio.sleep(0.5)

                # 5. 비밀번호 입력 (OS 키보드)
                await page.click("#pw")
                await asyncio.sleep(0.3)

                _cmd_a_with_applescript()
                await asyncio.sleep(0.1)
                _press_delete_with_applescript()
                await asyncio.sleep(0.1)

                _set_clipboard(naver_pw)
                await asyncio.sleep(0.1)
                _cmd_v_with_applescript()
                await asyncio.sleep(0.5)

                # 6. 로그인 버튼 클릭
                log("5. 로그인 중...")
                await page.click("#log\\.login")

                log("   로그인 처리 대기 중 (15초)...")
                await asyncio.sleep(15)
                await page.wait_for_load_state("networkidle")

                # 로그인 후 팝업 처리
                log("6. 로그인 후 팝업 처리...")
                for i in range(3):
                    try:
                        popup_selector = "button.Button_btn___t8GZ.primary"
                        await page.wait_for_selector(popup_selector, timeout=2000)
                        await page.click(popup_selector)
                        log("   팝업 {} 닫기 완료".format(i + 1))
                        await asyncio.sleep(0.5)
                    except Exception:
                        break

            else:
                log("   이미 로그인되어 있습니다. 로그인 건너뜀.")

            # 8. 광고 플랫폼 버튼 클릭
            log("7. 광고 플랫폼 메뉴 클릭...")
            await page.click(
                "#header > div > div > div > section > "
                "div.PlatformBox_btn_platform_box__CgdxY."
                "PlatformBox_header_responsive__wUiWz."
                "PlatformBox_userProfile__w4ler."
                "PlatformBox_sticky__c3QNi > a"
            )
            await asyncio.sleep(1)

            # 9. 검색 광고 버튼 클릭 (새 탭 열림 감지)
            log("8. 검색 광고 선택 (새 탭 감지)...")

            async with context.expect_page() as new_page_info:
                await page.click(
                    "#header > div > div > div > section > "
                    "div.PlatformBox_btn_platform_box__CgdxY."
                    "PlatformBox_header_responsive__wUiWz."
                    "PlatformBox_userProfile__w4ler."
                    "PlatformBox_sticky__c3QNi."
                    "PlatformBox_on__t6H_v > ul > li:nth-child(1) > a"
                )
                log("   검색 광고 클릭, 새 탭 대기 중...")

            new_page = await new_page_info.value
            log("   새 탭 열림: {}".format(new_page.url))

            page = new_page
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            current_url = page.url
            log("   현재 URL: {}".format(current_url))

            # 10. 광고 계정 선택
            log("9. 광고 계정 선택...")

            if "searchad.naver.com/membership/select-account" in current_url:
                log("   계정 선택 페이지 진입")

                await asyncio.sleep(8)
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_load_state("networkidle")

                try:
                    result_acc = await page.evaluate("""
                        () => {
                            const marvelRoot = document.querySelector('marvel-root');
                            if (!marvelRoot) return {success: false, message: 'marvel-root not found'};

                            const scrollWrap = marvelRoot.querySelector('.scroll-wrap.text-body');
                            if (!scrollWrap) return {success: false, message: 'scroll-wrap not found'};

                            const links = scrollWrap.querySelectorAll('a');
                            if (links.length === 0) return {success: false, message: 'no links found'};

                            const firstLink = links[0];
                            const accountName = firstLink.textContent.trim();
                            firstLink.click();

                            return {success: true, accountName: accountName, linkCount: links.length};
                        }
                    """)

                    if result_acc["success"]:
                        log("   계정 선택: {}".format(result_acc["accountName"]))
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(5)
                    else:
                        log("   계정 선택 실패: {}".format(result_acc["message"]))
                        raise Exception("광고 계정을 자동 선택할 수 없습니다: " + result_acc["message"])

                except Exception as e:
                    if "자동 선택" in str(e):
                        raise
                    log("   계정 선택 오류: {}".format(e))
                    raise Exception("광고 계정 선택 오류: " + str(e))

            elif "manage.searchad.naver.com/customers" in current_url:
                log("   이미 대시보드에 진입되어 있습니다.")
            else:
                log("   계정 선택 화면이 나타나지 않았습니다. URL: {}".format(current_url))

            final_url = page.url
            log("   최종 URL: {}".format(final_url))

            if "manage.searchad.naver.com/customers" not in final_url:
                raise Exception("campaigns 페이지로 이동 실패. URL: " + final_url)

            log("   campaigns 페이지 도달")

            # 11. 도구 메뉴 클릭
            log("10. 도구 메뉴 클릭...")
            await page.click(
                "#root > div.sc-jwrfVR.jiHXTj > div.header > div > "
                "div:nth-child(1) > div.header-second-row > div > div > "
                "div:nth-child(1) > ul > li:nth-child(4) > div > a"
            )
            await asyncio.sleep(1)

            # 12. 키워드 도구 클릭
            log("11. 키워드 도구 클릭...")
            keyword_tool_clicked = False

            selectors_to_try = [
                "#root > div.sc-jwrfVR.jiHXTj > div.header > div > "
                "div:nth-child(1) > div.header-second-row > div > div > "
                "div:nth-child(1) > ul > li.nav-item.active > div > div > "
                "div:nth-child(5) > a > button",

                "#root > div.sc-jwrfVR.jiHXTj > div.header > div > "
                "div:nth-child(1) > div.header-second-row > div > div > "
                "div:nth-child(1) > ul > li.nav-item.active > div > div > "
                "div:nth-child(5) > a > button > span",

                "#root > div.sc-jwrfVR.jiHXTj > div.header > div > "
                "div:nth-child(1) > div.header-second-row > div > div > "
                "div:nth-child(1) > ul > li.nav-item.active > div > div > "
                "div:nth-child(5) > a",
            ]

            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.click(selector)
                    log("   키워드 도구 클릭 성공")
                    keyword_tool_clicked = True
                    break
                except Exception:
                    continue

            if not keyword_tool_clicked:
                await page.evaluate("""
                    () => {
                        const buttons = document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if (btn.textContent.includes('키워드')) {
                                btn.click();
                                return;
                            }
                        }
                    }
                """)
                log("   JavaScript로 키워드 도구 클릭 완료")

            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # 13. 키워드 입력
            log("12. 키워드 '{}' 입력...".format(keyword))

            try:
                await page.wait_for_selector("#keyword-hint", timeout=5000)
                await page.click("#keyword-hint")
                await page.fill("#keyword-hint", keyword)
                log("   키워드 입력 완료")
            except Exception:
                await page.evaluate(
                    """(kw) => {
                        const input = document.querySelector('#keyword-hint');
                        if (input) {
                            input.value = kw;
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    }""",
                    keyword,
                )
                log("   JavaScript로 입력 완료")

            await asyncio.sleep(1)

            # 14. 조회하기 버튼 클릭
            log("13. 조회하기 클릭...")
            search_button_selector = (
                "#root > div.sc-jwrfVR.jiHXTj > div.sc-goWbiw.hgIphO > div > div > "
                "div.row > div.col-sm-9.col-keyword-query > div:nth-child(1) > "
                "div.card-footer > button"
            )

            try:
                await page.wait_for_selector(search_button_selector, timeout=5000)
                await page.click(search_button_selector)
                log("   조회하기 버튼 클릭 완료")
            except Exception:
                await page.evaluate("""
                    () => {
                        const buttons = document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if (btn.textContent.includes('조회')) {
                                btn.click();
                                return;
                            }
                        }
                    }
                """)
                log("   JavaScript로 조회하기 클릭 완료")

            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # 15~20. 각 키워드 차트 캡처
            for keyword_num in range(1, num_keywords + 1):
                keyword_label = "{}번째".format(keyword_num)
                log("{} 키워드 클릭...".format(keyword_label))

                keyword_selector = (
                    "#root > div.sc-jwrfVR.jiHXTj > div.sc-goWbiw.hgIphO > div > div > "
                    "div.row > div.col-sm-9.col-keyword-query > div:nth-child(2) > "
                    "div.card-body > div > div.sc-dlWCHZ.taunU > table > tbody > "
                    "tr:nth-child({}) > td:nth-child(2) > div > span".format(keyword_num)
                )

                kw_name = ""
                try:
                    el = await page.wait_for_selector(keyword_selector, timeout=5000)
                    kw_name = (await el.text_content() or "").strip()
                    await page.click(keyword_selector)
                    log("   {} 키워드 '{}' 클릭 성공".format(keyword_label, kw_name))
                except Exception:
                    try:
                        kw_name = await page.evaluate(
                            """(num) => {
                                const table = document.querySelector('table tbody');
                                if (table) {
                                    const row = table.querySelector(
                                        'tr:nth-child(' + num + ') td:nth-child(2) div span');
                                    if (row) { row.click(); return row.textContent.trim(); }
                                }
                                return '';
                            }""",
                            keyword_num,
                        )
                        log("   JavaScript로 클릭 완료")
                    except Exception:
                        log("   {} 키워드를 찾을 수 없습니다.".format(keyword_label))
                        continue

                if not kw_name:
                    kw_name = "keyword_{}".format(keyword_num)

                # 모달 캡처
                try:
                    log("   모달 스크린샷 캡처 시도...")

                    modal_selector = "div.modal.fade.show"
                    await page.wait_for_selector(modal_selector, timeout=5000, state="visible")
                    await asyncio.sleep(2)

                    # 모달 바디에 포커스, 스크롤 맨 위로
                    await page.evaluate("""
                        () => {
                            const modal = document.querySelector('div.modal.fade.show');
                            if (modal) {
                                const modalBody = modal.querySelector('.modal-body');
                                if (modalBody) {
                                    modalBody.focus();
                                    modalBody.scrollTop = 0;
                                }
                            }
                        }
                    """)
                    await asyncio.sleep(1)

                    # 위쪽 차트 캡처
                    top_bytes = await page.screenshot(full_page=False)
                    top_image = Image.open(BytesIO(top_bytes))

                    # PageDown 후 아래쪽 캡처
                    await page.keyboard.press("PageDown")
                    await asyncio.sleep(1)

                    middle_bytes = await page.screenshot(full_page=False)
                    middle_image = Image.open(BytesIO(middle_bytes))

                    # 두 이미지 합치기 (중복 30% 제거)
                    overlap_remove = int(middle_image.height * 0.3)
                    middle_cropped = middle_image.crop(
                        (0, overlap_remove, middle_image.width, middle_image.height)
                    )

                    total_height = top_image.height + middle_cropped.height
                    total_width = max(top_image.width, middle_image.width)

                    combined_image = Image.new("RGB", (total_width, total_height), color="white")
                    combined_image.paste(top_image, (0, 0))
                    combined_image.paste(middle_cropped, (0, top_image.height))

                    # 저장
                    safe_name = kw_name.replace("/", "_").replace(" ", "_")
                    img_path = os.path.join(
                        SCREENSHOT_DIR,
                        "chart_{}_{}.png".format(safe_name, keyword_num),
                    )
                    combined_image.save(img_path)

                    results.append({"keyword": kw_name, "image_path": img_path})
                    log("   스크린샷 저장: {} ({}x{}px)".format(
                        kw_name, combined_image.width, combined_image.height
                    ))

                except Exception as e:
                    log("   {} 키워드 모달 캡처 실패: {}".format(keyword_label, e))

                # 팝업 닫기
                log("   {} 키워드 팝업 닫는 중...".format(keyword_label))
                try:
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1)

                    modal_visible = await page.is_visible("div.modal.fade.show")
                    if not modal_visible:
                        log("   {} 키워드 팝업 닫기 완료".format(keyword_label))
                    else:
                        try:
                            await page.click(".modal.fade.show .close")
                            log("   X 버튼으로 닫기 완료")
                        except Exception:
                            log("   X 버튼 찾기 실패")

                    await asyncio.sleep(1)

                except Exception as e:
                    log("   팝업 닫기 실패: {}".format(e))

            log("모든 작업 완료! ({}개 차트 캡처)".format(len(results)))

        except Exception as e:
            log("오류 발생: {}".format(e))
            err_path = os.path.join(SCREENSHOT_DIR, "error_screenshot.png")
            try:
                await page.screenshot(path=err_path, full_page=True)
                log("오류 스크린샷 저장됨")
            except Exception:
                pass
            raise

        finally:
            await browser.close()

    return results


def scrape_keyword_charts(keyword, naver_id, naver_pw, num_keywords=3, progress_callback=None):
    """동기 래퍼: Playwright 비동기 함수를 동기적으로 실행한다."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            _scrape_keyword_charts(keyword, naver_id, naver_pw, num_keywords, progress_callback)
        )
    finally:
        loop.close()
