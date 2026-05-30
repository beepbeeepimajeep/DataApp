# item_0433 — gpt-5.4 retry

## Reasoning + Response
We are asked to identify the correct formula for \(\cos 3\theta\).

Use the triple-angle identity:
\[
\cos 3\theta=\cos(2\theta+\theta)=\cos 2\theta \cos\theta-\sin 2\theta \sin\theta
\]
Now substitute
\[
\cos 2\theta=\cos^2\theta-\sin^2\theta,\qquad \sin 2\theta=2\sin\theta\cos\theta
\]
So
\[
\cos 3\theta=(\cos^2\theta-\sin^2\theta)\cos\theta-(2\sin\theta\cos\theta)\sin\theta
\]
\[
=\cos^3\theta-\cos\theta\sin^2\theta-2\cos\theta\sin^2\theta
\]
\[
=\cos^3\theta-3\cos\theta\sin^2\theta
\]
Using \(\sin^2\theta=1-\cos^2\theta\),
\[
\cos 3\theta=\cos^3\theta-3\cos\theta(1-\cos^2\theta)
=4\cos^3\theta-3\cos\theta
\]

This matches option C.

\boxed{C}

## Metadata
- Model: gpt-5.4
- Input tokens: 1188
- Output tokens: 286
- Hit token cap: False
- Finish reason: stop
- Generation time: 0.00s
- Request ID: chatcmpl-Dl9l1BXPulDdyHnlCuzHa3RjJsOjW
- Via batch: True