# GPT-5.5 xhigh Response

## Prompt
```

```

## Reasoning + Response
We need the largest number of edges a connected graph on \(2n\) vertices can have while still allowing Alice to evade forever.

If a graph has a universal vertex \(u\), then Bob wins: wherever Bob starts, on his first move he can move to \(u\). Once Bob is at \(u\), after Alice moves to any vertex, Bob can move there and catch her since \(u\) is adjacent to every vertex.

So for Alice to evade indefinitely, the graph cannot have a universal vertex. Hence every vertex must be missing at least one edge. In the complement graph, every vertex has degree at least \(1\), so the complement has at least

\[
\frac{2n}{2}=n
\]

edges. Therefore the original graph has at most

\[
\binom{2n}{2}-n
= n(2n-1)-n
=2n(n-1)
\]

edges.

This bound is attainable: take \(K_{2n}\) and remove a perfect matching. Each vertex has exactly one non-neighbor. Alice chooses Bob’s starting vertex \(b\), then starts somewhere adjacent to the unique non-neighbor of \(b\). On each turn, if Bob is at \(v\), Alice moves to the unique non-neighbor of \(v\). Bob can never move directly to her vertex, so she evades forever.

Thus the maximum possible number of edges is

\[
\boxed{2n(n-1)}
\]

## Metadata
- Model: gpt-5.5
- Input tokens: 309
- Output tokens: 9639
- Reasoning tokens: 9215
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-Dhxlp7LGoerfHoVxjzCbnBpfGsySi
- Via batch: True
