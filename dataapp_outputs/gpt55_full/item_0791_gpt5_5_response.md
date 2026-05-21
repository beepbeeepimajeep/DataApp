We need the closed form of \(S=\sum_{k=1}^n \cos(ka)\).

Use
\[
2\sin\left(\frac a2\right)\cos(ka)
=
\sin\left(\left(k+\frac12\right)a\right)-\sin\left(\left(k-\frac12\right)a\right).
\]

Summing from \(k=1\) to \(n\),
\[
2\sin\left(\frac a2\right)S
=
\sin\left(\frac{(2n+1)a}{2}\right)-\sin\left(\frac a2\right).
\]

Using \(\sin x-\sin y=2\cos\left(\frac{x+y}{2}\right)\sin\left(\frac{x-y}{2}\right)\),
\[
2\sin\left(\frac a2\right)S
=
2\cos\left(\frac{(n+1)a}{2}\right)\sin\left(\frac{na}{2}\right).
\]

Thus
\[
S=\frac{\sin\left(\frac{na}{2}\right)\cos\left(\frac{(n+1)a}{2}\right)}{\sin\left(\frac a2\right)}.
\]

This matches option F.

\boxed{F}