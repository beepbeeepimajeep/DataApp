# GPT-5.5 xhigh Response

## Prompt
```

```

## Reasoning + Response
We need \(a>0\) such that the tangent line to \(f(x)=x^2e^{-x}\) at \(x=a\) passes through \((0,0)\).

The tangent line at \(x=a\) is
\[
y=f(a)+f'(a)(x-a).
\]
For it to pass through the origin:
\[
0=f(a)-a f'(a).
\]

Compute:
\[
f'(x)=2xe^{-x}-x^2e^{-x}=e^{-x}(2x-x^2).
\]
So
\[
f(a)=a^2e^{-a}, \quad f'(a)=e^{-a}(2a-a^2).
\]
Then
\[
a^2e^{-a}=a e^{-a}(2a-a^2).
\]
Since \(a>0\), divide by \(a^2e^{-a}\):
\[
1=2-a
\]
so
\[
a=1.
\]

This corresponds to option H.

\[
\boxed{H}
\]

## Metadata
- Model: gpt-5.5
- Input tokens: 303
- Output tokens: 618
- Reasoning tokens: 381
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-DhhhgV5dxwYHzxMSvhhsDxbH4Y0E5
- Via batch: True
