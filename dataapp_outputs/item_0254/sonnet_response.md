# sonnet Response

## Prompt
```
Let $C$ be a smooth projective curve over $\mathbb{C}$ and $\omega_{C}^{\otimes2}$ the square of its canonical sheaf.\
Suppose $g ( C ) \, \geq\, 2$ and $s \, \in\, \Gamma( C, \omega_{C}^{\otimes2} )$ is a section with simple zeros. What is the genus of $\Sigma=\{x^{2}=s \}$ in the total space of the line bundle $\omega_{C}$? i.e. the curve defined by the 2-valued 1-form $\sqrt{s}$ .

Options:
A. $$
g ( \Sigma)=4 g+0.
$$
B. $$
g ( \Sigma)=3 g+2.
$$
C. $$
g ( \Sigma)=5 g-4.
$$
D. $$
g ( \Sigma)=3 g-5.
$$
E. $$
g ( \Sigma)=4 g+1.
$$
F. $$
g ( \Sigma)=4 g-5.
$$
G. $$
g ( \Sigma)=5 g-2.
$$
H. $$
g ( \Sigma)=4 g-3.
$$
I. $$
g ( \Sigma)=2 g-3.
$$
J. $$
g ( \Sigma)=6 g-1.
$$

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
## Setting up the problem

We need to find the genus of the curve $\Sigma = \{x^2 = s\}$ in the total space of $\omega_C$, where $s \in \Gamma(C, \omega_C^{\otimes 2})$ has simple zeros.

## Using Riemann-Hurwitz

The curve $\Sigma$ is a double cover of $C$ via the projection map $\pi: \Sigma \to C$. The cover is defined by $x^2 = s$, so it's a degree 2 map branched at the zeros of $s$.

**Number of branch points:** We need $\deg(\omega_C^{\otimes 2}) = 2(2g-2) = 4g-4$. Since $s$ has simple zeros, there are $4g-4$ branch points (simple zeros of $s$).

**Riemann-Hurwitz formula:**
$$2g(\Sigma) - 2 = 2(2g(C) - 2) + \text{(ramification)}$$

For a degree 2 cover with $b = 4g-4$ simple branch points, each branch point contributes ramification index 1 (since the ramification at a simple branch point in a double cover is 1):

$$2g(\Sigma) - 2 = 2(2g - 2) + (4g - 4)$$

$$2g(\Sigma) - 2 = 4g - 4 + 4g - 4 = 8g - 8$$

$$2g(\Sigma) = 8g - 6$$

$$g(\Sigma) = 4g - 3$$

## Answer

This matches option **H**.

\boxed{H}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 553
- Output tokens: 426
- Hit token cap: False
- Generation time: 6.87s
- Request ID: msg_01X27mr2m5ZWzChV4rchhevP
