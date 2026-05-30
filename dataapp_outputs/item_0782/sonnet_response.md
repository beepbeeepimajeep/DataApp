# sonnet Response

## Prompt
```
Find the following partial sum,
$ \sum_{n=0}^{40} (3-2 n)=$ [ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We need the sum $\sum_{n=0}^{40}(3-2n)$.

This has 41 terms. The first term (n=0) is 3, the last term (n=40) is $3-80=-77$.

Sum = $\frac{41}{2}(3 + (-77)) = \frac{41}{2}(-74) = 41 \times (-37) = -1517$

\boxed{-1517}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 212
- Output tokens: 116
- Hit token cap: False
- Generation time: 2.28s
- Request ID: msg_01YHb9RaAXNS8xX5w7vAtLj8
