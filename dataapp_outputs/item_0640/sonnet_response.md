# sonnet Response

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
Using the binomial theorem, the term with $x^3 y^{13}$ in $({\frac{1}{2}}x + y)^{17}$ requires $k=3$:

$$\binom{17}{3}\left(\frac{1}{2}\right)^3 y^{14}$$

Wait, let me be careful. The general term is:

$$\binom{17}{k}\left(\frac{x}{2}\right)^k y^{17-k}$$

For $x^3 y^{13}$: $k=3$ and $17-k=14$... but we need $y^{13}$, so $17-k=13 \Rightarrow k=4$.

Check: $k=4$ gives $x^4$, not $x^3$. That doesn't match either.

We need $k=3$ and $17-k=13$, but $17-3=14\neq 13$. The exponents must sum to 17, so $x^3 y^{13}$ has exponents summing to 16, not 17. 

Actually wait — the term is $x^3 y^{13}$, exponents sum to 16 ≠ 17, so this term doesn't appear in $(x/2 + y)^{17}$.

Hmm, but let me re-read: the coefficient of $x^3 y^{13}$ in $\left(\frac{1}{2}x + y\right)^{17}$.

Since 3+13=16≠17, the coefficient is 0.

\boxed{G}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 262
- Output tokens: 400
- Hit token cap: False
- Generation time: 6.50s
- Request ID: msg_0184JXcjnAVokpizcbACPShi
