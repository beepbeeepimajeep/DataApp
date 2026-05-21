We need count ordered pairs where both \(a\) and \(b\) are not divisors of \(720\), but \(ab\mid 720^2\).

Factor:
\[
720=2^4\cdot 3^2\cdot 5,\qquad 720^2=2^8\cdot 3^4\cdot 5^2.
\]

First count all ordered pairs \((a,b)\) with \(ab\mid 720^2\). For each prime exponent \(m\), the number of pairs \((x,y)\) with \(x+y\le m\) is \(\binom{m+2}{2}\). Thus:
\[
\binom{10}{2}\binom{6}{2}\binom{4}{2}=45\cdot 15\cdot 6=4050.
\]

Now subtract pairs where \(a\mid 720\). For prime exponent \(n\) in \(720\), count:
\[
\sum_{x=0}^n (2n-x+1).
\]
For \(n=4,2,1\), these counts are:
\[
35,\ 12,\ 5.
\]
So pairs with \(a\mid 720\):
\[
35\cdot 12\cdot 5=2100.
\]
Similarly, pairs with \(b\mid 720\) also equal \(2100\).

Pairs where both \(a\mid 720\) and \(b\mid 720\):
\[
d(720)^2=(5\cdot 3\cdot 2)^2=900.
\]

By inclusion-exclusion, desired count is:
\[
4050-2100-2100+900=750.
\]

Option \(J\).

\boxed{J}