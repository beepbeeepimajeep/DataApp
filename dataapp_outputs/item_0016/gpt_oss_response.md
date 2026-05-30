# gpt_oss Response

## Prompt
```
Rose and Brunno play the game on a board shaped like a regular 1001-gon. Initially, all vertices of the board are white, and there is a chip at one of them. On each turn, Rose chooses an arbitrary positive integer \( k \), then Brunno chooses a direction: clockwise or counterclockwise, and moves the chip in the chosen direction by \( k \) vertices. If at the end of the turn the chip stands at a white vertex, this vertex is painted red.

Find the greatest number of vertices that Rose can make red regardless of Brunno's actions, if the number of turns is not limited.

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
The board is the cyclic group \(\mathbb Z_{1001}\).
If the chip is at a vertex \(v\) and Rose chooses a positive integer \(k\), then
the two possible next vertices are  

\[
v+k\pmod{1001},\qquad v-k\pmod{1001}.
\]

If at least one of these two vertices is still white, Brunno can choose the
other (red) one and avoid painting a new vertex.  
Consequently Rose can force a new vertex to become red **iff** she can pick a
\(k\) for which **both** \(v\pm k\) are white; then whichever direction Brunno
takes, a white vertex is painted red.

Thus Brunno can stop the game when the current vertex \(v\) has the property

\[
\forall k\;(1\le k\le 1000):\qquad \{v+k,\;v-k\}\cap R\neq\varnothing ,
\]

where \(R\) is the set of already red vertices.  
In other words, for the present \(v\) there is **no** pair of opposite white
vertices.

If the set of white vertices \(W\) has size at most \(500\), then \(W\) can be
placed inside an arc of length \(500\) (a “half‑circle”).  Choosing \(v\) as the
vertex opposite that arc, every pair \(\{v\pm k\}\) meets the red set, so Brunno
can prevent any further red vertex.  
Hence Rose can never guarantee more than  

\[
1001-500 = 501
\]

red vertices.

---

**Rose can achieve 501 red vertices.**  

Start with the chip on any vertex.  
In each turn Rose announces \(k=1\).  
Both vertices \(v\pm1\) are white until at most \(500\) vertices have become red,
so Brunno is forced to move to a white vertex, which then turns red.
Thus after each turn exactly one new vertex is painted red, irrespective of
the direction Brunno chooses.

After \(500\) turns at least \(501\) vertices are red.  At this moment the
white set has size \(\le 500\); from now on Brunno could stop further progress,
but Rose has already secured 501 red vertices.

Since 501 can be forced and more than 501 cannot be guaranteed, the greatest
number of vertices that Rose can always make red is

\[
\boxed{501}
\]

## Metadata
- Model: api-gpt-oss-120b
- Input tokens: 352
- Output tokens: 5866
- Hit token cap: False
- Generation time: 38.79s
- Request ID: chatcmpl-ab18b731fea45d45
