# item_0303 — gpt-5.4 retry

## Reasoning + Response
We need to evaluate
\[
\sum_{n=5}^{29} \lceil \sqrt n\rceil.
\]

Group values of \(n\) by when \(\lceil \sqrt n\rceil\) is constant.

- \(\sqrt n \in (2,3]\) for \(n=5,6,7,8,9\), so \(\lceil \sqrt n\rceil=3\) for 5 numbers.
- \(\sqrt n \in (3,4]\) for \(n=10,11,12,13,14,15,16\), so value \(4\) for 7 numbers.
- \(\sqrt n \in (4,5]\) for \(n=17,18,19,20,21,22,23,24,25\), so value \(5\) for 9 numbers.
- \(\sqrt n \in (5,6)\) for \(n=26,27,28,29\), so \(\lceil \sqrt n\rceil=6\) for 4 numbers.

Now add:
\[
5\cdot 3+7\cdot 4+9\cdot 5+4\cdot 6
=15+28+45+24=112.
\]

So the correct option is C.

\boxed{C}

## Metadata
- Model: gpt-5.4
- Input tokens: 299
- Output tokens: 293
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-Dl9j0xGBxfeY2knUFtql4cETdXXOB
- Via batch: True