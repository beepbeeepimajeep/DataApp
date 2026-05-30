# gpt5_4 Response

## Prompt
```
Let $n > 1$ be an integer. In a configuration of an $n \times n$ board, each of the $n^2$ cells contains an arrow, either pointing up, down, left, or right. Given a starting configuration, Turbo the snail starts in one of the cells of the board and travels from cell to cell. In each move, Turbo moves one square unit in the direction indicated by the arrow in her cell (possibly leaving the board). After each move, the arrows in all of the cells rotate $90^{\circ}$ counterclockwise. We call a cell good if, starting from that cell, Turbo visits each cell of the board exactly once, without leaving the board, and returns to her initial cell at the end. Let $S(n)$ denote the maximum number of good cells over all possible starting configurations.

Compute $\sum_{n=10}^{20} S(n)$.


Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We are asked to find the maximum possible number of good starting cells on an \(n\times n\) board, call it \(S(n)\), and then compute
\[
\sum_{n=10}^{20} S(n).
\]

## 1. Reformulating the motion

Label directions by numbers mod \(4\):
\[
\text{right}=0,\quad \text{up}=1,\quad \text{left}=2,\quad \text{down}=3.
\]
If a cell initially has direction \(a\), then after \(t\) moves its arrow points in direction \(a+t \pmod 4\), since every move rotates all arrows \(90^\circ\) counterclockwise.

So if Turbo is in cell \(c\) at time \(t\), her move is determined by
\[
a(c)+t \pmod 4.
\]

Thus the process is a deterministic walk on the state space
\[
(\text{cell}, t \bmod 4).
\]

A starting cell is good if the walk starting at time \(0\) from that cell visits all \(n^2\) cells exactly once and returns to the start after \(n^2\) moves.

## 2. A necessary condition: parity of \(n\)

Color the board like a chessboard. Every move goes to an adjacent cell, so Turbo alternates colors every step.

If she visits all \(n^2\) cells exactly once and returns to the starting cell after \(n^2\) moves, then after \(n^2\) moves she must be back on the same color. Hence \(n^2\) must be even, so \(n\) must be even.

Therefore
\[
S(n)=0 \qquad \text{for odd } n.
\]

So only even \(n\in\{10,12,14,16,18,20\}\) matter.

## 3. Upper bound for even \(n\)

Suppose a cell \(c\) is good. Starting from \(c\) at time \(0\), Turbo follows a Hamiltonian cycle of length \(n^2\) through the board.

Now compare starting from another cell \(d\). Since the arrow pattern depends on time mod \(4\), shifting the starting point along the same Hamiltonian cycle only works if the time offset is compatible mod \(4\). In particular, if two starting cells lie at positions along the cycle differing by \(k\), then the walk from the later one sees all arrows \(k\) time-steps later. For it to trace the same cycle structure, we need \(k\equiv 0\pmod 4\).

Hence among the \(n^2\) cells on a Hamiltonian cycle, at most one residue class mod \(4\) along the cycle can be good. So
\[
S(n)\le \frac{n^2}{4}.
\]

## 4. Achievability for even \(n\)

We now show this bound is attainable for every even \(n\), so
\[
S(n)=\frac{n^2}{4}.
\]

Construct a Hamiltonian cycle on the \(n\times n\) board. Since \(n\) is even, such a cycle exists.

Index the cells along this cycle as
\[
v_0,v_1,\dots,v_{n^2-1}
\]
in cyclic order.

For each \(i\), define the initial arrow in \(v_i\) to point toward \(v_{i+1}\) after compensating for the time \(i\): namely choose the initial direction so that after \(i\) counterclockwise rotations it points from \(v_i\) to \(v_{i+1}\). This makes the walk starting from \(v_0\) follow the Hamiltonian cycle exactly.

Now if we start from \(v_{4m}\), then at step \(t\) the arrow in \(v_{4m+t}\) has rotated by \(t\), and because \(4m\equiv 0\pmod 4\), the same compensation works. So the walk again follows the same Hamiltonian cycle, just starting at a different point. Thus every \(v_i\) with \(i\equiv 0\pmod 4\) is good.

There are exactly
\[
\frac{n^2}{4}
\]
such cells, so
\[
S(n)\ge \frac{n^2}{4}.
\]
Combined with the upper bound,
\[
S(n)=\frac{n^2}{4}\qquad \text{for even }n.
\]

Therefore
\[
S(n)=
\begin{cases}
\dfrac{n^2}{4}, & n \text{ even},\\[4pt]
0, & n \text{ odd}.
\end{cases}
\]

## 5. Compute the sum

So
\[
\sum_{n=10}^{20} S(n)
=
\frac{10^2+12^2+14^2+16^2+18^2+20^2}{4}.
\]
Compute:
\[
100+144+196+256+324+400=1420.
\]
Thus
\[
\sum_{n=10}^{20} S(n)=\frac{1420}{4}=355.
\]

\[
\boxed{355}
\]

## Metadata
- Model: gpt-5.4
- Input tokens: 349
- Output tokens: 1157
- Hit token cap: False
- Generation time: 14.99s
- Request ID: chatcmpl-DhGT8Uqtb8mSKQq4ca4NyzOwVDK3x
