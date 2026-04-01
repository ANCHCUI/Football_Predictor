import psycopg2
import streamlit as st

# 从保险箱读取云端连接密码
def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # PostgreSQL 的自增 ID 用 SERIAL
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            total_points REAL DEFAULT 0.0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Matches (
            id SERIAL PRIMARY KEY,
            home_team VARCHAR(50) NOT NULL,
            away_team VARCHAR(50) NOT NULL,
            kickoff_time TIMESTAMP NOT NULL,
            home_score INTEGER,
            away_score INTEGER,
            status VARCHAR(20) DEFAULT '未开赛'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Predictions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES Users(id),
            match_id INTEGER REFERENCES Matches(id),
            predicted_home INTEGER NOT NULL,
            predicted_away INTEGER NOT NULL,
            submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ 云端数据库建表大功告成！数据已飞向云端！")

if __name__ == "__main__":
    init_db()