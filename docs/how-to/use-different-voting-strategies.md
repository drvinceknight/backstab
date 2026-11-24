# Use different voting strategies

The `TraitorsGame` class can take different voting strategies for traitors
and/or faithful:

```python
>>> import backstab
>>> game = backstab.TraitorsGame(n_players=9, n_traitors=3)
>>> game.simulate(n=1000, seed=0, faithful=backstab.FixedOrder(), traitor=backstab.Collusion())
SimulationResults(n=1000, P(F)=0.985 [0.977,0.993], avg_rounds=4.0)

```

Here are the available strategies:

```python
>>> backstab.FixedOrder()
FixedOrder()
>>> backstab.RandomVote()
RandomVote()
>>> backstab.Collusion()
Collusion()
>>> backstab.MixedDeviation()
MixedDeviation(p=0.2)
>>> backstab.RampDeviation()
RampDeviation(p_start=0.0, p_end=1.0)
>>> backstab.ThresholdDeviation()
ThresholdDeviation(threshold=8, p_late=1.0)
>>> backstab.OptimalTimingDeviation()
OptimalTimingDeviation()
>>> backstab.FixedOrderThenRandom(n_traitors=3)
FixedOrderThenRandom(n_traitors=3)

```

## Use Random Voting

We need to disable `detect`:

```python
>>> game = backstab.TraitorsGame(n_players=9, n_traitors=3, detect=False)
>>> game.simulate(n=1000, seed=0, faithful=backstab.RandomVote(), traitor=backstab.RandomVote())
SimulationResults(n=1000, P(F)=0.132 [0.111,0.153], avg_rounds=2.9)

```

## Use Collusion

```python
>>> game.simulate(n=1000, seed=0, faithful=backstab.RandomVote(), traitor=backstab.Collusion())
SimulationResults(n=1000, P(F)=0.004 [0.000,0.008], avg_rounds=2.1)

```

## Use detection and Fixed Order

We need to enable `detect` (this is `True` by default):

```python
>>> game = backstab.TraitorsGame(n_players=9, n_traitors=3, detect=True)
>>> game.simulate(n=1000, seed=0, faithful=backstab.FixedOrder(), traitor=backstab.Collusion())
SimulationResults(n=1000, P(F)=0.985 [0.977,0.993], avg_rounds=4.0)

```

## Use Fixed Order with Detection and Optimal Timing Deviation

```python
>>> game.simulate(n=1000, seed=0, faithful=backstab.FixedOrder(), traitor=backstab.OptimalTimingDeviation())
SimulationResults(n=1000, P(F)=0.018 [0.010,0.026], avg_rounds=2.4)

```

## Switch from Fixed Order to Random Voting in the late game

Once \(n \leq 2m + 2\), colluding Traitors reach parity before any punishment can
take place, so we can have the Faithful switch to random voting at that point. We
switch off late-game detection so that the late-game random votes are not treated
as deviations:

```python
>>> game = backstab.TraitorsGame(n_players=9, n_traitors=3, late_game_detection=False)
>>> game.simulate(n=1000, seed=0, faithful=backstab.FixedOrderThenRandom(n_traitors=3), traitor=backstab.OptimalTimingDeviation())
SimulationResults(n=1000, P(F)=0.055 [0.041,0.069], avg_rounds=2.4)

```
