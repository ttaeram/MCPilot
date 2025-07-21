import os
from dotenv import load_dotenv
import requests

load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_slack_alert(event_type: str, pr_url: str, reviewer: str = None, review_text: str = None):
    if event_type == "pr_created":
        title = "📌 새로운 PR이 생성되었습니다!"
        text = f"<{pr_url}|PR 보러 가기>"

    elif event_type == "mcpilot_review_posted":
        title = "🤖 MCPilot이 코드 리뷰를 완료했습니다"
        summary = (review_text[:500] + "...") if review_text and len(review_text) > 500 else review_text
        text = f"*리뷰 요약:*\n{summary}\n\n<{pr_url}|PR 보러 가기>"

    elif event_type == "user_review_posted":
        title = f"🧑‍💻 {reviewer}님이 PR에 리뷰를 남겼습니다"
        summary = (review_text[:500] + "...") if review_text and len(review_text) > 500 else review_text
        text = f"*리뷰 요약:*\n{summary}\n\n<{pr_url}|PR 보러 가기>"

    else:
        return

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            }
        ]
    }

    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print(f"Slack 응답 코드: {response.status_code}")
    print(f"Slack 응답 내용: {response.text}")
    response.raise_for_status()
