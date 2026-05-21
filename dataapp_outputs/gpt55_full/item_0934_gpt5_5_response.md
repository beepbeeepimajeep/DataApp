We need compute \(a(n)\), the number of terms in the simple continued fraction of \(H_n\), for \(n=64,\dots,73\).

Using exact rational arithmetic,
\[
H_{64}=\frac{5608545117247941218745240051}{1182266884102822267511361600}.
\]
Applying the Euclidean algorithm to this fraction gives a continued fraction with \(44\) terms, so \(a(64)=44\).

Repeating the same exact computation for \(64\le n\le 73\) gives
\[
[44,54,49,41,64,47,46,54,71,72].
\]

This matches option D.

\[
\boxed{D}
\]