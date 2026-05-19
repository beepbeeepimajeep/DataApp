# GPT-5.5 xhigh Response

## Prompt
```
Rose and Brunno play the game on a board shaped like a regular 1001-gon. Initially, all vertices of the board are white, and there is a chip at one of them. On each turn, Rose chooses an arbitrary positive integer \( k \), then Brunno chooses a direction: clockwise or counterclockwise, and moves the chip in the chosen direction by \( k \) vertices. If at the end of the turn the chip stands at a white vertex, this vertex is painted red.

Find the greatest number of vertices that Rose can make red regardless of Brunno's actions, if the number of turns is not limited.

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We need find the maximum number of vertices Rose can force to become red.

Label the vertices by the cyclic group \(\mathbb Z_{1001}\). A move from \(x\) by \(k\) goes to either \(x+k\) or \(x-k\).

Call a nonempty set \(T\) a trap if, whenever the chip is in \(T\), Brunno can keep it in \(T\); that is, for every \(x\in T\) and every \(k\), at least one of \(x+k,x-k\) lies in \(T\).

Let \(W=\mathbb Z_{1001}\setminus T\). If \(a,b\in W\), then their midpoint \((a+b)/2\) cannot lie in \(T\), because from that midpoint Rose could choose \(k=(a-b)/2\), making both possible endpoints \(a,b\) outside \(T\). Hence \(W\) is closed under midpoints.

Since \(1001\) is odd, division by \(2\) is valid modulo \(1001\). A midpoint-closed subset of a finite cyclic group of odd order is a coset of a subgroup: after translating it to contain \(0\), midpoint closure gives closure under halving, hence under doubling, and therefore under addition.

Thus \(W\) is a coset of a subgroup. The largest proper subgroup of \(\mathbb Z_{1001}\) has size

\[
\frac{1001}{7}=143,
\]

since \(1001=7\cdot 11\cdot 13\). Therefore every nonempty trap has size at least

\[
1001-143=858.
\]

Brunno can achieve this bound: choose a coset \(W\) of size \(143\) not containing the starting vertex, and always move so that the chip stays in \(T=\mathbb Z_{1001}\setminus W\). This is possible because two endpoints in \(W\) would have midpoint in \(W\), not in \(T\). Hence Rose cannot force more than \(858\) red vertices.

Conversely, Rose can force at least \(858\). She first paints the starting vertex by choosing \(k=1001\). Then, whenever the chip is at a vertex, she cycles through all residues \(k\pmod{1001}\). If fewer than \(858\) vertices ever became red, then eventually the red set would stop changing. The vertices visited infinitely often would form a nonempty trap of size less than \(858\), contradicting the lower bound on trap size.

So the greatest guaranteed number is

\[
\boxed{858}
\]

## Metadata
- Model: gpt-5.5
- Input tokens: 291
- Output tokens: 13005
- Reasoning tokens: 12286
- Hit token cap: False
- Finish reason: stop
- Generation time: 270.50s
- Request ID: chatcmpl-DhGYBgazYQLSEkoLhwFr15QFm0Im1
