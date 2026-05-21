# GPT-5.5 xhigh Response

## Prompt
```

```

## Reasoning + Response
We need to prove the Poisson moment recursion and use it to find \(E(X^3)\).

Let \(X \sim \text{Poisson}(\lambda)\). Then

\[
P(X=x)=e^{-\lambda}\frac{\lambda^x}{x!}, \qquad x=0,1,2,\dots
\]

For \(n\ge 1\),

\[
E(X^n)=\sum_{x=0}^{\infty} x^n e^{-\lambda}\frac{\lambda^x}{x!}
\]

The \(x=0\) term is \(0\), so

\[
E(X^n)=\sum_{x=1}^{\infty} x^n e^{-\lambda}\frac{\lambda^x}{x!}
\]

Since \(x! = x(x-1)!\),

\[
E(X^n)=\sum_{x=1}^{\infty} x^{n-1} e^{-\lambda}\frac{\lambda^x}{(x-1)!}
\]

\[
=\lambda \sum_{x=1}^{\infty} x^{n-1} e^{-\lambda}\frac{\lambda^{x-1}}{(x-1)!}
\]

Let \(y=x-1\). Then \(x=y+1\), so

\[
E(X^n)=\lambda \sum_{y=0}^{\infty} (y+1)^{n-1} e^{-\lambda}\frac{\lambda^y}{y!}
\]

Thus,

\[
E(X^n)=\lambda E\left[(X+1)^{n-1}\right]
\]

Now compute \(E(X^3)\):

\[
E(X^3)=\lambda E[(X+1)^2]
\]

\[
=\lambda E[X^2+2X+1]
\]

We need \(E(X^2)\):

\[
E(X^2)=\lambda E[X+1]=\lambda(\lambda+1)=\lambda^2+\lambda
\]

Therefore,

\[
E(X^3)=\lambda\left((\lambda^2+\lambda)+2\lambda+1\right)
\]

\[
=\lambda(\lambda^2+3\lambda+1)
\]

\[
=\lambda^3+3\lambda^2+\lambda
\]

This corresponds to option H.

\boxed{H}

## Metadata
- Model: gpt-5.5
- Input tokens: 413
- Output tokens: 1009
- Reasoning tokens: 480
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-DhxruWnlluml4C9UaQRWo4rQ6sQmk
- Via batch: True
