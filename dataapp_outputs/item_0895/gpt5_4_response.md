# gpt5_4 Response

## Prompt
```
Find a formula for the exponential function which satisfies the given conditions: g(10)=70 \quad\mbox{and}\quad g(30)=20. $g(x)=$ [ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We need an exponential function \(g(x)\) such that \(g(10)=70\) and \(g(30)=20\).

Assume
\[
g(x)=ab^x.
\]
Then the conditions give
\[
ab^{10}=70,\qquad ab^{30}=20.
\]
Divide the second equation by the first:
\[
\frac{ab^{30}}{ab^{10}}= \frac{20}{70}
\]
\[
b^{20}=\frac{2}{7}.
\]
So
\[
b=\left(\frac{2}{7}\right)^{1/20}.
\]

Now use \(ab^{10}=70\):
\[
a\left(\left(\frac{2}{7}\right)^{1/20}\right)^{10}=70
\]
\[
a\left(\frac{2}{7}\right)^{1/2}=70
\]
\[
a\sqrt{\frac{2}{7}}=70
\]
\[
a=70\sqrt{\frac{7}{2}}.
\]

A cleaner form is to anchor the function at \(x=10\):
\[
g(x)=70\left(\frac{2}{7}\right)^{\frac{x-10}{20}}.
\]

\[
\boxed{70\left(\frac{2}{7}\right)^{\frac{x-10}{20}}}
\]

## Metadata
- Model: gpt-5.4
- Input tokens: 202
- Output tokens: 309
- Hit token cap: False
- Generation time: 4.70s
- Request ID: chatcmpl-DhOeE955k5OMdNRnPsQ6exWYReBUK
