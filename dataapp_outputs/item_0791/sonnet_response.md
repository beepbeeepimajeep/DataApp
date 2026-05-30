# sonnet Response

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
We want to find $S = \sum_{k=1}^n \cos(ka)$.

**Standard derivation:**

Multiply both sides by $2\sin\frac{a}{2}$:

$$2\sin\tfrac{a}{2}\cdot\cos(ka) = \sin\!\left(ka + \tfrac{a}{2}\right) - \sin\!\left(ka - \tfrac{a}{2}\right)$$

This is a telescoping sum:

$$2\sin\tfrac{a}{2}\cdot S = \sum_{k=1}^n\left[\sin\!\left(\tfrac{(2k+1)a}{2}\right) - \sin\!\left(\tfrac{(2k-1)a}{2}\right)\right]$$

$$= \sin\!\left(\tfrac{(2n+1)a}{2}\right) - \sin\!\left(\tfrac{a}{2}\right)$$

So:
$$S = \frac{\sin\!\left(\frac{(2n+1)a}{2}\right) - \sin\!\left(\frac{a}{2}\right)}{2\sin\!\left(\frac{a}{2}\right)}$$

Using sum-to-product: $\sin A - \sin B = 2\cos\!\left(\frac{A+B}{2}\right)\sin\!\left(\frac{A-B}{2}\right)$

With $A = \frac{(2n+1)a}{2}$ and $B = \frac{a}{2}$:

$$\frac{A+B}{2} = \frac{\frac{(2n+1)a}{2}+\frac{a}{2}}{2} = \frac{(n+1)a}{2}$$

$$\frac{A-B}{2} = \frac{\frac{(2n+1)a}{2}-\frac{a}{2}}{2} = \frac{na}{2}$$

So:
$$\sin\!\left(\tfrac{(2n+1)a}{2}\right) - \sin\!\left(\tfrac{a}{2}\right) = 2\cos\!\left(\tfrac{(n+1)a}{2}\right)\sin\!\left(\tfrac{na}{2}\right)$$

Therefore:
$$S = \frac{2\cos\!\left(\frac{(n+1)a}{2}\right)\sin\!\left(\frac{na}{2}\right)}{2\sin\!\left(\frac{a}{2}\right)} = \frac{\sin\!\left(\frac{na}{2}\right)\cos\!\left(\frac{(n+1)a}{2}\right)}{\sin\!\left(\frac{a}{2}\right)}$$

This matches option **F**.

\boxed{F}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 640
- Output tokens: 704
- Hit token cap: False
- Generation time: 6.79s
- Request ID: msg_01987kh84Ay5FQTiLrRpa7CW
