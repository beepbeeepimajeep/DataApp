# GPT-5.5 (xhigh) Response

## Metadata
- Item ID: 38
- Type: mcq
- Input tokens: 369
- Completion tokens: 1281
- Reasoning tokens: 948
- Generation time: 19.60s
- Request ID: chatcmpl-Dh3A9FXjAFC1Linq0KTkFV5IRQRc8

## Response
We need evaluate the contour integral and choose the matching option.

The contour is
\[
x^2+y^2=2(x+y)\implies (x-1)^2+(y-1)^2=2,
\]
a circle centered at \(1+i\) with radius \(\sqrt2\).

The poles are \(z=1\) double, and \(z=\pm i\) simple. Inside the circle are \(z=1\) and \(z=i\); \(z=-i\) is outside.

Residues:

At \(z=1\):
\[
\operatorname{Res}_{z=1}\frac1{(z-1)^2(z^2+1)}
=\left.\frac{d}{dz}\left(\frac1{z^2+1}\right)\right|_{z=1}
=-\frac12.
\]

At \(z=i\):
\[
\operatorname{Res}_{z=i}\frac1{(z-1)^2(z^2+1)}
=\frac1{(i-1)^2(2i)}
=\frac14.
\]

So the sum of residues is
\[
-\frac12+\frac14=-\frac14.
\]

Thus
\[
\int_C \frac{dz}{(z-1)^2(z^2+1)}
=2\pi i\left(-\frac14\right)
=-\frac{\pi i}{2}.
\]

This corresponds to option B.

\boxed{B}