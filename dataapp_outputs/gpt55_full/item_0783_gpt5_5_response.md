# GPT-5.5 xhigh Response

## Prompt
```

```

## Reasoning + Response
We need the antiderivative and then match it to the options.

Since \(\sin(-2x)=-\sin(2x)\),

\[
2\int \sin(-2x)^5\cos(2x)^2\,dx
=
-2\int \sin^5(2x)\cos^2(2x)\,dx.
\]

Write \(\sin^5(2x)=\sin^4(2x)\sin(2x)\):

\[
-2\int (1-\cos^2(2x))^2\cos^2(2x)\sin(2x)\,dx.
\]

Let

\[
u=\cos(2x), \qquad du=-2\sin(2x)\,dx.
\]

Then the integral becomes

\[
\int (1-u^2)^2u^2\,du
=
\int (u^2-2u^4+u^6)\,du.
\]

So

\[
\frac{u^3}{3}-\frac{2u^5}{5}+\frac{u^7}{7}+C.
\]

Substitute back \(u=\cos(2x)\):

\[
C+\frac{1}{3}\cos^3(2x)+\frac{1}{7}\cos^7(2x)-\frac{2}{5}\cos^5(2x).
\]

This matches option H.

\boxed{H}

## Metadata
- Model: gpt-5.5
- Input tokens: 907
- Output tokens: 835
- Reasoning tokens: 512
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-DhxnZUjOubqPJf33nqb7qrTsl1iqd
- Via batch: True
