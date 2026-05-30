# sonnet Response

## Prompt
```
Find a cosine series which represents f(x) in 0 \leq x \leq \pi if f(x) is defined as f(x) = 00 \leq x < (\pi / 2) f(x) = 1(\pi / 2) < x \leq \pi.

Options:
A. f(x)= (1 / 2) - (2 / \pi) \sum_n=1^∞ (- 1)^n [{cos(2n)} / (2n + 1)]
B. f(x)= (1 / 2) - (2 / \pi) \infty \sum_n=0 (- 1)^n [{tan(2n + 1)} / (2n + 1)]
C. f(x)= (1 / 2) - (4 / \pi) \sum_n=0^∞ (- 1)^n [{sin(2n)} / (2n + 1)]
D. f(x)= (1 / 2) - (2 / \pi) \sum_n=0^∞ [{cos(2n + 1)} / (2n)]
E. f(x)= (1 / 2) - (2 / \pi) \infty \sum_n=0 (- 1)^n [{cos(2n + 1)} / (2n + 1)]
F. f(x)= (1 / 2) + (2 / \pi) \sum_n=1^∞ (- 1)^n [{cos(2n)} / (2n)]
G. f(x)= (1 / 2) - (2 / \pi) \sum_n=0^∞ (- 1)^n [{sin(n)} / (2n + 1)]
H. f(x)= (1 / 2) - (1 / \pi) \sum_n=0^∞ (- 1)^n [{cos(n)} / n]
I. f(x)= (1 / 2) - (2 / \pi) \infty \sum_n=0 (- 1)^n [{cos(2n + 1)} / (2n + 2)]
J. f(x)= (1 / 2) - (2 / \pi) \infty \sum_n=0 (- 1)^n [{sin(2n + 1)} / (2n + 1)]

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
We need the cosine series for f(x) = 0 on [0, π/2) and f(x) = 1 on (π/2, π].

**Cosine series:** f(x) = a₀/2 + Σ aₙ cos(nx)

**a₀:**
a₀ = (2/π) ∫₀^π f(x) dx = (2/π) ∫_{π/2}^π 1 dx = (2/π)(π/2) = 1

So a₀/2 = 1/2.

**aₙ (n ≥ 1):**
aₙ = (2/π) ∫_{π/2}^π cos(nx) dx = (2/π) [sin(nx)/n]_{π/2}^π

= (2/π) · (1/n)[sin(nπ) - sin(nπ/2)]

= (2/π) · (1/n)[0 - sin(nπ/2)]

= -(2/π) · sin(nπ/2)/n

Now sin(nπ/2) is nonzero only for odd n. For n = 2m+1 (odd):
sin((2m+1)π/2) = (-1)^m

So for odd n = 2m+1:
aₙ = -(2/π) · (-1)^m / (2m+1)

The series becomes:
f(x) = 1/2 + Σ_{m=0}^∞ [-(2/π)·(-1)^m/(2m+1)] cos((2m+1)x)

= 1/2 - (2/π) Σ_{n=0}^∞ (-1)^n · cos((2n+1)x)/(2n+1)

This matches option **E**.

\boxed{E}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 794
- Output tokens: 483
- Hit token cap: False
- Generation time: 6.69s
- Request ID: msg_01EJnzDqPnXydFf4AeAgK9Us
