import sqlite3, json, sys, os, subprocess, argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

SCRAPER_BASE = Path(os.getcwd())
load_dotenv(SCRAPER_BASE / ".env")
DB_PATH = SCRAPER_BASE / "tweets.db"

def search_tweets(account, topic, days):
    conn = sqlite3.connect(DB_PATH)
    since_date = (datetime.now() - timedelta(days=days)).isoformat()
    query = "SELECT id, created_at, text FROM tweets WHERE account = ? AND text LIKE ? AND created_at >= ? ORDER BY created_at DESC"
    rows = conn.execute(query, (account, f"%{topic}%", since_date)).fetchall()
    conn.close()
    return rows

def analyze_topic_weighted(topic, tweets):
    tweet_list = [{"id": r[0], "date": r[1], "text": r[2]} for r in tweets]
    prompt = f"""分析關於「{topic}」的推文。\n\n【分析指令】：\n1. **時效性優先**：以最新推文為最高權重。觀察觀點演變。\n2. **結構化摘要**：產出繁體中文專業分析。\n3. **判定情感**：Bullish, Bearish 或 Neutral。\n\n數據：\n{json.dumps(tweet_list, ensure_ascii=False)}\n\n請按此格式結尾：\n---SENTIMENT_JSON---\n{{"id": "sentiment"}}"""
    cmd = ["gemini", "--model", "gemini-2.5-flash-lite", "-p", prompt]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return res.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic")
    parser.add_argument("--account", default="aleabitoreddit")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--output")
    args = parser.parse_args()
    tweets = search_tweets(args.account, args.topic, args.days)
    if not tweets: return
    out = analyze_topic_weighted(args.topic, tweets)
    parts = out.split("---SENTIMENT_JSON---")
    summary = parts[0].strip()
    s_map = {}
    try: s_map = json.loads(parts[1].strip())
    except: pass
    if args.output:
        res = [{"id": r[0], "created_at": r[1], "text": r[2], "sentiment": s_map.get(r[0], "Neutral")} for r in tweets]
        with open(args.output, "w") as f: json.dump({"tweets": res, "summary": summary}, f)

if __name__ == "__main__": main()
