import psycopg2
import streamlit as st


# 从你的保险箱里读取云端钥匙
def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


def insert_matchweek_32():
    # 这是我为你整理好的英超第32轮真实赛程（时间已换算为北京时间）
    fixtures = [
        ("西汉姆联", "狼队", "2026-04-11 03:00:00"),
        ("阿森纳", "伯恩茅斯", "2026-04-11 19:30:00"),
        ("布伦特福德", "埃弗顿", "2026-04-11 22:00:00"),
        ("伯恩利", "布莱顿", "2026-04-11 22:00:00"),
        ("利物浦", "富勒姆", "2026-04-12 00:30:00"),
        ("水晶宫", "纽卡斯尔联", "2026-04-12 21:00:00"),
        ("桑德兰", "托特纳姆热刺", "2026-04-12 21:00:00"),
        ("诺丁汉森林", "阿斯顿维拉", "2026-04-12 21:00:00"),
        ("切尔西", "曼城", "2026-04-12 23:30:00"),
        ("曼联", "利兹联", "2026-04-14 03:00:00")
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("🚀 正在向云端数据库发送赛程数据...")
        for home, away, kickoff in fixtures:
            cursor.execute('''
                           INSERT INTO Matches (home_team, away_team, kickoff_time, status)
                           VALUES (%s, %s, %s, '未开赛')
                           ''', (home, away, kickoff))

        # 提交保存
        conn.commit()
        print("✅ 成功！第32轮的 10 场比赛已全部就绪！")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    insert_matchweek_32()