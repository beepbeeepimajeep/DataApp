# sonnet Response

## Prompt
```
Let $n > 1$ be an integer. In a configuration of an $n \times n$ board, each of the $n^2$ cells contains an arrow, either pointing up, down, left, or right. Given a starting configuration, Turbo the snail starts in one of the cells of the board and travels from cell to cell. In each move, Turbo moves one square unit in the direction indicated by the arrow in her cell (possibly leaving the board). After each move, the arrows in all of the cells rotate $90^{\circ}$ counterclockwise. We call a cell good if, starting from that cell, Turbo visits each cell of the board exactly once, without leaving the board, and returns to her initial cell at the end. Let $S(n)$ denote the maximum number of good cells over all possible starting configurations.

Compute $\sum_{n=10}^{20} S(n)$.


Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
I need to find S(n) for n = 10 to 20, where S(n) is the maximum number of good cells over all configurations of an n×n board.

## Understanding the Problem

Turbo starts at a cell, follows arrows, and after each move all arrows rotate 90° CCW. She must visit all n² cells exactly once and return to start.

## Key Observations

**Arrow rotation:** After each move, all arrows rotate 90° CCW. So if Turbo makes move k, the arrows have rotated k times from the initial configuration. The arrow in cell (i,j) at step k points in direction: (initial direction + k·90° CCW).

**The path structure:** The path must be a Hamiltonian cycle of length n². 

**Parity/coloring argument:** Color the board like a checkerboard. Each move changes the cell's color (since moving up/down/left/right changes parity of coordinates). So the path alternates colors, requiring n² to be even, i.e., n must be even for a Hamiltonian cycle on a checkerboard (since we need equal numbers of black and white cells, which requires n² even, so n even).

Wait, n² cells with a cycle of length n²: we need n² even, so n must be even.

For odd n: n² is odd, so a Hamiltonian cycle (returning to start with n² steps) would require n² even (since checkerboard coloring alternates). This means **S(n) = 0 for odd n**.

For even n: A Hamiltonian cycle is potentially possible.

## Result from Competition

This is ISL 2024 or similar competition problem. The answer for S(n):
- S(n) = 0 when n is odd
- S(n) = n² when n is even (all cells can be good cells simultaneously)

Wait, let me reconsider. The problem asks for the maximum number of good cells. If a configuration has a Hamiltonian cycle, how many starting cells are "good"?

If Turbo starts at any cell on the Hamiltonian cycle, she traverses all n² cells. But the arrow configuration changes based on how many steps have been taken. Starting from a different cell on the same cycle means the arrows have been pre-rotated differently... actually no, the starting configuration is fixed, and we choose the starting cell.

If the path is a fixed sequence of cells c₀, c₁, ..., c_{n²-1}, c_{n²}=c₀, then starting from c₀ works. Starting from c₁: Turbo is at c₁ with the original arrow configuration. The arrow at c₁ initially pointed toward c₂ (in the original path), so Turbo would go to c₂, then arrows rotate... This would trace c₁→c₂→...→c_{n²-1}→c₀→c₁, which IS a valid Hamiltonian cycle visiting all cells!

So if ANY starting cell works, ALL cells on the cycle work, meaning all n² cells are good (since the cycle covers all cells). So S(n) = n² for even n, and S(n) = 0 for odd n.

But wait - we need to verify such a configuration exists for even n. For even n ≥ 2, one can construct snake-like Hamiltonian cycles, so S(n) = n² for even n.

Actually, I should double-check the odd case more carefully. For odd n, the checkerboard argument: in n² steps returning to start, we alternate black/white, so we'd need equal black and white cells visited, but n² odd means unequal counts. This confirms S(n) = 0 for odd n.

## Computing the Sum

For n = 10 to 20:
- Even n: 10, 12, 14, 16, 18, 20 → S(n) = n²
- Odd n: 11, 13, 15, 17, 19 → S(n) = 0

Sum = 10² + 12² + 14² + 16² + 18² + 20²
= 100 + 144 + 196 + 256 + 324 + 400
= 1420

Let me verify: 100 + 144 = 244, + 196 = 440, + 256 = 696, + 324 = 1020, + 400 = 1420.

\boxed{1420}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 387
- Output tokens: 1062
- Hit token cap: False
- Generation time: 17.69s
- Request ID: msg_0143f1WDgWq4YtopwMdYTW3i
