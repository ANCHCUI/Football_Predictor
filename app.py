import streamlit as st
import sqlite3
import hashlib
import psycopg2

# ==========================================
# 🛠️ 辅助工具区：密码加密与数据库操作
# ==========================================
# 为了安全，密码不能明文存进数据库，我们用 SHA-256 给它加个密
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 注意：PostgreSQL 的占位符是 %s 而不是 ?
    cursor.execute("SELECT password FROM Users WHERE username=%s", (username,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] == hash_password(password):
        return True
    return False


def create_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (username, password) VALUES (%s, %s)",
                       (username, hash_password(password)))
        conn.commit()
        success = True
    except psycopg2.errors.UniqueViolation:  # 云端数据库的重复报错名不一样
        conn.rollback()
        success = False
    finally:
        conn.close()
    return success


# ==========================================
# 🖥️ 网页界面区：登录与注册逻辑
# ==========================================
st.set_page_config(page_title="英超赛事预测平台", page_icon="⚽")

# 初始化备忘录 (session_state)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# --- 如果没登录，显示大门（登录/注册） ---
if not st.session_state['logged_in']:
    st.title("⚽ 欢迎来到英超预测")
    st.write("请先登录您的球迷账号。")

    # 用 tabs 做出切换标签页的效果
    tab1, tab2 = st.tabs(["🔑 登录", "📝 注册新账号"])

    with tab1:
        st.subheader("账号登录")
        login_user = st.text_input("用户名", key="login_user")
        login_pwd = st.text_input("密码", type="password", key="login_pwd")
        if st.button("登录"):
            if verify_user(login_user, login_pwd):
                st.session_state['logged_in'] = True
                st.session_state['username'] = login_user
                st.success("登录成功！正在跳转...")
                st.rerun()  # 强制刷新页面，进入内部大厅
            else:
                st.error("用户名或密码错误！")

    with tab2:
        st.subheader("注册新球迷")
        reg_user = st.text_input("想一个拉风的用户名", key="reg_user")
        reg_pwd = st.text_input("设置密码", type="password", key="reg_pwd")
        reg_pwd2 = st.text_input("确认密码", type="password", key="reg_pwd2")
        if st.button("立即注册"):
            if reg_pwd != reg_pwd2:
                st.warning("两次输入的密码不一致哦！")
            elif reg_user == "" or reg_pwd == "":
                st.warning("用户名和密码不能为空！")
            else:
                if create_user(reg_user, reg_pwd):
                    st.success(f"太棒了 {reg_user}！注册成功，请去左边登录吧！")
                    st.balloons()  # 放点气球庆祝一下
                else:
                    st.error("哎呀，这个用户名已经被别人抢先注册了，换一个吧。")

# --- 如果已经登录，显示内部大厅 ---
else:
    st.sidebar.title(f"👤 欢迎, {st.session_state['username']}")
    if st.sidebar.button("退出登录"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.rerun()

    st.title("🏆 预测大厅")
    st.write(f"你好，**{st.session_state['username']}**！这里是赛前预测中心。")
    st.info("我们即将在这里展示本轮英超的对阵表...")