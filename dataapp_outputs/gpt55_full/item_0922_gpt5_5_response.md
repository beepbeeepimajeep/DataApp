# GPT-5.5 xhigh Response

## Prompt
```
What is the value of the integral $\oint_{c} \frac{2 z^{2}-z+1} {z-1} \mathrm{d} z$,Where $C \colon\mid z \mid=2$?

Options:
A. $$
-4 \pi\mathrm{i}
$$
B. $$
4 \pi\mathrm{i}
$$
C. $$
\pi\mathrm{i}
$$
D. $$
-8 \pi\mathrm{i}
$$
E. $$
-2 \pi\mathrm{i}
$$
F. $$
2 \pi\mathrm{i}
$$
G. $$
12 \pi\mathrm{i}
$$
H. $$
6 \pi\mathrm{i}
$$
I. $$
0
$$
J. $$
8 \pi\mathrm{i}
$$

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
We need the contour integral around \(C: |z|=2\).

The integrand
\[
\frac{2z^2-z+1}{z-1}
\]
has a simple pole at \(z=1\), which lies inside \(|z|=2\).

The residue at \(z=1\) is
\[
\operatorname{Res}_{z=1}\frac{2z^2-z+1}{z-1}
= 2(1)^2-1+1=2.
\]

By the residue theorem,
\[
\oint_C \frac{2z^2-z+1}{z-1}\,dz
=2\pi i \cdot 2
=4\pi i.
\]

So the correct option is B.

\boxed{B}

## Metadata
- Model: gpt-5.5
- Input tokens: 343
- Output tokens: 341
- Reasoning tokens: 159
- Hit token cap: False
- Finish reason: stop
- Generation time: 5.50s
- Request ID: chatcmpl-DhGJ0e7PfjJbOS9eHGOoSGGAwbqHx
