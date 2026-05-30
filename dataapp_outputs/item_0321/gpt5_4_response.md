# item_0321 — gpt-5.4 retry

## Reasoning + Response
We need the positive \(a\) such that the tangent line to \(f(x)=x^2e^{-x}\) at \(x=a\) passes through the origin.

A tangent line at \(x=a\) is
\[
y=f(a)+f'(a)(x-a).
\]
For it to pass through \((0,0)\), substitute \(x=0,\ y=0\):
\[
0=f(a)-af'(a).
\]
So we need
\[
f(a)=af'(a).
\]

Now compute the derivative:
\[
f(x)=x^2e^{-x}
\]
\[
f'(x)=2xe^{-x}-x^2e^{-x}=e^{-x}(2x-x^2).
\]

Substitute into the condition:
\[
a^2e^{-a}=a\cdot e^{-a}(2a-a^2).
\]
Since \(a>0\) and \(e^{-a}\neq 0\), divide by \(ae^{-a}\):
\[
a=2a-a^2.
\]
\[
0=a-a^2=a(1-a).
\]
So
\[
a=0 \quad \text{or} \quad a=1.
\]
Given \(a>0\), we take
\[
a=1.
\]

Option \(H\).

\boxed{H}

## Metadata
- Model: gpt-5.4
- Input tokens: 303
- Output tokens: 298
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-Dl9kJoqKpFm0XB8mC1nl9NJwXuKKN
- Via batch: True