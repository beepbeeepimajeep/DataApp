# gpt5_4 Response

## Prompt
```
Rose and Brunno play the game on a board shaped like a regular 1001-gon. Initially, all vertices of the board are white, and there is a chip at one of them. On each turn, Rose chooses an arbitrary positive integer \( k \), then Brunno chooses a direction: clockwise or counterclockwise, and moves the chip in the chosen direction by \( k \) vertices. If at the end of the turn the chip stands at a white vertex, this vertex is painted red.

Find the greatest number of vertices that Rose can make red regardless of Brunno's actions, if the number of turns is not limited.

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We are asked for the maximum number of vertices Rose can guarantee to become red on a regular \(1001\)-gon, no matter how Brunno chooses directions.

Let the vertices be the elements of \(\mathbb Z_{1001}\), with the chip starting at \(0\).

On each turn, Rose chooses \(k>0\), and Brunno moves the chip by either \(+k\) or \(-k\) mod \(1001\).  
So after a sequence of chosen lengths \(k_1,k_2,\dots,k_t\), the chip can be at any point of the form
\[
\pm k_1 \pm k_2 \pm \cdots \pm k_t \pmod{1001},
\]
depending on Brunno's choices.

We need the largest number of vertices Rose can force to be visited (and hence painted red).

## Key invariant: all reachable positions lie in one coset of a subgroup

Let
\[
d=\gcd(1001,k_1,k_2,\dots).
\]
Every position of the chip is a sum of \(\pm k_i\), hence is divisible by \(d\) modulo \(1001\). So all positions always lie in the subgroup
\[
d\mathbb Z_{1001},
\]
which has size
\[
\frac{1001}{d}.
\]
Therefore, if all chosen \(k_i\) have common gcd \(d>1\) with \(1001\), Rose can never get outside that set.

So to maximize the number of possible red vertices, Rose must make the overall gcd equal to \(1\). Then in principle all \(1001\) vertices are not excluded by this invariant.

But Brunno controls the signs, so Rose may still be unable to force all \(1001\) vertices red.

## Brunno’s pairing strategy

The crucial idea is that Brunno can always keep the chip inside one part of a partition into pairs.

Since \(1001\) is odd, for every nonzero \(x\in \mathbb Z_{1001}\), the two vertices \(x\) and \(-x\) are distinct. Thus the \(1000\) nonzero vertices split into \(500\) pairs
\[
\{x,-x\},
\]
plus the single vertex \(0\).

Now suppose before a turn the chip is at \(v\), and Rose chooses \(k\). Brunno may move to either
\[
v+k \quad\text{or}\quad v-k.
\]
These two candidate vertices satisfy
\[
(v+k)+(v-k)=2v.
\]
More importantly, they are symmetric about \(v\), and Brunno can always choose between them.

Brunno’s goal is to avoid creating too many new red vertices. He can do this by ensuring that from each pair \(\{x,-x\}\), at most one vertex ever gets visited unless forced.

Why is this possible? If one of \(v+k\) and \(v-k\) is already red, Brunno chooses that one. If neither is red, then they belong to two opposite locations relative to \(v\), and Brunno may choose one representative to keep future play consistent. This allows him to prevent both members of any opposite pair from being forced red.

Hence Rose cannot guarantee more than:
- the initial vertex \(0\), and
- at most one vertex from each of the \(500\) opposite pairs.

So Rose cannot force more than
\[
1+500=501
\]
vertices to become red.

## Rose can guarantee 501 vertices

Now we show Rose can force \(501\).

Rose uses this strategy: on each turn, choose \(k\) so that the two possible destinations \(v+k\) and \(v-k\) are both currently white whenever possible.

As long as fewer than \(501\) vertices are red, there are fewer than \(500\) red nonzero vertices, so fewer than \(500\) opposite pairs have been hit. Hence there exists an unused pair \(\{x,-x\}\). From the current position \(v\), choosing
\[
k \equiv x-v \pmod{1001}
\]
makes the two possible destinations exactly \(x\) and \(2v-x\); by choosing appropriately among unused pairs, Rose can ensure Brunno must land on a new white vertex. Repeating this, she can force a new red vertex each turn until \(501\) vertices are red.

Thus \(501\) is achievable.

Therefore, the greatest number of vertices Rose can guarantee is

\[
\boxed{501}
\]

## Metadata
- Model: gpt-5.4
- Input tokens: 291
- Output tokens: 979
- Hit token cap: False
- Generation time: 16.19s
- Request ID: chatcmpl-DhGHw9KovqhHwbNgfRDxmW3Rptn2r
