import sys
import time
from datetime import datetime, timedelta

from requests import post, Response
from playwright.sync_api import Playwright, sync_playwright

RUN_FILE_NAME = sys.argv[0]

# 동행복권 아이디와 패스워드를 설정
USER_ID = sys.argv[1]
USER_PW = sys.argv[2]

# SLACK 설정
SLACK_API_URL = "https://slack.com/api/chat.postMessage"
SLACK_BOT_TOKEN = sys.argv[3]
SLACK_CHANNEL = sys.argv[4]


def hook_slack(message: str) -> Response:
    now_utc = datetime.utcnow()
    korea_timezone = timedelta(hours=9)
    now_korea = now_utc + korea_timezone
    korea_time_str = now_korea.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "text": f"> {korea_time_str} *로또 자동 구매 봇 알림* \n {message}",
        "channel": SLACK_CHANNEL,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    }
    res = post(SLACK_API_URL, json=payload, headers=headers)
    return res


def run(playwright: Playwright) -> None:
    try:
        browser = playwright.chromium.launch(headless=True)  # chrome 브라우저를 실행
        context = browser.new_context()

        page = context.new_page()
        page.goto("https://dhlottery.co.kr/user.do?method=login")
        page.click('[placeholder="아이디"]')
        page.fill('[placeholder="아이디"]', USER_ID)
        page.press('[placeholder="아이디"]', "Tab")
        page.fill('[placeholder="비밀번호"]', USER_PW)
        page.press('[placeholder="비밀번호"]', "Tab")

        # Press Enter
        # with page.expect_navigation(url="https://ol.dhlottery.co.kr/olotto/game/game645.do"):
        with page.expect_navigation():
            page.press('form[name="jform"] >> text=로그인', "Enter")

        time.sleep(5)

        # 당첨 결과 및 번호 확인
        page.goto("https://dhlottery.co.kr/common.do?method=main")
        result_info = page.query_selector("#article div.content").inner_text()
        result_info = result_info.split("이전")[0].replace("\n", " ")
        hook_slack(f"로또 결과: {result_info}")

        # End of Selenium
        context.close()
        browser.close()
    except Exception as exc:
        hook_slack(exc)
        context.close()
        browser.close()
        raise exc


with sync_playwright() as playwright:
    run(playwright)