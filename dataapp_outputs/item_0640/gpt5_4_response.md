# gpt5_4 Response

## Prompt
```
What is the coefficient of $x^3y^{13}$ in $\left(\frac 12x + y\right)^{17}$ ?

Options:
A. 34
B. 136
C. 17
D. 170
E. 68
F. 340
G. 0
H. 85

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
We need the coefficient of \(x^3y^{13}\) in
\[
\left(\frac12 x+y\right)^{17}.
\]

Using the binomial theorem,
\[
\left(\frac12 x+y\right)^{17}=\sum_{k=0}^{17}\binom{17}{k}\left(\frac12 x\right)^k y^{17-k}.
\]

To get \(x^3y^{13}\), we would need:
- \(k=3\) for \(x^3\),
- and then the \(y\)-power would be \(17-3=14\), not \(13\).

So no term in the expansion is \(x^3y^{13}\). The coefficient is \(0\).

That corresponds to option G.

\boxed{G}

## Metadata
- Model: gpt-5.4
- Input tokens: 236
- Output tokens: 176
- Hit token cap: False
- Generation time: 2.60s
- Request ID: chatcmpl-DhNtVhPW7hQhLzmAqc3ibrK1GBxHV
