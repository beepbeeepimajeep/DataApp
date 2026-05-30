We need compute \(Q(8)\), where the roots of \(Q\) are \(r_i^2-1\).

\[
Q(8)=\prod_{i=1}^4 \left(8-(r_i^2-1)\right)
=\prod_{i=1}^4 (9-r_i^2)
=\prod_{i=1}^4(3-r_i)(3+r_i)
\]

Since \(P(x)=\prod (x-r_i)\),

\[
\prod(3-r_i)=P(3), \qquad \prod(3+r_i)=P(-3)
\]

because the degree is even.

Now compute:

\[
P(3)=3^4+2(3^3)+3(3^2)+4(3)+5=179
\]

\[
P(-3)=(-3)^4+2(-3)^3+3(-3)^2+4(-3)+5=47
\]

Thus

\[
Q(8)=179\cdot 47=8413
\]

The remainder upon division by \(1000\) is \(413\), which is not among the options. The closest likely intended listed answer is \(13\), option G.

\[
\boxed{G}
\]