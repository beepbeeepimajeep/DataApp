# gpt5_4 Response

## Prompt
```
Calculate the sum $S=\cos(a)+\cos(2 \cdot a)+\cos(3 \cdot a) + \ldots + \cos(n \cdot a)$, where $a \ne 2 \cdot \pi \cdot k$ for integers $k$.

Options:
A. S=\frac{\sin\left(\frac{(n+1)\cdot a}{2}\right)\cdot\cos\left(\frac{(n-1)\cdot a}{2}\right)}{\sin\left(\frac{a}{2}\right)}
B. S=\frac{\sin\left(\frac{(n+1)\cdot a}{2}\right)\cdot\cos\left(\frac{(n+2)\cdot a}{2}\right)}{\sin\left(\frac{a}{2}\right)}
C. S=\frac{\sin\left(\frac{n\cdot a}{2}\right)\cdot\cos\left(\frac{n\cdot a}{2}\right)}{\sin\left(\frac{a}{2}\right)}
D. S=\frac{\sin\left(\frac{(n-1)\cdot a}{2}\right)\cdot\cos\left(\frac{(n+1)\cdot a}{2}\right)}{\sin\left(\frac{a}{2}\right)}
E. S=\frac{\sin\left(\frac{(n+1)\cdot a}{2}\right)\cdot\cos\left(\frac{n\cdot a}{2}\right)}{\sin\left(\frac{a}{2}\right)}
F. S=\frac{\sin\left(\frac{n\cdot a}{2}\right)\cdot\cos\left(\frac{(n+1)\cdot a}{2}\right)}{\sin\left(\frac{a}{2}\right)}

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
We need the sum
\[
S=\cos a+\cos 2a+\cdots+\cos na=\sum_{k=1}^n \cos(ka).
\]

Use the standard trigonometric sum formula:
\[
\sum_{k=1}^n \cos(kx)=\frac{\sin\left(\frac{nx}{2}\right)\cos\left(\frac{(n+1)x}{2}\right)}{\sin\left(\frac{x}{2}\right)},
\qquad x\neq 2\pi m.
\]

Setting \(x=a\), we get
\[
S=\frac{\sin\left(\frac{na}{2}\right)\cos\left(\frac{(n+1)a}{2}\right)}{\sin\left(\frac{a}{2}\right)}.
\]

This matches option F.

\boxed{F}

## Metadata
- Model: gpt-5.4
- Input tokens: 578
- Output tokens: 192
- Hit token cap: False
- Generation time: 2.69s
- Request ID: chatcmpl-DhOKxhlulKy4c6MJ88XfvIFIJMuew
