import functools
import itertools
import math
from fractions import Fraction

ZERO = Fraction(0)
ONE = Fraction(1)


@functools.cache
def traitor_win_prob(n: int, m: int) -> Fraction:
    """Exact P(Traitor win) from state (n, m) under mutual random play.

    Day-then-night recurrence: uniform random banishment, then Traitors
    murder one random Faithful. Returns an exact `fractions.Fraction`.

    This is taken from Migdał, P., "A mathematical model of the Mafia game",
    Art. no. arXiv:1009.1031, 2010. doi:10.48550/arXiv.1009.1031.
    """
    if m <= 0:
        return ZERO
    if m >= math.ceil(n / 2):
        return ONE

    traitor_banish_prob = Fraction(m, n)

    # Case 1: Traitor banished -> (n-1, m-1), then night murder -> (n-2, m-1)
    post_banish_players, post_banish_traitors = n - 1, m - 1
    if post_banish_traitors <= 0:
        win_prob_traitor_banished = ZERO
    else:
        post_murder_players = post_banish_players - 1
        win_prob_traitor_banished = traitor_win_prob(
            post_murder_players, post_banish_traitors
        )

    # Case 2: Faithful banished -> (n-1, m), then night murder -> (n-2, m)
    post_banish_players, post_banish_traitors = n - 1, m
    if post_banish_traitors >= math.ceil(post_banish_players / 2):
        win_prob_faithful_banished = ONE
    else:
        post_murder_players = post_banish_players - 1
        post_murder_traitors = post_banish_traitors
        if post_murder_traitors >= math.ceil(post_murder_players / 2):
            win_prob_faithful_banished = ONE
        else:
            win_prob_faithful_banished = traitor_win_prob(
                post_murder_players, post_murder_traitors
            )

    return (
        traitor_banish_prob * win_prob_traitor_banished
        + (ONE - traitor_banish_prob) * win_prob_faithful_banished
    )


def _truncated_product(first: list[int], second: list[int], degree: int) -> list[int]:
    """Multiply two integer polynomials, keeping terms up to `degree`."""
    result = [0] * (degree + 1)
    for first_power, first_coefficient in enumerate(first):
        if first_coefficient == 0 or first_power > degree:
            continue
        for second_power in range(min(len(second), degree + 1 - first_power)):
            result[first_power + second_power] += (
                first_coefficient * second[second_power]
            )
    return result


@functools.cache
def _p_faithful_rv_collusion(n: int, m: int) -> Fraction:
    r"""Exact probability that a Faithful is banished under RV+C.

    Each of the $n - m$ Faithful votes uniformly at random for one of the
    other $n - 1$ players, and all $m$ Traitors vote for the same Faithful
    target. The plurality winner is banished, with ties broken uniformly.

    The number of Faithful voting profiles with a given vote-count vector
    $v$ and no self-votes is, by inclusion and exclusion over the set $S$ of
    voters forced to vote for themselves,
    $$\sum_S (-1)^{|S|} (n - m - |S|)! / \prod_j (v_j - [j \in S])!.$$
    The players fall into three classes (the target, the other Faithful and
    the Traitors), and the banishment probability depends on $v$ only
    through the maximum count and the number of players of each class that
    attain it. We condition on these and sum the inclusion-exclusion terms
    with exponential generating functions in integer arithmetic. The cost is
    polynomial in $n$, compared with $(n - 1)^{n - m}$ voting profiles.
    """
    n_faithful = n - m
    other_faithful = n_faithful - 1
    scale = math.factorial(n_faithful)
    factorials = [math.factorial(votes) for votes in range(n_faithful + 1)]
    weighted_total = Fraction(0)
    for max_votes in range(m, n_faithful + m + 1):
        below_max = [
            scale // factorials[votes]
            for votes in range(min(max_votes, n_faithful + 1))
        ]
        self_vote_below_max = [0] + [
            scale // factorials[votes - 1]
            for votes in range(1, min(max_votes, n_faithful + 1))
        ]
        at_max = scale // factorials[max_votes] if max_votes <= n_faithful else 0
        self_vote_at_max = (
            scale // factorials[max_votes - 1] if max_votes <= n_faithful else 0
        )
        target_faithful_votes = max_votes - m
        target_terms = {}
        for target_at_max in (True, False):
            plain = [0] * (n_faithful + 1)
            self_vote = [0] * (n_faithful + 1)
            if target_at_max is True:
                votes_range = [target_faithful_votes]
            else:
                votes_range = list(range(target_faithful_votes))
            for votes in votes_range:
                plain[votes] = scale // factorials[votes]
                if votes >= 1:
                    self_vote[votes] = scale // factorials[votes - 1]
            target_terms[target_at_max] = (plain, self_vote)
        below_max_powers = [[1]]
        for _ in range(other_faithful + m):
            below_max_powers.append(
                _truncated_product(below_max_powers[-1], below_max, n_faithful)
            )
        self_vote_powers = [[1]]
        for _ in range(other_faithful):
            self_vote_powers.append(
                _truncated_product(
                    self_vote_powers[-1], self_vote_below_max, n_faithful
                )
            )
        for target_at_max, (target_plain, target_self_vote) in target_terms.items():
            for others_at_max in range(other_faithful + 1):
                others_below_max = other_faithful - others_at_max
                at_max_weights = [
                    math.comb(others_at_max, self_votes)
                    * at_max ** (others_at_max - self_votes)
                    * (-self_vote_at_max) ** self_votes
                    for self_votes in range(others_at_max + 1)
                ]
                for traitors_at_max in range(m + 1):
                    faithful_at_max = others_at_max + int(target_at_max)
                    players_at_max = faithful_at_max + traitors_at_max
                    degree = n_faithful - (others_at_max + traitors_at_max) * max_votes
                    if players_at_max == 0 or degree < 0:
                        continue
                    class_total = 0
                    for self_votes_below in range(others_below_max + 1):
                        base = _truncated_product(
                            below_max_powers[
                                others_below_max
                                - self_votes_below
                                + m
                                - traitors_at_max
                            ],
                            self_vote_powers[self_votes_below],
                            degree,
                        )
                        for target_poly, target_self in (
                            (target_plain, 0),
                            (target_self_vote, 1),
                        ):
                            coefficient = sum(
                                base[power] * target_poly[degree - power]
                                for power in range(degree + 1)
                            )
                            if coefficient == 0:
                                continue
                            for self_votes_at_max, at_max_weight in enumerate(
                                at_max_weights
                            ):
                                self_votes = (
                                    self_votes_below + target_self + self_votes_at_max
                                )
                                class_total += (
                                    (-1) ** (self_votes_below + target_self)
                                    * math.comb(others_below_max, self_votes_below)
                                    * at_max_weight
                                    * coefficient
                                    * factorials[n_faithful - self_votes]
                                )
                    class_total *= (
                        math.comb(other_faithful, others_at_max)
                        * math.comb(m, traitors_at_max)
                        * at_max**traitors_at_max
                    )
                    weighted_total += Fraction(
                        class_total * faithful_at_max, players_at_max
                    )
    return weighted_total / (scale**n * (n - 1) ** n_faithful)


@functools.cache
def traitor_win_prob_collusion(n: int, m: int) -> Fraction:
    """Exact P(Traitor win) from (n, m) under RV+C (w_‡).

    Faithful vote randomly; all m Traitors collude on a single Faithful
    target each round. Returns an exact `fractions.Fraction`.

    The recurrence is
        w_‡(n, m) = p_F · w_‡(n-2, m) + (1-p_F) · w_‡(n-2, m-1),
    where p_F = p_F^{coll,RV}(n, m) is the probability of banishing a
    Faithful under collusion, computed by `_p_faithful_rv_collusion`.

    The banishment probability is computed exactly in time polynomial in
    n, so exact values are available across the televised range.
    """
    if m <= 0:
        return ZERO
    if 2 * m >= n:
        return ONE
    faithful_banish_prob = _p_faithful_rv_collusion(n, m)
    return faithful_banish_prob * traitor_win_prob_collusion(n - 2, m) + (
        ONE - faithful_banish_prob
    ) * traitor_win_prob_collusion(n - 2, m - 1)


@functools.cache
def traitor_win_prob_vlopt(n: int, m: int) -> Fraction:
    """Exact P(Traitor win) from (n, m) under VL+Opt (w_†).

    Faithful follow Vote-Left; Traitors play the optimal strategy σ†:
    comply (random vote) when n > 2m+2, collude otherwise. Returns an
    exact `fractions.Fraction`.

    The recurrence is
        w_†(n, m) = p_F · w_†(n-2, m) + (1-p_F) · w_†(n-2, m-1),
    where p_F = (n-m)/n when n > 2m+2 (comply branch, Migdał), and
    p_F = 1 when n ≤ 2m+2 (collude branch): the colluding Traitors' target
    receives at least two votes and every other player at most one, so the
    Traitors reach parity with certainty.
    """
    if m <= 0:
        return ZERO
    if n <= 2 * m + 2:
        return ONE
    faithful_banish_prob = Fraction(n - m, n)
    return faithful_banish_prob * traitor_win_prob_vlopt(n - 2, m) + (
        ONE - faithful_banish_prob
    ) * traitor_win_prob_vlopt(n - 2, m - 1)


@functools.cache
def traitor_win_prob_switch(n: int, m: int) -> Fraction:
    """Exact P(Traitor win) from (n, m) when the Faithful switch protocols.

    The Faithful play Vote-Left with punishment while n > 2m+2 and vote
    uniformly at random once n ≤ 2m+2. The Traitors comply in the main game
    and collude in the late game. Returns an exact `fractions.Fraction`.

    The recurrence is that of `traitor_win_prob_vlopt` in the main game,
        w_s(n, m) = (n-m)/n · w_s(n-2, m) + m/n · w_s(n-2, m-1),
    with the late-game boundary w_s(n, m) = w_‡(n, m) for 2m < n ≤ 2m+2,
    the RV+C value from `traitor_win_prob_collusion`.
    """
    if m <= 0:
        return ZERO
    if n <= 2 * m:
        return ONE
    if n <= 2 * m + 2:
        return traitor_win_prob_collusion(n, m)
    faithful_banish_prob = Fraction(n - m, n)
    return faithful_banish_prob * traitor_win_prob_switch(n - 2, m) + (
        ONE - faithful_banish_prob
    ) * traitor_win_prob_switch(n - 2, m - 1)


def _ordered_vote_outcome(roles: tuple[bool, ...]) -> Fraction | None:
    """Return the Traitor win probability if the state is decided, else None."""
    traitors_alive = sum(roles)
    if traitors_alive == 0:
        return ZERO
    if 2 * traitors_alive >= len(roles):
        return ONE
    return None


@functools.cache
def _ordered_vote_value(roles: tuple[bool, ...], vote_left_main_game: bool) -> Fraction:
    r"""Exact Traitor win probability under an ordered vote with planned murders.

    The state lists the roles of the surviving players in the public order,
    with `True` for a Traitor, at the start of a day phase. Every player votes
    for the first surviving player in the order, who votes for the second, so
    the first player is banished. When `vote_left_main_game` is true this
    applies only in the late game ($n \leq 2m + 2$), and in the main game
    every player follows Vote-Left, so that each survivor is banished with
    probability $1/n$. At night the Traitors murder the Faithful player that
    maximises their winning probability.
    """
    decided = _ordered_vote_outcome(roles)
    if decided is not None:
        return decided
    n_alive = len(roles)
    traitors_alive = sum(roles)
    if vote_left_main_game is True and n_alive > 2 * traitors_alive + 2:
        banishments = [(index, Fraction(1, n_alive)) for index in range(n_alive)]
    else:
        banishments = [(0, ONE)]
    total = ZERO
    for banished_index, banish_prob in banishments:
        after_day = roles[:banished_index] + roles[banished_index + 1 :]
        decided = _ordered_vote_outcome(after_day)
        if decided is not None:
            total += banish_prob * decided
            continue
        best_value = max(
            _ordered_vote_value(
                after_day[:victim_index] + after_day[victim_index + 1 :],
                vote_left_main_game,
            )
            for victim_index, is_traitor in enumerate(after_day)
            if is_traitor is False
        )
        total += banish_prob * best_value
    return total


def _ordered_vote_average(n: int, m: int, vote_left_main_game: bool) -> Fraction:
    """Average the ordered vote value over every placement of the Traitors."""
    total = ZERO
    placements = 0
    for traitor_positions in itertools.combinations(range(n), m):
        roles = tuple(position in traitor_positions for position in range(n))
        total += _ordered_vote_value(roles, vote_left_main_game)
        placements += 1
    return total / placements


@functools.cache
def traitor_win_prob_first_player(n: int, m: int) -> Fraction:
    """Exact P(Traitor win) when everyone votes for the first player in order.

    Every player votes for the first surviving player in the public order,
    who votes for the second, so the banishment order is fixed in advance.
    The Traitors know the order and choose each murder to maximise their
    winning probability; the roles are placed uniformly at random. Returns an
    exact `fractions.Fraction`.

    Because the banishment order is known, the Traitors can protect themselves
    by murdering the Faithful who stand behind them, and they do much better
    than under random voting.
    """
    return _ordered_vote_average(n, m, vote_left_main_game=False)


@functools.cache
def traitor_win_prob_concentrated(n: int, m: int) -> Fraction:
    r"""Exact P(Traitor win) under Vote-Left then a concentrated vote.

    The Faithful play Vote-Left while $n > 2m + 2$, and in the late game every
    player votes for the first surviving player in the public order, who votes
    for the second. A Traitor is then banished in the late game exactly when
    the first player is a Traitor, whatever the Traitors vote. The Traitors
    know the order and choose each murder, in the main game as well as the
    late game, to maximise their winning probability; the roles are placed
    uniformly at random. Returns an exact `fractions.Fraction`.

    The computation is a dynamic programme over the sequence of roles in the
    public order, so its cost grows with the number of such sequences.
    """
    return _ordered_vote_average(n, m, vote_left_main_game=True)
