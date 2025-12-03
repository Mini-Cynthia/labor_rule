import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json
from datetime import datetime

# 設定環境變數 (在 GitHub Actions 裡設定)
TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 初始化 OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
print 
def fetch_labor_laws():
    """
    範例：爬取勞動部「最新消息」或「法規異動」
    這裡以模擬邏輯為主，實際 URL 需依照勞動部當下改版狀況調整
    """
    # 這是勞動部最新消息的範例網址 (需根據實際狀況替換)
    url = "https://www.mol.gov.tw/1607/1632/1633/lpsimplelist" 
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        # 假設新聞列表在 class="list" 裡面，這部分需要針對目標網站按 F12 觀察
        # 這裡僅為偽代碼邏輯
        for item in soup.select('.list a'):
            title = item.text.strip()
            link = item['href']
            date = item.find_next_sibling('span').text if item.find_next_sibling('span') else ""
            
            # 關鍵字過濾
            if "勞動基準法" in title or "勞基法" in title:
                # 檢查是否為近期的 (例如今天的日期)
                # 這裡為了演示，先全部抓下來
                news_list.append({
                    "title": title,
                    "url": "https://www.mol.gov.tw" + link, # 補全網址
                    "date": date
                })
        return news_list
    except Exception as e:
        print(f"爬蟲錯誤: {e}")
        return []

def analyze_with_gpt(news_item):
    """
    使用 GPT 分析法規內容
    """
    prompt = f"""
    你是台灣勞動法規專家。請分析以下這則關於勞基法的變動通知：
    標題：{news_item['title']}
    連結：{news_item['url']}

    請幫我總結以下資訊 (請用條列式，繁體中文)：
    1. **變動摘要**：簡單說明改了什麼？
    2. **影響對象**：誰會受到影響（雇主/勞工/特定行業）？
    3. **行動建議**：HR 或工程師需要配合做什麼調整嗎？
    """

    response = client.chat.completions.create(
        model="gpt-4o", # 或 gpt-3.5-turbo
        messages=[
            {"role": "system", "content": "你是一個專業的法律分析助手，負責整理法規變更通知。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def send_to_teams(summary, news_item):
    """
    發送 Adaptive Card 或簡單訊息到 Teams
    """
    # 簡單的 JSON 格式
    payload = {
        "title": f"🚨 勞基法規異動警報 - {news_item['date']}",
        "text": f"### [{news_item['title']}]({news_item['url']})\n\n{summary}"
    }
    
    headers = {'Content-Type': 'application/json'}
    print "test teams"
    print(f"payload: {data}") 
    print(f"TEAMS_WEBHOOK_URL: {TEAMS_WEBHOOK_URL}") 
    print requests.post(TEAMS_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
    response = requests.post(TEAMS_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
    
    if response.status_code == 200:
        print("訊息發送成功")
    else:
        print(f"訊息發送失敗: {response.status_code}")

def main():
    print("開始檢查法規變動...")
    news_items = fetch_labor_laws()
    
    if not news_items:
        print("今日無相關法規變動。")
        return

    # 為了避免重複發送，實際專案通常會記錄「已發送過的清單」在一個檔案或資料庫
    # 這裡假設每次都分析最新的第一筆
    latest_news = news_items[0] 
    
    print(f"發現新聞: {latest_news['title']}")
    analysis = analyze_with_gpt(latest_news)
    send_to_teams(analysis, latest_news)

if __name__ == "__main__":
    main()
