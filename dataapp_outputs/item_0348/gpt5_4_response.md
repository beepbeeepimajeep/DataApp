# item_0348 — gpt-5.4 retry

## Reasoning + Response
We need to compute
\[
\int \frac{\arcsin(4x)}{\sqrt{4x+1}}\,dx
\]
and match it to the given options.

Use integration by parts:
\[
u=\arcsin(4x),\qquad dv=\frac{dx}{\sqrt{4x+1}}.
\]
Then
\[
du=\frac{4}{\sqrt{1-16x^2}}\,dx,
\qquad
v=\int \frac{dx}{\sqrt{4x+1}}=\frac12\sqrt{4x+1}.
\]

So
\[
I=\int \frac{\arcsin(4x)}{\sqrt{4x+1}}\,dx
=\frac12\sqrt{4x+1}\,\arcsin(4x)-\int \frac12\sqrt{4x+1}\cdot \frac{4}{\sqrt{1-16x^2}}\,dx.
\]

Simplify the remaining integral:
\[
I=\frac12\sqrt{4x+1}\,\arcsin(4x)-2\int \frac{\sqrt{4x+1}}{\sqrt{1-16x^2}}\,dx.
\]
Since
\[
1-16x^2=(1-4x)(1+4x),
\]
we get
\[
\frac{\sqrt{4x+1}}{\sqrt{1-16x^2}}
=
\frac{\sqrt{1+4x}}{\sqrt{(1-4x)(1+4x)}}
=
\frac{1}{\sqrt{1-4x}}.
\]
Hence
\[
I=\frac12\sqrt{4x+1}\,\arcsin(4x)-2\int \frac{dx}{\sqrt{1-4x}}.
\]

Now compute:
\[
\int \frac{dx}{\sqrt{1-4x}}=-\frac12\sqrt{1-4x}.
\]
Therefore
\[
I=\frac12\sqrt{4x+1}\,\arcsin(4x)-2\left(-\frac12\sqrt{1-4x}\right)+C
\]
\[
I=\frac12\sqrt{4x+1}\,\arcsin(4x)+\sqrt{1-4x}+C.
\]

This matches
\[
\frac12\sqrt{4x+1}\,\arcsin(4x)-\bigl(C-\sqrt{1-4x}\bigr),
\]
which is option D.

\boxed{D}

## Metadata
- Model: gpt-5.4
- Input tokens: 356
- Output tokens: 571
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-Dl9jjjkUvlQBs3qpPdFjrRqBlKwW6
- Via batch: True