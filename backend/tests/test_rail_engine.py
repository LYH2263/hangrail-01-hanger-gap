from app.services.rail_engine import FitResult, Placement, Segment, first_fit, fit, free_gaps


# —— 无缓冲（现网行为保持不变）——

def test_first_fit_leftmost():
    occ = [Segment(20, 40)]
    p = first_fit(100, occ, 15)
    assert p is not None
    assert p.start_cm == 0
    assert p.end_cm == 15


def test_first_fit_skips_too_small_gap():
    occ = [Segment(0, 10), Segment(18, 50)]
    p = first_fit(100, occ, 10)
    assert p is not None
    assert p.start_cm == 50


def test_no_space():
    occ = [Segment(0, 80)]
    assert first_fit(100, occ, 25) is None


def test_free_gaps_edges():
    gaps = free_gaps(50, [Segment(10, 20), Segment(30, 35)])
    assert gaps == [Segment(0, 10), Segment(20, 30), Segment(35, 50)]


def test_no_buffer_flush_from_zero_and_fill_continuous():
    """无缓冲：可贴 0 起挂，并连续挂满不留空隙。"""
    occ: list[Segment] = []
    for length in (30, 30, 40):
        decision = fit(100, occ, length, buffer_cm=0)
        assert decision.result is FitResult.OK
        assert decision.placement is not None
        occ.append(Segment(decision.placement.start_cm, decision.placement.end_cm))
    assert occ == [Segment(0, 30), Segment(30, 60), Segment(60, 100)]
    # 贴边填满后无空位
    assert fit(100, occ, 1, buffer_cm=0).result is FitResult.NO_SPACE


def test_no_buffer_default_argument():
    decision = fit(100, [Segment(0, 60)], 40)
    assert decision.result is FitResult.OK
    assert decision.placement == Placement(60, 100)


# —— 有缓冲 ——

def test_buffer_first_garment_starts_at_zero():
    """有缓冲时首件仍从 0 起挂：缓冲只存在于相邻衣物之间，杆边不加。"""
    decision = fit(100, [], 40, buffer_cm=5)
    assert decision.result is FitResult.OK
    assert decision.placement is not None
    assert decision.placement.start_cm == 0
    assert decision.placement.end_cm == 40


def test_buffer_start_after_previous_end_plus_buffer():
    """有缓冲：起点至少离开前衣 end + 缓冲。"""
    occ = [Segment(0, 40)]
    decision = fit(100, occ, 30, buffer_cm=5)
    assert decision.result is FitResult.OK
    assert decision.placement is not None
    assert decision.placement.start_cm == 45  # 40 + 5
    assert decision.placement.end_cm == 75


def test_buffer_both_sides_of_middle_gap():
    """中间空隙：新衣前后都要让出缓冲。"""
    occ = [Segment(0, 20), Segment(50, 100)]
    decision = fit(100, occ, 20, buffer_cm=5)
    assert decision.result is FitResult.OK
    assert decision.placement is not None
    assert decision.placement.start_cm == 25  # 20 + 5
    assert decision.placement.end_cm == 45    # 距后衣 50 恰好 5 cm


def test_buffer_blocks_flush_gap_and_reports_buffer_blocked():
    """贴边恰好能塞下、但加缓冲后失败：返回 BUFFER_BLOCKED 而非 NO_SPACE。"""
    # 空隙 40-60 正好 20 cm；缓冲 5 时需 25（前 5 + 衣 20，末端贴杆边无需后缓冲）
    occ = [Segment(0, 40), Segment(60, 100)]
    decision = fit(100, occ, 20, buffer_cm=5)
    assert decision.placement is None
    assert decision.result is FitResult.BUFFER_BLOCKED


def test_buffer_skips_flush_gap_uses_later_gap():
    """贴边空隙被缓冲封阻时，First-Fit 改挂更靠后的空隙。"""
    # 尾隙贴杆边只需前缓冲；中间隙 40-60（20cm 衣，需前后各 5）失败，
    # 尾隙 80-100 只需离开前衣 5：85 起挂、85+20=105 > 100 也不行，
    # 故构造更长尾隙 80-110。
    occ = [Segment(0, 40), Segment(60, 80)]
    decision = fit(110, occ, 20, buffer_cm=5)
    assert decision.result is FitResult.OK
    assert decision.placement is not None
    # 中间隙需 30 cm 可用空间（5+20+5），只有 20 → 跳过；尾隙 85 起挂
    assert decision.placement.start_cm == 85


def test_buffer_tail_gap_may_reach_rail_edge():
    """尾隙新衣可贴杆末端，只需离开前衣一个缓冲。"""
    occ = [Segment(0, 40)]
    # 45 起挂、45+55=100 贴边，恰好可行
    decision = fit(100, occ, 55, buffer_cm=5)
    assert decision.result is FitResult.OK
    assert decision.placement is not None
    assert decision.placement.start_cm == 45
    assert decision.placement.end_cm == 100
    # 物理空隙仅 60：61 cm 衣物贴边都放不下（普通空间不足）
    assert fit(100, occ, 61, buffer_cm=5).result is FitResult.NO_SPACE
    # 56 cm 物理可放但需 61（前缓冲 5）：属缓冲封阻
    assert fit(100, occ, 56, buffer_cm=5).result is FitResult.BUFFER_BLOCKED


def test_buffer_released_after_pickup():
    """取件释放后，合并空隙按缓冲规则重新可入。"""
    # 0-20、40-60 挂两件；中间隙 20-40 与尾隙 60-100 对 36 cm 衣物
    # 均被 5 cm 缓冲封阻（中间需 5+36+5=46>20；尾隙需 5+36=41>40）
    occ = [Segment(0, 20), Segment(40, 60)]
    assert fit(100, occ, 36, buffer_cm=5).result is FitResult.BUFFER_BLOCKED
    # 取件后衣：空隙合并为 20-100（贴杆末端），25 起挂可行
    occ = [Segment(0, 20)]
    decision = fit(100, occ, 36, buffer_cm=5)
    assert decision.result is FitResult.OK
    assert decision.placement is not None
    assert decision.placement.start_cm == 25


def test_buffer_zero_never_buffer_blocked():
    """无缓冲杆即使塞满也只报普通无空位，永不误报缓冲。"""
    occ = [Segment(0, 100)]
    decision = fit(100, occ, 1, buffer_cm=0)
    assert decision.result is FitResult.NO_SPACE


def test_seed_scenario_buffer_reroutes_to_rear_gap():
    """种子场景：A 杆 200cm/缓冲5，占位 0-45、50-85、90-150；
    50cm 新衣在 150-200 贴边可挂，加缓冲起点须 155、末端 205 超杆 → 封阻。"""
    occ = [Segment(0, 45), Segment(50, 85), Segment(90, 150)]
    decision_a = fit(200, occ, 50, buffer_cm=5)
    assert decision_a.placement is None
    assert decision_a.result is FitResult.BUFFER_BLOCKED
    # 无缓冲杆（B 杆）占位 0-40，同件衣物贴边挂入 40-90
    decision_b = fit(160, [Segment(0, 40)], 50, buffer_cm=0)
    assert decision_b.result is FitResult.OK
    assert decision_b.placement is not None
    assert (decision_b.placement.start_cm, decision_b.placement.end_cm) == (40, 90)
