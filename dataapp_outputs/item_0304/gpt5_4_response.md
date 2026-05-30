# item_0304 — gpt-5.4 retry

## Reasoning + Response
We need to evaluate
\[
\oint_{|z|=3}\frac{z^{13}}{(z^2+5)^3(z^4+1)^2}\,dz
\]
and identify the correct multiple-choice option.

Use the residue theorem:
\[
\oint_{|z|=3} f(z)\,dz = 2\pi i \sum \operatorname{Res}(f;\text{poles inside }|z|=3).
\]

But there is a quicker way: check the residue at infinity.

Let
\[
f(z)=\frac{z^{13}}{(z^2+5)^3(z^4+1)^2}.
\]
As \(z\to\infty\),
\[
(z^2+5)^3\sim z^6,\qquad (z^4+1)^2\sim z^8,
\]
so
\[
f(z)\sim \frac{z^{13}}{z^{14}}=\frac1z.
\]
Thus the coefficient of \(1/z\) in the Laurent expansion at infinity is \(1\).

Now use
\[
\sum \text{residues at finite poles} = -\operatorname{Res}(f,\infty).
\]
Since the coefficient of \(1/z\) is \(1\),
\[
\operatorname{Res}(f,\infty)=-1,
\]
so the sum of residues at all finite poles is
\[
1.
\]

Therefore,
\[
\oint_{|z|=3} f(z)\,dz = 2\pi i(1)=2\pi i.
\]

So the correct option is G.

\boxed{G}

## Metadata
- Model: gpt-5.4
- Input tokens: 269
- Output tokens: 369
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-Dl9j5Kn7OargBSUblw0oxF6vtwbbo
- Via batch: True