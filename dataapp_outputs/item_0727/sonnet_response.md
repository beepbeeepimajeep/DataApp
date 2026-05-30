# sonnet Response

## Prompt
```
Determine the greatest possible value of $\sum_{i=1}^{10} \cos(3x_i)$ for real numbers $x_1,x_2,\dots,x_{10}$ satisfying $\sum_{i=1}^{10} \cos(x_i) = 0$.

Options:
A. \frac{480}{49}
B. \frac{480}{56}
C. \frac{480}{51}
D. \frac{480}{48}
E. \frac{480}{47}
F. \frac{480}{52}
G. \frac{480}{55}
H. \frac{480}{53}
I. \frac{480}{50}
J. \frac{480}{54}

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
## Setting Up the Problem

We want to maximize $\sum_{i=1}^{10} \cos(3x_i)$ subject to $\sum_{i=1}^{10} \cos(x_i) = 0$.

## Using the Triple Angle Formula

Recall: $\cos(3x) = 4\cos^3(x) - 3\cos(x)$

So $\sum_{i=1}^{10} \cos(3x_i) = 4\sum_{i=1}^{10} \cos^3(x_i) - 3\sum_{i=1}^{10} \cos(x_i) = 4\sum_{i=1}^{10} \cos^3(x_i)$

since the constraint gives $\sum \cos(x_i) = 0$.

## Maximizing $\sum \cos^3(x_i)$ Subject to $\sum \cos(x_i) = 0$

Let $c_i = \cos(x_i) \in [-1, 1]$. We need to maximize $\sum c_i^3$ subject to $\sum c_i = 0$.

To maximize $\sum c_i^3$, we want some $c_i$ to be as large as possible (close to 1) and the rest to compensate with negative values.

**Optimal strategy:** Let $k$ variables have $c_i = 1$ and the remaining $10-k$ variables have $c_i = -\frac{k}{10-k}$ (to satisfy the constraint), provided $\frac{k}{10-k} \leq 1$, i.e., $k \leq 5$.

For $k$ variables at 1 and $(10-k)$ variables at $-\frac{k}{10-k}$:

$$\sum c_i^3 = k \cdot 1 + (10-k)\cdot\left(-\frac{k}{10-k}\right)^3 = k - (10-k)\cdot\frac{k^3}{(10-k)^3}$$

$$= k - \frac{k^3}{(10-k)^2}= k\left(1 - \frac{k^2}{(10-k)^2}\right) = k \cdot \frac{(10-k)^2 - k^2}{(10-k)^2}$$

$$= k \cdot \frac{(10-2k) \cdot 10}{(10-k)^2} = \frac{10k(10-2k)}{(10-k)^2}$$

Now evaluate for $k = 1, 2, 3, 4, 5$:

- $k=1$: $\frac{10 \cdot 1 \cdot 8}{81} = \frac{80}{81}$
- $k=2$: $\frac{10 \cdot 2 \cdot 6}{64} = \frac{120}{64} = \frac{15}{8}$
- $k=3$: $\frac{10 \cdot 3 \cdot 4}{49} = \frac{120}{49}$
- $k=4$: $\frac{10 \cdot 4 \cdot 2}{36} = \frac{80}{36} = \frac{20}{9}$
- $k=5$: $\frac{10 \cdot 5 \cdot 0}{25} = 0$

Comparing: $\frac{80}{81} \approx 0.988$, $\frac{15}{8} = 1.875$, $\frac{120}{49} \approx 2.449$, $\frac{20}{9} \approx 2.222$

Maximum is at $k=3$: $\sum c_i^3 = \frac{120}{49}$

## Computing the Answer

$$\sum_{i=1}^{10} \cos(3x_i) = 4 \cdot \frac{120}{49} = \frac{480}{49}$$

This matches option **A**.

\boxed{A}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 369
- Output tokens: 1049
- Hit token cap: False
- Generation time: 14.72s
- Request ID: msg_013TjJg5GWf9mu4JZ39CLERa
