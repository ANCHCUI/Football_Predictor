import psycopg2
import requests
import streamlit as st
from core_logic import calculate_score

# 你的专属 API 钥匙（请把邮箱里收到的 Token 填到这里！）
API_KEY = "9714b4df7d01485489057432a0f352d3"

# 🇬🇧 核心翻译官：把 API 的英文队名翻译成我们数据库里的中文
TEAM_TRANSLATOR = {
    "Arsenal FC": "阿森纳", "Aston Villa FC": "阿斯顿维拉", "AFC Bournemouth": "伯恩茅斯",
    "Brentford FC": "布伦特福德", "Brighton & Hove Albion FC": "布莱顿", "Burnley FC": "伯恩利",
    "Chelsea FC": "切尔西", "Crystal Palace FC": "水晶宫", "Everton FC": "埃弗顿",
    "Fulham FC": "富勒姆", "Leeds United FC": "利兹联", "Liverpool FC": "利物浦",
    "Manchester City FC": "曼城", "Manchester United FC": "曼联", "Newcastle United FC": "纽卡斯尔联",
    "Nottingham Forest FC": "诺丁汉森林", "Sunderland AFC": "桑德兰", "Tottenham Hotspur FC": "托特纳姆热刺",
    "West Ham United FC": "西汉姆联", "Wolverhampton Wanderers FC": "狼队"
}


def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def fetch_finished_matches():
    """向 API 发送请求，获取英超最近刚踢完的比赛比分"""
    print("📡 正在呼叫英超数据中心 API...")
    url = "https://api.football-data.org/v4/competitions/PL/matches?status=FINISHED"
    headers = {"X-Auth-Token": API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ API 请求失败！错误码: {response.status_code}")
        return []

    # 提取比赛数据
    matches = response.json().get('matches', [])
    finished_results = {}

    for match in matches:
        eng_home = match['homeTeam']['name']
        eng_away = match['awayTeam']['name']

        # 将英文翻译成中文
        cn_home = TEAM_TRANSLATOR.get(eng_home, eng_home)
        cn_away = TEAM_TRANSLATOR.get(eng_away, eng_away)

        # 提取全场比分
        score_home = match['score']['fullTime']['home']
        score_away = match['score']['fullTime']['away']

        # 用 "主队_客队" 作为字典的钥匙，存下比分
        match_key = f"{cn_home}_{cn_away}"
        finished_results[match_key] = (score_home, score_away)

    return finished_results


def run_auto_settlement():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 查出我们数据库里所有还在“未开赛”状态的比赛
    cursor.execute("SELECT id, home_team, away_team FROM Matches WHERE status='未开赛'")
    pending_matches = cursor.fetchall()

    if not pending_matches:
        print("🎉 数据库中目前没有需要结算的比赛。")
        return

    # 2. 从外部 API 获取真实比分数据
    real_scores = fetch_finished_matches()
    if not real_scores:
        return

    print("\n" + "=" * 50)
    print("🤖 自动结算引擎启动，正在核对现实赛果...")
    print("=" * 50)

    settlement_count = 0

    try:
        # 3. 循环比对：看看我们数据库里的比赛，是不是在现实中已经踢完了
        for match_id, home, away in pending_matches:
            match_key = f"{home}_{away}"

            # 如果这场比赛的中文名在 API 返回的完赛列表里找到了！
            if match_key in real_scores:
                actual_home, actual_away = real_scores[match_key]
                print(f"✅ 捕获到完赛比分: {home} {actual_home} - {actual_away} {away}")

                # 更新 Matches 表状态
                cursor.execute("UPDATE Matches SET home_score=%s, away_score=%s, status='已结束' WHERE id=%s",
                               (actual_home, actual_away, match_id))

                # 抓取用户预测并算分
                cursor.execute("SELECT user_id, predicted_home, predicted_away FROM Predictions WHERE match_id=%s",
                               (match_id,))
                predictions = cursor.fetchall()

                for user_id, pred_h, pred_a in predictions:
                    points_earned = calculate_score(actual_home, actual_away, pred_h, pred_a)
                    cursor.execute("UPDATE Users SET total_points = total_points + %s WHERE id=%s",
                                   (points_earned, user_id))
                    print(f"   💸 用户ID [{user_id}] 预测 {pred_h}:{pred_a}，进账 {points_earned} 分！")

                settlement_count += 1

        # 4. 全部循环结束后，一次性提交保存到云端
        conn.commit()
        print(f"\n🎉 报告老板：本次自动化运行完毕，共自动结算了 {settlement_count} 场比赛！")

    except Exception as e:
        conn.rollback()
        print(f"❌ 自动结算发生严重错误，已启动数据保护回滚机制。报错信息: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_auto_settlement()