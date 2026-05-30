# gpt_oss Response

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
The curve \(\Sigma\) is a double cover of \(C\) branched over the zero divisor of \(s\).  
Since \(s\in H^{0}(C,\omega_{C}^{\otimes 2})\) has simple zeros, the branch divisor \(B\) consists of \(\deg(\omega_{C}^{\otimes 2})=4g-4\) distinct points.

For a degree‑2 map \(\pi:\Sigma\to C\), the Riemann–Hurwitz formula gives  

\[
2g(\Sigma)-2 = 2\bigl(2g-2\bigr) + \#B
               = 2(2g-2) + (4g-4)
               = 8g-8 .
\]

Hence  

\[
2g(\Sigma) = 8g-6 \qquad\Longrightarrow\qquad g(\Sigma)=4g-3 .
\]

Thus the genus of \(\Sigma\) is \(4g-3\).

\[
\boxed{H}
\]

## Metadata
- Model: api-gpt-oss-120b
- Input tokens: 522
- Output tokens: 660
- Hit token cap: False
- Generation time: 4.69s
- Request ID: chatcmpl-b1271ebfc41fc1e7
