# gpt_oss Response

## Prompt
```
Let $n > 1$ be an integer. In a configuration of an $n \times n$ board, each of the $n^2$ cells contains an arrow, either pointing up, down, left, or right. Given a starting configuration, Turbo the snail starts in one of the cells of the board and travels from cell to cell. In each move, Turbo moves one square unit in the direction indicated by the arrow in her cell (possibly leaving the board). After each move, the arrows in all of the cells rotate $90^{\circ}$ counterclockwise. We call a cell good if, starting from that cell, Turbo visits each cell of the board exactly once, without leaving the board, and returns to her initial cell at the end. Let $S(n)$ denote the maximum number of good cells over all possible starting configurations.

Compute $\sum_{n=10}^{20} S(n)$.


Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
The arrows rotate uniformly, so after \(t\) moves the arrow that was initially in a cell points in the direction obtained by rotating the initial arrow \(t\) times \(90^{\circ}\) counter‑clockwise.  
If a Hamiltonian cycle (a tour that visits every cell exactly once and returns to the start) is fixed, we may assign to each cell the time \(t\) at which it is visited.  
For a cell \(c\) visited at time \(t\) whose successor in the cycle is the adjacent cell \(c'\), the initial arrow in \(c\) must be the direction from \(c\) to \(c'\) rotated \(-t\) (i.e. rotated clockwise \(t\) times).  
Thus any Hamiltonian cycle determines a unique arrow configuration that makes the tour work for the chosen starting cell.

To have many good starting cells the same arrow configuration must support many Hamiltonian cycles, each being a cyclic shift of the same underlying cycle.  
The only way this can happen is when the underlying cycle itself is a single \(n^{2}\)-cycle of the time‑dependent transition function; then every starting cell on that cycle is good.  

Such a cycle exists exactly when the board is traversed column‑by‑column (or row‑by‑row) in a “snake’’ pattern.  
In this pattern the cells of one fixed column (say the first column) are visited at times congruent to \(0,1,\dots ,n-1\) modulo \(n\); the required initial arrows can be chosen so that the tour works from any of those \(n\) cells, while any other cell would require an initial move that leaves the board. Consequently the maximum possible number of good cells for an \(n\times n\) board is  

\[
S(n)=n .
\]

Therefore  

\[
\sum_{n=10}^{20} S(n)=\sum_{n=10}^{20} n
= \frac{(10+20)\times 11}{2}=165 .
\]

\[
\boxed{165}
\]

## Metadata
- Model: api-gpt-oss-120b
- Input tokens: 410
- Output tokens: 3291
- Hit token cap: False
- Generation time: 18.00s
- Request ID: chatcmpl-b68edce128fad529
