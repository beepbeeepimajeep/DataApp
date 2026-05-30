# sonnet Response

## Prompt
```
Find a formula for the exponential function which satisfies the given conditions: g(10)=70 \quad\mbox{and}\quad g(30)=20. $g(x)=$ [ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We need an exponential function g(x) = a·bˣ satisfying g(10) = 70 and g(30) = 20.

From the two conditions:
- a·b¹⁰ = 70
- a·b³⁰ = 20

Dividing the second by the first:
b²⁰ = 20/70 = 2/7

So b = (2/7)^(1/20)

From a·b¹⁰ = 70:
a = 70/b¹⁰ = 70/(2/7)^(1/2) = 70·(7/2)^(1/2) = 70·√(7/2)

Simplify: 70·√(7/2) = 70·√7/√2 = 70√7/√2 = 35√14

So:
g(x) = 35√14 · (2/7)^(x/20)

\boxed{g(x)=35\sqrt{14}\left(\dfrac{2}{7}\right)^{x/20}}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 229
- Output tokens: 279
- Hit token cap: False
- Generation time: 4.46s
- Request ID: msg_015DupfFyKkNy7JKiuZ8St8q
