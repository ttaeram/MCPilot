from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import httpx
import os
from dotenv import load_dotenv
from app.review_graph import graph
from app.slack_alert import send_slack_alert

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = FastAPI()

async def fetch_pr_files(files_url: str):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(files_url, headers=headers)
        response.raise_for_status()
        return response.json()

@app.post("/webhook")
async def github_webhook(request: Request):
    headers = request.headers
    body = await request.body()
    event = headers.get("x-github-event")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return JSONResponse(content={"error": "Invalid JSON"}, status_code=400)

    if event == "pull_request":
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})
        files_url = pr.get("url") + "/files"
        pr_url = pr.get("html_url")

        print(f"[Webhook] Pull request {action} on repo {repo.get('full_name')}")

        if action == "opened":
            send_slack_alert("pr_created", pr_url)

        # 파일 목록과 diff 불러오기
        files = await fetch_pr_files(files_url)
        for f in files:
            print(f"\n📄 파일: {f['filename']}")
            diff_text = f.get("patch")
            if not diff_text:
                continue

            result = graph.invoke({"diff": diff_text})
            final_review = result["final_review"]
            print(f"\n📝 최종 리뷰 결과:\n{final_review}")

            send_slack_alert("mcpilot_review_posted", pr_url, review_text=final_review)

            comment_url = pr["comments_url"]
            comment_body = {
                "body": f"### 🤖 코드 리뷰 결과 for `{f['filename']}`\n\n{final_review}"
            }

            async with httpx.AsyncClient() as client:
                comment_response = await client.post(
                    comment_url,
                    headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
                    json=comment_body
                )
                comment_response.raise_for_status()
    
    elif event == "pull_request_review":
        review = payload.get("review", {})
        pr = payload.get("pull_request", {})
        reviewer = review.get("user", {}).get("login")
        review_text = review.get("body")
        pr_url = pr.get("html_url")

        print(f"[Webhook] 사용자 {reviewer}가 PR 리뷰를 작성했습니다.")
        send_slack_alert("user_review_posted", pr_url, reviewer=reviewer, review_text=review_text)

    else:
        print(f"[Webhook] Received non-PR event: {event}")

    return {"status": "ok"}
