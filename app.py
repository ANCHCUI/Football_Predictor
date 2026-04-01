import streamlit as st
import psycopg2
import hashlib
from datetime import datetime, timedelta


# ==========================================
# 🛠️ 辅助工具区
# ==========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
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
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        success = False
    finally:
        conn.close()
    return success


# 获取当前的北京时间（防止云端服务器存在时差）
def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)


# ==========================================
# 🖥️ 网页界面区
# ==========================================
st.set_page_config(page_title="英超赛事预测平台", page_icon="⚽", layout="centered")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# --- 未登录界面 ---
if not st.session_state['logged_in']:
    st.title("⚽ 欢迎来到英超预测大师杯")
    st.write("请先登录您的球迷账号。")

    tab1, tab2 = st.tabs(["🔑 登录", "📝 注册新账号"])

    with tab1:
        login_user = st.text_input("用户名", key="login_user")
        login_pwd = st.text_input("密码", type="password", key="login_pwd")
        if st.button("登录"):
            if verify_user(login_user, login_pwd):
                st.session_state['logged_in'] = True
                st.session_state['username'] = login_user
                st.rerun()
            else:
                st.error("用户名或密码错误！")

    with tab2:
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
                    st.success("注册成功，请去左边登录吧！")
                else:
                    st.error("用户名已存在。")

# --- 登录后的预测大厅 ---
else:
    st.sidebar.title(f"👤 {st.session_state['username']}")
    if st.sidebar.button("退出登录"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.rerun()

    st.title("🏆 英超第32轮预测大厅")
    st.write("⚠️ **注意规则：** 每场比赛开球前 **30分钟** 停止预测提交！")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 获取当前用户的专属 ID
    cursor.execute("SELECT id FROM Users WHERE username=%s", (st.session_state['username'],))
    user_id = cursor.fetchone()[0]

    # 2. 获取该用户已经提交过的预测（方便他们修改）
    cursor.execute("SELECT match_id, predicted_home, predicted_away FROM Predictions WHERE user_id=%s", (user_id,))
    user_preds = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    # 3. 获取所有未开赛的比赛
    cursor.execute(
        "SELECT id, home_team, away_team, kickoff_time FROM Matches WHERE status='未开赛' ORDER BY kickoff_time")
    matches = cursor.fetchall()

    current_time = get_beijing_time()

    # 4. 循环生成每一场比赛的预测卡片
    for match in matches:
        match_id, home, away, kickoff = match

        # 计算是否已经过了提交截止时间（开球前30分钟）
        deadline = kickoff - timedelta(minutes=30)
        is_locked = current_time > deadline

        # 用漂亮的卡片样式框起来
        with st.container(border=True):
            st.subheader(f"{home} ⚔️ {away}")

            if is_locked:
                st.error(f"🔒 预测已关闭 (开球时间: {kickoff.strftime('%Y-%m-%d %H:%M')})")
            else:
                st.caption(
                    f"🕒 截止时间: {deadline.strftime('%Y-%m-%d %H:%M')} (当前: {current_time.strftime('%H:%M')})")

            # 读取历史预测作为默认值
            default_h, default_a = user_preds.get(match_id, (0, 0))

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                # 如果锁定，输入框就变成禁用状态 (disabled)
                pred_h = st.number_input(f"{home} 进球", min_value=0, max_value=20, step=1, value=default_h,
                                         key=f"h_{match_id}", disabled=is_locked)
            with col2:
                pred_a = st.number_input(f"{away} 进球", min_value=0, max_value=20, step=1, value=default_a,
                                         key=f"a_{match_id}", disabled=is_locked)
            with col3:
                st.write("")  # 占个位让按钮往下靠一点
                st.write("")
                if not is_locked:
                    if st.button("提交 / 修改", key=f"btn_{match_id}", use_container_width=True):
                        # 检查是新建预测还是修改老预测
                        if match_id in user_preds:
                            cursor.execute(
                                "UPDATE Predictions SET predicted_home=%s, predicted_away=%s, submit_time=CURRENT_TIMESTAMP WHERE user_id=%s AND match_id=%s",
                                (pred_h, pred_a, user_id, match_id))
                        else:
                            cursor.execute(
                                "INSERT INTO Predictions (user_id, match_id, predicted_home, predicted_away) VALUES (%s, %s, %s, %s)",
                                (user_id, match_id, pred_h, pred_a))
                        conn.commit()
                        st.success("保存成功！")
                        st.rerun()  # 刷新页面显示最新状态

    cursor.close()
    conn.close()