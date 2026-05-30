# gpt5_4 Response

## Prompt
```
Let $f(x)=\sqrt{56-x}$ and $g(x)=x^2-x$. Then the domain of $f\circ g$ is equal to $[a,b]$ for $a=$ [ANS]
and $b=$ [ANS]

Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \boxed{...} with comma-separated values

End with: \boxed{value1,value2,value3}
```

## Reasoning + Response
We are asked for the domain of the composition \(f\circ g\), where
\[
f(x)=\sqrt{56-x},\qquad g(x)=x^2-x.
\]

For \(f(g(x))\) to be defined, the input to the square root must be nonnegative:
\[
56-g(x)\ge 0.
\]
Substitute \(g(x)=x^2-x\):
\[
56-(x^2-x)\ge 0
\]
\[
56-x^2+x\ge 0
\]
\[
-x^2+x+56\ge 0.
\]
Multiply by \(-1\) and reverse the inequality:
\[
x^2-x-56\le 0.
\]
Factor:
\[
x^2-x-56=(x-8)(x+7).
\]
So we need
\[
(x-8)(x+7)\le 0,
\]
which holds for
\[
-7\le x\le 8.
\]

Thus the domain is \([a,b]=[-7,8]\), so \(a=-7\) and \(b=8\).

We have exactly 2 answers, in the requested order: \(a\), then \(b\).

\boxed{-7,8}

## Metadata
- Model: gpt-5.4
- Input tokens: 263
- Output tokens: 279
- Hit token cap: False
- Generation time: 3.80s
- Request ID: chatcmpl-DhNJnZxPr3v2GoGknMC0zwWhcPOSw
