# sonnet Response

## Prompt
```
Alice and Bob play a game on a connected graph with $2n$ vertices, where $n\in \mathbb{N}$ and $n>1$.. Alice and Bob have tokens named A and B respectively. They alternate their turns with Alice going first. Alice gets to decide the starting positions of A and B. Every move, the player with the turn moves their token to an adjacent vertex. Bob's goal is to catch Alice, and Alice's goal is to prevent this. Note that positions of A, B are visible to both Alice and Bob at every moment.

Provided they both play optimally, what is the maximum possible number of edges in the graph if Alice is able to evade Bob indefinitely?

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
I need to find the maximum number of edges in a connected graph on 2n vertices such that Alice can evade Bob indefinitely, when both play optimally.

## Setting Up the Problem

Alice places both tokens (she chooses starting positions for both A and B). Alice moves first, then they alternate. Bob catches Alice if B occupies the same vertex as A.

Alice can evade indefinitely if she has a strategy to never be on the same vertex as Bob.

## Key Insight: Bipartite Graphs

On a bipartite graph, if Alice places A and B on vertices of **different** parts (one in each partition), then after each full round (Alice moves, then Bob moves), both tokens move once. 

In a bipartite graph with parts X and Y: if A starts in X and B starts in Y, then after Alice's move, A is in Y and B is in Y. Wait, that's potentially dangerous.

Let me reconsider. After Alice moves: A goes from X to Y. After Bob moves: B goes from Y to X. So after each full round, A is in Y→X and B is in Y→X... Let me track parities.

- Start: A in X (parity 0), B in Y (parity 1). Different parities.
- After Alice moves: A in Y (parity 1), B in Y (parity 1). **Same parity** - Bob could catch Alice here.
- After Bob moves: A in Y (parity 1), B in X (parity 0). Different parities again.

So Bob can only catch Alice right after Alice moves (when both are in Y). Alice needs to ensure Bob can't reach her position in Y after she moves.

## Strategy on Bipartite Graphs

If Alice places A and B in **same** partition initially: A in X, B in X. After Alice moves: A in Y, B in X (different parts - safe). After Bob moves: A in Y, B in Y (same part). Now Bob might catch Alice.

Actually, the parity argument: place A and B in the **same** partition. Then after Alice's move they're in different partitions (safe from immediate capture), after Bob's move they're both in same partition again. 

For Alice to evade indefinitely on a bipartite graph with Alice choosing start positions: Alice puts A and B in the same partition. Then Bob can never catch Alice because whenever Bob moves, both are in the same partition but Bob needs to land on Alice's exact vertex. Alice can use the structure to stay away.

On a complete bipartite graph $K_{n,n}$: Alice places A and B both in part X. After Alice moves, A is in Y (she picks any vertex in Y). After Bob moves, B goes to Y. Alice has n choices in Y, Bob is at one vertex in Y. Alice can always pick a different vertex in Y next turn (since from any Y vertex, Alice can reach all X vertices, then all Y vertices). 

In $K_{n,n}$, Alice can always evade: when Alice is in Y (n vertices) and Bob is about to move into Y, Alice on her next turn moves to X, then Bob moves to X. Alice has n choices in X, Bob occupies one — Alice avoids it. This works as long as n > 1.

## Maximum Edges

The maximum edges in a connected graph on 2n vertices where Alice can evade is achieved by $K_{n,n}$ (complete bipartite graph), which has $n^2$ edges.

Can we do better? Can Alice evade on a graph with more than $n^2$ edges?

If we add any edge within a partition of $K_{n,n}$, say between two vertices in X, the graph is no longer bipartite. Non-bipartite graphs contain odd cycles. 

On a non-bipartite graph, the parity argument breaks down. Bob can potentially synchronize parities. In fact, it's known that on non-bipartite connected graphs, the cop (Bob) can always catch the robber (Alice) — this relates to the "cop number" theory. A graph has cop number 1 if and only if it's "dismantlable," and all non-bipartite graphs where the cop can adjust parity allow catching.

More precisely: on a non-bipartite graph, Bob can make a "parity adjustment" move (traverse an odd cycle effectively) to match Alice's parity, then pursue her. With cop number 1 graphs (which includes many graphs), Bob catches Alice.

The complete bipartite graph $K_{n,n}$ has $n^2$ edges and Alice can evade. Adding any edge creates an odd cycle, allowing Bob to synchronize and eventually catch Alice.

## Answer

The maximum number of edges is $n^2$, achieved by $K_{n,n}$.

$$\boxed{n^2}$$

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 330
- Output tokens: 1113
- Hit token cap: False
- Generation time: 20.50s
- Request ID: msg_01R3wqXSM19rHFj3yKwgbwnB
