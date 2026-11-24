"""Tests for exact win probabilities and deviation analysis."""

import fractions
import math

import backstab

# === Exact win probabilities (Migdał recurrence) =============================


def test_boundary_no_traitors():
    for n in range(1, 30):
        assert backstab.traitor_win_prob(n, 0) == 0


def test_boundary_traitor_majority():
    assert backstab.traitor_win_prob(4, 2) == 1
    assert backstab.traitor_win_prob(5, 3) == 1
    assert backstab.traitor_win_prob(6, 3) == 1
    assert backstab.traitor_win_prob(10, 5) == 1


def test_boundary_two_players():
    assert backstab.traitor_win_prob(2, 1) == 1


def test_in_unit_interval():
    for n in range(2, 30):
        for m in range(1, n):
            win_prob = backstab.traitor_win_prob(n, m)
            assert 0 <= win_prob <= 1, f"w({n},{m})={win_prob}"


def test_monotone_in_m():
    for n in [10, 15, 20, 25]:
        prev_win_prob = fractions.Fraction(0)
        for m in range(1, n):
            win_prob = backstab.traitor_win_prob(n, m)
            assert win_prob >= prev_win_prob
            prev_win_prob = win_prob


def test_known_value_w4_1():
    assert backstab.traitor_win_prob(4, 1) == fractions.Fraction(3, 4)


def test_more_traitors_helps():
    assert backstab.traitor_win_prob(10, 3) > backstab.traitor_win_prob(10, 2)


# === RV+C win probability (w_‡) ==============================================


def test_collusion_boundary_no_traitors():
    for n in range(1, 15):
        assert backstab.traitor_win_prob_collusion(n, 0) == 0


def test_collusion_boundary_no_faithful():
    assert backstab.traitor_win_prob_collusion(5, 5) == 1


def test_collusion_boundary_majority():
    assert backstab.traitor_win_prob_collusion(4, 2) == 1
    assert backstab.traitor_win_prob_collusion(6, 3) == 1


def test_collusion_returns_fraction():
    collusion_prob = backstab.traitor_win_prob_collusion(6, 2)
    assert isinstance(collusion_prob, fractions.Fraction)


def test_collusion_known_value_5_1():
    win_prob = backstab.traitor_win_prob_collusion(5, 1)
    assert isinstance(win_prob, fractions.Fraction)
    assert win_prob == fractions.Fraction(8, 15)


def test_collusion_known_value_6_2():
    win_prob = backstab.traitor_win_prob_collusion(6, 2)
    assert isinstance(win_prob, fractions.Fraction)
    assert win_prob == fractions.Fraction(2411, 2500)


def test_collusion_known_value_8_3():
    win_prob = backstab.traitor_win_prob_collusion(8, 3)
    assert isinstance(win_prob, fractions.Fraction)
    assert win_prob == fractions.Fraction(10493428, 10504375)


def test_collusion_known_value_9_3():
    win_prob = backstab.traitor_win_prob_collusion(9, 3)
    assert isinstance(win_prob, fractions.Fraction)
    assert win_prob == fractions.Fraction(1298596652927, 1304596316160)


def test_collusion_known_value_10_4():
    win_prob = backstab.traitor_win_prob_collusion(10, 4)
    assert isinstance(win_prob, fractions.Fraction)
    assert win_prob == fractions.Fraction(1860812219951, 1860818518125)


# === VL+Opt win probability (w_†) ============================================


def test_vlopt_boundary_no_traitors():
    for n in range(1, 20):
        assert backstab.traitor_win_prob_vlopt(n, 0) == 0


def test_vlopt_boundary_majority():
    assert backstab.traitor_win_prob_vlopt(4, 2) == 1
    assert backstab.traitor_win_prob_vlopt(6, 3) == 1
    assert backstab.traitor_win_prob_vlopt(8, 4) == 1


def test_vlopt_collude_threshold():
    for m in range(2, 6):
        n_boundary = 2 * m + 2
        n_safe = 2 * m + 4
        prob_at_boundary = backstab.traitor_win_prob_vlopt(n_boundary, m)
        prob_at_safe = backstab.traitor_win_prob_vlopt(n_safe, m)
        assert prob_at_boundary >= prob_at_safe


def test_vlopt_in_unit_interval():
    for n in range(2, 30):
        for m in range(0, n):
            win_prob = backstab.traitor_win_prob_vlopt(n, m)
            assert 0 <= win_prob <= 1, f"w_†({n},{m})={win_prob}"


def test_vlopt_returns_fraction():
    vlopt_prob = backstab.traitor_win_prob_vlopt(8, 2)
    assert isinstance(vlopt_prob, fractions.Fraction)


def test_vlopt_dominates_random():
    for n in range(3, 30):
        for m in range(1, math.ceil(n / 2)):
            vlopt_prob = backstab.traitor_win_prob_vlopt(n, m)
            migdal_prob = backstab.traitor_win_prob(n, m)
            assert vlopt_prob >= migdal_prob, (
                f"w_†({n},{m})={vlopt_prob} < w({n},{m})={migdal_prob}"
            )


def test_vlopt_known_value_8_2():
    vlopt_prob = backstab.traitor_win_prob_vlopt(8, 2)
    assert vlopt_prob == fractions.Fraction(23, 24)


def test_vlopt_deviates_from_migdal_at_threshold():
    for m in range(2, 5):
        n = 2 * m + 2
        vlopt_prob = backstab.traitor_win_prob_vlopt(n, m)
        migdal_prob = backstab.traitor_win_prob(n, m)
        assert vlopt_prob > migdal_prob, (
            f"w_†({n},{m})={vlopt_prob} should exceed w({n},{m})={migdal_prob}"
        )


def test_vlopt_single_traitor_late_game_is_certain_win():
    assert backstab.traitor_win_prob_vlopt(3, 1) == 1
    assert backstab.traitor_win_prob_vlopt(4, 1) == 1


def test_vlopt_known_values_single_traitor():
    assert backstab.traitor_win_prob_vlopt(5, 1) == fractions.Fraction(4, 5)
    assert backstab.traitor_win_prob_vlopt(6, 1) == fractions.Fraction(5, 6)


# === Switching protocol win probability (w_s) ================================


def test_switch_boundaries():
    assert backstab.traitor_win_prob_switch(9, 0) == 0
    assert backstab.traitor_win_prob_switch(4, 2) == 1


def test_switch_equals_collusion_in_late_game():
    for m in range(1, 4):
        for n in (2 * m + 1, 2 * m + 2):
            assert backstab.traitor_win_prob_switch(
                n, m
            ) == backstab.traitor_win_prob_collusion(n, m)


def test_switch_equals_migdal_with_one_traitor():
    for n in range(3, 20):
        assert backstab.traitor_win_prob_switch(n, 1) == backstab.traitor_win_prob(n, 1)


def test_switch_improves_on_vlopt_and_collusion():
    for n in range(3, 26):
        for m in range(1, math.ceil(n / 2)):
            switch_prob = backstab.traitor_win_prob_switch(n, m)
            assert switch_prob <= backstab.traitor_win_prob_vlopt(n, m)
            assert switch_prob <= backstab.traitor_win_prob_collusion(n, m)


def test_switch_known_value_15_2():
    switch_prob = backstab.traitor_win_prob_switch(15, 2)
    assert switch_prob == fractions.Fraction(246557, 411840)


def enumerate_p_faithful_rv_collusion(n, m):
    """Brute-force reference: enumerate every Faithful voting profile."""
    import itertools

    n_faithful = n - m
    total_profiles = 0
    faithful_banished = fractions.Fraction(0)
    for votes in itertools.product(range(n), repeat=n_faithful):
        if any(votes[voter] == voter for voter in range(n_faithful)):
            continue
        total_profiles += 1
        vote_totals = [0] * n
        for target in votes:
            vote_totals[target] += 1
        vote_totals[0] += m
        max_votes = max(vote_totals)
        tied_players = [
            player for player, count in enumerate(vote_totals) if count == max_votes
        ]
        tied_faithful = [player for player in tied_players if player < n_faithful]
        faithful_banished += fractions.Fraction(len(tied_faithful), len(tied_players))
    return faithful_banished / total_profiles


def test_collusion_banishment_matches_enumeration():
    from backstab._analysis import _p_faithful_rv_collusion

    for n in range(2, 9):
        for m in range(1, n):
            assert _p_faithful_rv_collusion(n, m) == enumerate_p_faithful_rv_collusion(
                n, m
            )


def test_collusion_exact_in_televised_range():
    for n, m in [(20, 3), (22, 3), (22, 4), (25, 4), (25, 5)]:
        win_prob = backstab.traitor_win_prob_collusion(n, m)
        assert 0 < win_prob < 1
        assert win_prob > backstab.traitor_win_prob(n, m)


def test_ordered_vote_boundaries():
    assert backstab.traitor_win_prob_concentrated(5, 0) == 0
    assert backstab.traitor_win_prob_concentrated(4, 2) == 1
    assert backstab.traitor_win_prob_first_player(5, 0) == 0
    assert backstab.traitor_win_prob_first_player(4, 2) == 1


def test_first_player_with_one_traitor_from_three():
    """The first player is banished; the Traitor is first with probability 1/3."""
    assert backstab.traitor_win_prob_first_player(3, 1) == fractions.Fraction(2, 3)


def test_concentrated_equals_first_player_in_the_late_game():
    for m in range(1, 4):
        for n in (2 * m + 1, 2 * m + 2):
            assert backstab.traitor_win_prob_concentrated(
                n, m
            ) == backstab.traitor_win_prob_first_player(n, m)


def test_planned_murders_beat_the_switching_profile():
    """With planned murders the concentrated vote is worse for the Faithful."""
    for n, m in [(9, 2), (12, 3), (15, 2)]:
        assert backstab.traitor_win_prob_concentrated(
            n, m
        ) > backstab.traitor_win_prob_switch(n, m)
        assert backstab.traitor_win_prob_first_player(n, m) > backstab.traitor_win_prob(
            n, m
        )


def test_concentrated_matches_simulation():
    n, m = 9, 2
    game = backstab.TraitorsGame(n, m, detect=True, late_game_detection=False)
    results = game.simulate(
        faithful=backstab.FixedOrderThenFirst(n_traitors=m),
        traitor=backstab.FixedOrderThenFirst(n_traitors=m),
        murder=backstab.PlanningMurder(vote_left_main_game=True),
        n=4000,
        seed=0,
    )
    exact = 1 - float(backstab.traitor_win_prob_concentrated(n, m))
    lower, upper = results.ci_95
    assert lower <= exact <= upper


def test_first_player_matches_simulation():
    n, m = 9, 2
    game = backstab.TraitorsGame(n, m, detect=False)
    results = game.simulate(
        faithful=backstab.FixedOrderThenFirst(n_traitors=n),
        traitor=backstab.FixedOrderThenFirst(n_traitors=n),
        murder=backstab.PlanningMurder(vote_left_main_game=False),
        n=4000,
        seed=0,
    )
    exact = 1 - float(backstab.traitor_win_prob_first_player(n, m))
    lower, upper = results.ci_95
    assert lower <= exact <= upper
