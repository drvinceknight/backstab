import random

from backstab._analysis import _ordered_vote_value
from backstab._types import PlayerID, RoundRecord


class FixedOrder:
    """Vote for the next surviving player in the fixed cyclic ordering."""

    def vote(
        self,
        voter: PlayerID,
        alive: list[PlayerID],
        seating: list[PlayerID],
        traitors: set[PlayerID],
        is_traitor: bool,
        history: list[RoundRecord],
        known_traitors: set[PlayerID],
    ) -> PlayerID:
        alive_set = set(alive)
        voter_seat_index = seating.index(voter)
        seating_size = len(seating)
        for step in range(1, seating_size):
            candidate = seating[(voter_seat_index + step) % seating_size]
            if candidate in alive_set and candidate != voter:
                return candidate
        raise ValueError(  # pragma: no cover
            f"No valid vote target found for voter {voter}"
        )

    def __repr__(self) -> str:
        return "FixedOrder()"


class RandomVote:
    """Vote uniformly at random among surviving players (excluding self)."""

    def vote(
        self,
        voter: PlayerID,
        alive: list[PlayerID],
        seating: list[PlayerID],
        traitors: set[PlayerID],
        is_traitor: bool,
        history: list[RoundRecord],
        known_traitors: set[PlayerID],
    ) -> PlayerID:
        return random.choice([player for player in alive if player != voter])

    def __repr__(self) -> str:
        return "RandomVote()"


class Collusion:
    """Traitors coordinate on a single random Faithful target per round.

    Faithful players using this strategy vote randomly.
    """

    def __init__(self) -> None:
        self._target: int | None = None
        self._round: int = -1

    def vote(
        self,
        voter: PlayerID,
        alive: list[PlayerID],
        seating: list[PlayerID],
        traitors: set[PlayerID],
        is_traitor: bool,
        history: list[RoundRecord],
        known_traitors: set[PlayerID],
    ) -> PlayerID:
        if is_traitor is False:
            return random.choice([player for player in alive if player != voter])
        round_number = len(history)
        if (
            round_number != self._round
            or self._target not in alive
            or self._target in traitors
        ):
            faithful_players = [player for player in alive if player not in traitors]
            self._target = random.choice(faithful_players)
            self._round = round_number
        target = self._target
        assert target is not None
        return target

    def __repr__(self) -> str:
        return "Collusion()"


class MixedDeviation:
    """Traitors deviate from FixedOrder with probability p each round.

    When deviating, votes for a random Faithful. Faithful always play FixedOrder.

    Raises:
        ValueError: If p is not in [0, 1].
    """

    def __init__(self, p: float = 0.2) -> None:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"Deviation probability must be in [0,1], got {p}")
        self.p = p
        self._fixed_order = FixedOrder()

    def vote(
        self,
        voter: PlayerID,
        alive: list[PlayerID],
        seating: list[PlayerID],
        traitors: set[PlayerID],
        is_traitor: bool,
        history: list[RoundRecord],
        known_traitors: set[PlayerID],
    ) -> PlayerID:
        if is_traitor is False:
            return self._fixed_order.vote(
                voter, alive, seating, traitors, is_traitor, history, known_traitors
            )
        if random.random() < self.p:
            faithful_players = [
                player for player in alive if player not in traitors and player != voter
            ]
            if len(faithful_players) > 0:
                return random.choice(faithful_players)
        return self._fixed_order.vote(
            voter, alive, seating, traitors, is_traitor, history, known_traitors
        )

    def __repr__(self) -> str:
        return f"MixedDeviation(p={self.p})"


class RampDeviation:
    """Deviation probability ramps linearly from p_start to p_end over the game.

    Progress is measured by the fraction of players eliminated. Faithful always
    play FixedOrder.

    Raises:
        ValueError: If either probability is not in [0, 1].
    """

    def __init__(
        self,
        p_start: float = 0.0,
        p_end: float = 1.0,
        n_total: int = 22,
    ) -> None:
        if not (0 <= p_start <= 1 and 0 <= p_end <= 1):
            raise ValueError("Probabilities must be in [0,1]")
        self.p_start = p_start
        self.p_end = p_end
        self.n_total = n_total
        self._fixed_order = FixedOrder()

    def _current_p(self, n_alive: int) -> float:
        """Interpolate deviation probability based on fraction of game elapsed."""
        if self.n_total <= 2:
            return self.p_end
        game_progress_fraction = (self.n_total - n_alive) / (self.n_total - 2)
        game_progress_fraction = max(0.0, min(1.0, game_progress_fraction))
        return self.p_start + game_progress_fraction * (self.p_end - self.p_start)

    def vote(
        self,
        voter: PlayerID,
        alive: list[PlayerID],
        seating: list[PlayerID],
        traitors: set[PlayerID],
        is_traitor: bool,
        history: list[RoundRecord],
        known_traitors: set[PlayerID],
    ) -> PlayerID:
        if is_traitor is False:
            return self._fixed_order.vote(
                voter, alive, seating, traitors, is_traitor, history, known_traitors
            )
        deviation_prob = self._current_p(len(alive))
        if random.random() < deviation_prob:
            faithful_players = [
                player for player in alive if player not in traitors and player != voter
            ]
            if len(faithful_players) > 0:
                return random.choice(faithful_players)
        return self._fixed_order.vote(
            voter, alive, seating, traitors, is_traitor, history, known_traitors
        )

    def __repr__(self) -> str:
        return f"RampDeviation(p_start={self.p_start}, p_end={self.p_end})"


class ThresholdDeviation:
    """Comply with FixedOrder while n_alive > threshold, then deviate.

    Models late-game deviation when the cost of identification is low.

    Raises:
        ValueError: If threshold < 2 or p_late not in [0, 1].
    """

    def __init__(self, threshold: int = 8, p_late: float = 1.0) -> None:
        if threshold < 2:
            raise ValueError("Threshold must be >= 2")
        if not 0 <= p_late <= 1:
            raise ValueError("p_late must be in [0,1]")
        self.threshold = threshold
        self.p_late = p_late
        self._fixed_order = FixedOrder()

    def vote(
        self,
        voter: PlayerID,
        alive: list[PlayerID],
        seating: list[PlayerID],
        traitors: set[PlayerID],
        is_traitor: bool,
        history: list[RoundRecord],
        known_traitors: set[PlayerID],
    ) -> PlayerID:
        if is_traitor is False:
            return self._fixed_order.vote(
                voter, alive, seating, traitors, is_traitor, history, known_traitors
            )
        if len(alive) <= self.threshold and random.random() < self.p_late:
            faithful_players = [
                player for player in alive if player not in traitors and player != voter
            ]
            if len(faithful_players) > 0:
                return random.choice(faithful_players)
        return self._fixed_order.vote(
            voter, alive, seating, traitors, is_traitor, history, known_traitors
        )

    def __repr__(self) -> str:
        return f"ThresholdDeviation(threshold={self.threshold}, p_late={self.p_late})"


class OptimalTimingDeviation:
    """Deviate only when exact payoff analysis predicts it is profitable.

    Deviates when n <= 2m + 2 by colluding on a single Faithful target, which
    forces that target's banishment. A sole surviving Traitor never targets
    their own FixedOrder target, since voting for that player is not a
    deviation and would leave every player with one vote. Faithful always play
    FixedOrder.
    """

    def __init__(self) -> None:
        self._fixed_order = FixedOrder()
        self._collusion = Collusion()

    def vote(
        self,
        voter: PlayerID,
        alive: list[PlayerID],
        seating: list[PlayerID],
        traitors: set[PlayerID],
        is_traitor: bool,
        history: list[RoundRecord],
        known_traitors: set[PlayerID],
    ) -> PlayerID:
        if is_traitor is False:
            return self._fixed_order.vote(
                voter, alive, seating, traitors, is_traitor, history, known_traitors
            )
        n_alive = len(alive)
        n_traitors_alive = sum(1 for player in alive if player in traitors)
        if n_alive <= 2 * n_traitors_alive + 2:
            faithful_players = [
                player for player in alive if player not in traitors and player != voter
            ]
            if n_traitors_alive == 1:
                own_target = self._fixed_order.vote(
                    voter, alive, seating, traitors, is_traitor, history, known_traitors
                )
                forcing_targets = [
                    player for player in faithful_players if player != own_target
                ]
                return random.choice(forcing_targets)
            if len(faithful_players) > 0:
                return self._collusion.vote(
                    voter, alive, seating, traitors, is_traitor, history, known_traitors
                )
        return self._fixed_order.vote(
            voter, alive, seating, traitors, is_traitor, history, known_traitors
        )

    def __repr__(self) -> str:
        return "OptimalTimingDeviation()"


class FixedOrderThenRandom:
    """Play FixedOrder in the main game, then vote at random in the late game.

    The late game is the set of states with n <= 2m + 2, in which punishment
    can no longer deter a deviation because colluding Traitors reach parity
    before the punishment round. The number of surviving Traitors is public:
    it is the initial number of Traitors less those banished so far, which
    the strategy reads from the game history. Use it with
    ``TraitorsGame(..., late_game_detection=False)`` so that late-game votes
    are not treated as deviations.

    Parameters
    ----------
    n_traitors : int
        The number of Traitors at the start of the game.

    Raises
    ------
    ValueError
        If ``n_traitors`` is less than one.
    """

    def __init__(self, n_traitors: int) -> None:
        if n_traitors < 1:
            raise ValueError(f"n_traitors must be at least 1, got {n_traitors}")
        self.n_traitors = n_traitors
        self._fixed_order = FixedOrder()
        self._random_vote = RandomVote()

    def vote(
        self,
        voter: PlayerID,
        alive: list[PlayerID],
        seating: list[PlayerID],
        traitors: set[PlayerID],
        is_traitor: bool,
        history: list[RoundRecord],
        known_traitors: set[PlayerID],
    ) -> PlayerID:
        banished_traitors = sum(1 for record in history if record["was_traitor"])
        traitors_alive = self.n_traitors - banished_traitors
        strategy = (
            self._random_vote
            if len(alive) <= 2 * traitors_alive + 2
            else self._fixed_order
        )
        return strategy.vote(
            voter, alive, seating, traitors, is_traitor, history, known_traitors
        )

    def __repr__(self) -> str:
        return f"FixedOrderThenRandom(n_traitors={self.n_traitors})"


class FixedOrderThenFirst:
    r"""Play FixedOrder in the main game, then vote for the first player.

    In the late game ($n \leq 2m + 2$) every player votes for the first
    surviving player in the seating order, and that player votes for the
    second, so the first player is banished whatever the Traitors do. The
    number of surviving Traitors is read from the game history, as in
    `FixedOrderThenRandom`. Use it with
    ``TraitorsGame(..., late_game_detection=False)`` so that late-game votes
    are not treated as deviations.

    Parameters
    ----------
    n_traitors : int
        The number of Traitors at the start of the game.

    Raises
    ------
    ValueError
        If ``n_traitors`` is less than one.
    """

    def __init__(self, n_traitors: int) -> None:
        if n_traitors < 1:
            raise ValueError(f"n_traitors must be at least 1, got {n_traitors}")
        self.n_traitors = n_traitors
        self._fixed_order = FixedOrder()

    def vote(
        self,
        voter: PlayerID,
        alive: list[PlayerID],
        seating: list[PlayerID],
        traitors: set[PlayerID],
        is_traitor: bool,
        history: list[RoundRecord],
        known_traitors: set[PlayerID],
    ) -> PlayerID:
        banished_traitors = sum(1 for record in history if record["was_traitor"])
        traitors_alive = self.n_traitors - banished_traitors
        if len(alive) > 2 * traitors_alive + 2:
            return self._fixed_order.vote(
                voter, alive, seating, traitors, is_traitor, history, known_traitors
            )
        alive_set = set(alive)
        ordered_alive = [player for player in seating if player in alive_set]
        if ordered_alive[0] == voter:
            return ordered_alive[1]
        return ordered_alive[0]

    def __repr__(self) -> str:
        return f"FixedOrderThenFirst(n_traitors={self.n_traitors})"


class PlanningMurder:
    """Murder the Faithful player that is best for the Traitors.

    For use when the Faithful vote for the first player in the order, either
    throughout the game or in the late game only (see
    `traitor_win_prob_concentrated`). The order is that of the player
    identifiers, which is the seating order of `TraitorsGame`. The victim is
    chosen by the exact dynamic programme behind
    `traitor_win_prob_concentrated` and `traitor_win_prob_first_player`.

    Parameters
    ----------
    vote_left_main_game : bool
        Whether the Faithful play Vote-Left in the main game (true) or vote
        for the first player throughout (false).
    """

    def __init__(self, vote_left_main_game: bool = True) -> None:
        self.vote_left_main_game = vote_left_main_game

    def choose_victim(
        self,
        traitors_alive: list[PlayerID],
        faithful_alive: list[PlayerID],
        history: list[RoundRecord],
    ) -> PlayerID:
        traitor_set = set(traitors_alive)
        ordered_alive = sorted(traitors_alive + faithful_alive)
        best_victim = faithful_alive[0]
        best_value = -1.0
        for victim in sorted(faithful_alive):
            roles = tuple(
                player in traitor_set for player in ordered_alive if player != victim
            )
            victim_value = _ordered_vote_value(roles, self.vote_left_main_game)
            if victim_value > best_value:
                best_victim = victim
                best_value = victim_value
        return best_victim

    def __repr__(self) -> str:
        return f"PlanningMurder(vote_left_main_game={self.vote_left_main_game})"


class RandomMurder:
    """Murder a uniformly random surviving Faithful."""

    def choose_victim(
        self,
        traitors_alive: list[PlayerID],
        faithful_alive: list[PlayerID],
        history: list[RoundRecord],
    ) -> PlayerID:
        return random.choice(faithful_alive)

    def __repr__(self) -> str:
        return "RandomMurder()"
