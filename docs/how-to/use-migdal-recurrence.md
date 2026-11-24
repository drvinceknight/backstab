# Use Win Probability Recurrences

`backstab` provides four exact recurrences for the Traitor win probability
under different strategy profiles. All return `fractions.Fraction` values so
the results are exact rational numbers.

## Migdał recurrence (random or fixed order voting, $w$)

Under mutual random voting Faithful and Traitors both vote uniformly
the Traitor win probability from state $(n, m)$ is given by the
Migdał recurrence:

```python
>>> import backstab
>>> probability = backstab.traitor_win_prob(n=22, m=3)
>>> probability
Fraction(33901, 45056)
>>> float(probability)
0.7524...

```

## RV+C recurrence (Traitor collusion, $w_{\ddagger}$)

When the Faithful continue to vote randomly but all Traitors collude on a
single Faithful target each round, the Traitor win probability increases.
We compute this with `traitor_win_prob_collusion`:

```python
>>> p_rvc = backstab.traitor_win_prob_collusion(n=8, m=2)
>>> float(p_rvc)
0.9203...

```

The underlying helper computes the exact banishment probability by summing
over vote-count classes with generating functions, rather than enumerating every
voting profile, so it is fast across the televised range:

```python
>>> p_rvc = backstab.traitor_win_prob_collusion(n=22, m=3)
>>> float(p_rvc)
0.9452...

```

## VL+Opt recurrence (optimal Traitor deviation, $w_{\dagger}$)

Under Vote-Left (Faithful vote cyclically) with the optimal Traitor strategy
$\sigma_{\dagger}$: comply for `n > 2m+2`, collude otherwise, the Traitor win probability
is computed by `traitor_win_prob_vlopt`. This recurrence is exact and fast
for any $(n, m)$:

```python
>>> p_dag = backstab.traitor_win_prob_vlopt(n=22, m=3)
>>> float(p_dag)
0.8641...

```

## Switching recurrence (Vote-Left then random voting, $w_{s}$)

When the Faithful play Vote-Left while `n > 2m+2` and switch to random voting in
the late game, the main game follows the VL+Opt recurrence and the late-game
states take their RV+C values. We compute this with `traitor_win_prob_switch`:

```python
>>> p_switch = backstab.traitor_win_prob_switch(n=22, m=3)
>>> float(p_switch)
0.7756...

```

## Voting for the first player in the order

A deterministic alternative to random voting is for every player to vote for the
first surviving player in the public order, who votes for the second. The
Faithful then decide every banishment, but the banishment order is known in
advance, and the Traitors use their murders to protect themselves. We compute the
Traitor win probability, with the Traitors choosing every murder optimally, using
`traitor_win_prob_first_player`:

```python
>>> p_first = backstab.traitor_win_prob_first_player(n=15, m=2)
>>> float(p_first)
0.8

```

The concentrated vote can also be used only in the late game, after Vote-Left in
the main game. The Traitors then plan their murders during the main game so that
a Faithful player is first in the order when the late game begins, and the result
is worse for the Faithful than switching to random voting:

```python
>>> p_concentrated = backstab.traitor_win_prob_concentrated(n=15, m=2)
>>> float(p_concentrated)
0.6876...
>>> float(backstab.traitor_win_prob_switch(n=15, m=2))
0.5986...

```

Both functions are dynamic programmes over the order of the roles, so they are
slower than the recurrences above: a few seconds at 25 players and four Traitors.
