# item_0419 — gpt-5.4 retry

## Reasoning + Response
We are asked for the largest number of edges a connected graph on \(2n\) vertices can have while still allowing Alice, with optimal choice of starting positions and play, to avoid Bob forever.

The key is to characterize exactly when Bob can force a capture.

### 1. A sufficient condition for Alice to evade forever
If the graph is bipartite with parts of size \(n\) and \(n\), then Alice can evade forever.

Why: let the bipartition be \(X\sqcup Y\), and Alice chooses both starting positions in the same part, say \(X\). Since every move crosses from one part to the other, after each round both tokens are again in the same part. So at all times they remain in the same part immediately before the player to move acts.

If Bob ever caught Alice, both tokens would have to occupy the same vertex. But that would require Bob to move onto Alice’s current vertex, which lies in the opposite part from Bob’s current position. Since Alice and Bob always start each Bob-turn in the same part, Bob can never be adjacent to Alice’s vertex at that moment. So capture never occurs.

Thus any connected balanced bipartite graph works. The maximum number of edges in such a graph is achieved by the complete bipartite graph \(K_{n,n}\), which has
\[
n^2
\]
edges.

So the answer is at least \(n^2\).

---

### 2. Why any graph with more than \(n^2\) edges lets Bob force capture
We show that if a graph on \(2n\) vertices has more than \(n^2\) edges, then it is not bipartite. Indeed, among all bipartite graphs on \(2n\) vertices, the maximum number of edges is \(n^2\), attained by \(K_{n,n}\). So \(m>n^2\) implies the graph contains an odd cycle.

Now we use a standard fact from pursuit on graphs: on a connected graph, if the graph is not bipartite, then Bob can force a capture.

Reason: fix any starting positions. Because the graph is connected and contains an odd cycle, there exist both even-length and odd-length walks between suitable vertices; equivalently, Bob can adjust the parity of his route. He can therefore move along a shortest path toward Alice while matching the parity needed to land on her vertex on his turn. Since Alice moves only one edge each turn, Bob can keep reducing the distance whenever it is positive, and the odd cycle removes the parity obstruction that is the only thing preventing capture in bipartite graphs.

So in any connected non-bipartite graph, Bob has a winning strategy. Therefore, for Alice to evade indefinitely, the graph must be bipartite.

Hence the maximum possible number of edges is exactly the maximum number of edges in a connected bipartite graph on \(2n\) vertices, namely
\[
n^2.
\]

Therefore the required maximum is \(\boxed{n^2}\).

## Metadata
- Model: gpt-5.4
- Input tokens: 309
- Output tokens: 636
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-Dl9kGe4Owa9JHwx46OmqSA8dqM0ES
- Via batch: True