# gpt5_4 Response

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
We are asked for the genus of the double cover
\[
\pi:\Sigma\to C,\qquad \Sigma=\{x^2=s\}\subset \operatorname{Tot}(\omega_C),
\]
where \(s\in H^0(C,\omega_C^{\otimes 2})\) has simple zeros.

Since \(x^2=s\), this is a degree \(2\) cover of \(C\), branched exactly over the zeros of \(s\).

A section of \(\omega_C^{\otimes 2}\) has divisor of degree
\[
\deg(\omega_C^{\otimes 2})=2\deg(\omega_C)=2(2g-2)=4g-4.
\]
Because the zeros are simple, there are exactly \(4g-4\) branch points.

Now apply Riemann–Hurwitz to the double cover \(\pi\):
\[
2g(\Sigma)-2 = 2(2g(C)-2) + (4g-4).
\]
So
\[
2g(\Sigma)-2 = 4g-4+4g-4=8g-8,
\]
hence
\[
2g(\Sigma)=8g-6,\qquad g(\Sigma)=4g-3.
\]

Thus the correct option is H.

\boxed{H}

## Metadata
- Model: gpt-5.4
- Input tokens: 461
- Output tokens: 295
- Hit token cap: False
- Generation time: 3.70s
- Request ID: chatcmpl-DhH8Jo71mKER4mcSdrAs9m9OqonwW
