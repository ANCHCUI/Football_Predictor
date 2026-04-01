def calculate_score(actual_home, actual_away, predicted_home, predicted_away):
    """
    根据英超预测规则计算得分
    :param actual_home: 实际主队进球
    :param actual_away: 实际客队进球
    :param predicted_home: 预测主队进球
    :param predicted_away: 预测客队进球
    :return: 最终得分 (float)
    """

    # 规则 1：完全准确（5分）
    if actual_home == predicted_home and actual_away == predicted_away:
        return 5.0

    # 辅助函数：判断胜负关系（1代表主胜，-1代表客胜，0代表平局）
    def get_match_result(home, away):
        if home > away:
            return 1
        elif home < away:
            return -1
        else:
            return 0

    actual_result = get_match_result(actual_home, actual_away)
    predicted_result = get_match_result(predicted_home, predicted_away)

    # 规则 2 & 3：胜负准确的情况
    if actual_result == predicted_result:
        # 命中一方进球，或者净胜球准确（注：命中平局时，净胜球差值都为0，也会走这个逻辑）
        if (actual_home == predicted_home) or \
                (actual_away == predicted_away) or \
                (actual_home - actual_away == predicted_home - predicted_away):
            return 3.5
        # 胜负准确，但进球全错
        else:
            return 2.0

    # 规则 4 & 5：胜负错误的情况
    else:
        # 虽然胜负错了，但蒙对了一方的进球数
        if actual_home == predicted_home or actual_away == predicted_away:
            return 1.5
        # 彻底全错
        else:
            return 0.0


# ==========================================
# ⬇️ 本地测试区：运行一下看看准不准！
# ==========================================
if __name__ == "__main__":
    print("--- 开始测试计分引擎 (假设实际比分是 2:1) ---")
    print(f"预测 2:1 -> 得分: {calculate_score(2, 1, 2, 1)} (应为 5.0，完全准确)")
    print(f"预测 3:2 -> 得分: {calculate_score(2, 1, 3, 2)} (应为 3.5，胜负准且净胜球准)")
    print(f"预测 3:1 -> 得分: {calculate_score(2, 1, 3, 1)} (应为 3.5，胜负准且客队进球准)")
    print(f"预测 4:0 -> 得分: {calculate_score(2, 1, 4, 0)} (应为 2.0，胜负准但全错)")
    print(f"预测 1:1 -> 得分: {calculate_score(2, 1, 1, 1)} (应为 1.5，胜负错但客队进球准)")
    print(f"预测 0:3 -> 得分: {calculate_score(2, 1, 0, 3)} (应为 0.0，完全错误)")