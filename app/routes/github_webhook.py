from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.services.review_service import review_diff_concurrently, fetch_pr_files
from app.slack_alert import send_slack_alert
import os, json, httpx

router = APIRouter()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

@router.post("")
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

        files = await fetch_pr_files(files_url)
        for f in files:
            print(f"\n📄 파일: {f['filename']}")
            diff_text = f.get("patch")
            if not diff_text:
                continue

            state = await review_diff_concurrently(diff_text)
            final_review = state["final_review"]
            print(f"\n📝 최종 리뷰 결과:\n{final_review}")

            send_slack_alert("mcpilot_review_posted", pr_url, review_text=final_review)

            comment_url = pr["comments_url"]
            comment_body = {
                "body": f"### 🤖 코드 리뷰 결과 for `{f['filename']}`\n\n{final_review}"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    comment_url,
                    headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
                    json=comment_body
                )
                response.raise_for_status()

    elif event == "pull_request_review":
        reviewer = payload.get("review", {}).get("user", {}).get("login")
        pr_url = payload.get("pull_request", {}).get("html_url")
        review_text = payload.get("review", {}).get("body")

        print(f"[Webhook] 사용자 {reviewer}가 PR 리뷰를 작성했습니다.")
        send_slack_alert("user_review_posted", pr_url, reviewer=reviewer, review_text=review_text)

    return {"status": "ok"}
