from app.services.rail_engine import Segment, first_fit, free_gaps


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


# —— 间隔缓冲 ——


def test_no_buffer_allows_edge_to_edge():
    # 无缓冲：可贴 0 起挂，也可贴满连续空隙（现网行为不变）
    assert first_fit(100, [], 100, buffer_cm=0).start_cm == 0
    p = first_fit(100, [Segment(0, 40)], 60, buffer_cm=0)
    assert p is not None
    assert p.start_cm == 40  # 贴边，无需留白
    assert p.end_cm == 100


def test_buffer_pushes_start_past_prev_end_plus_buffer():
    # 有缓冲：起点至少离开前衣 end + 缓冲
    p = first_fit(100, [Segment(0, 40)], 50, buffer_cm=5)
    assert p is not None
    assert p.start_cm == 45
    assert p.end_cm == 95


def test_buffer_also_counts_before_next_garment():
    # 两侧都有衣物时，缓冲在两边都计入占用
    occ = [Segment(0, 40), Segment(95, 100)]  # 空隙 [40,95] 长 55
    assert first_fit(100, occ, 55, buffer_cm=5) is None  # 55+5+5 放不下
    p = first_fit(100, occ, 45, buffer_cm=5)
    assert p is not None
    assert p.start_cm == 45
    assert p.end_cm == 90  # 距后衣 95 恰好留 5cm 缓冲


def test_buffer_not_required_at_rail_ends():
    # 杆端无相邻衣物，不留缓冲：可贴 0 起挂、可顶到杆尾
    p = first_fit(100, [Segment(50, 100)], 45, buffer_cm=5)
    assert p is not None
    assert p.start_cm == 0
    p = first_fit(100, [Segment(0, 50)], 45, buffer_cm=5)
    assert p is not None
    assert p.end_cm == 100


def test_buffer_blocks_exact_fit_gap():
    # 恰好等长的空隙：无缓冲可贴边挂满，有缓冲则失败
    occ = [Segment(0, 40), Segment(90, 100)]  # 空隙 [40,90] 长 50
    assert first_fit(100, occ, 50, buffer_cm=0) is not None
    assert first_fit(100, occ, 50, buffer_cm=5) is None


def test_buffer_moves_placement_to_later_gap():
    # 种子场景：A 杆缓冲 5，[0,45] [50,85] [115,155]
    occ = [Segment(0, 45), Segment(50, 85), Segment(115, 155)]
    # 无缓冲：30cm 贴边挂入恰好等长的 [85,115]
    p = first_fit(200, occ, 30, buffer_cm=0)
    assert p is not None
    assert p.start_cm == 85
    # 有缓冲：[85,115] 不可用，改挂更靠后的空隙 160 起
    p = first_fit(200, occ, 30, buffer_cm=5)
    assert p is not None
    assert p.start_cm == 160
    assert p.end_cm == 190


def test_release_reopens_gap_with_buffer_rules():
    # 取件释放后，空隙按缓冲规则重新可入
    occ = [Segment(0, 45), Segment(50, 85), Segment(115, 155)]
    assert first_fit(200, occ, 30, buffer_cm=5).start_cm == 160
    released = [Segment(0, 45), Segment(115, 155)]  # 取走 [50,85]
    p = first_fit(200, released, 30, buffer_cm=5)
    assert p is not None
    assert p.start_cm == 50  # 释放出的空隙按缓冲重新可用
