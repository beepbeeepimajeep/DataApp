# gpt5_4 Response

## Prompt
```
Solve the integral:
$$
2 \cdot \int \sin(-2 \cdot x)^5 \cdot \cos(2 \cdot x)^2 \, dx
$$

Options:
A. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{1}{4} \cdot (\cos(2 \cdot x))^5
B. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{1}{5} \cdot (\cos(2 \cdot x))^5
C. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{3}{5} \cdot (\cos(2 \cdot x))^5
D. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{1}{6} \cdot (\cos(2 \cdot x))^5
E. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{1}{2} \cdot (\cos(2 \cdot x))^5
F. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{1}{8} \cdot (\cos(2 \cdot x))^5
G. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{4}{5} \cdot (\cos(2 \cdot x))^5
H. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{2}{5} \cdot (\cos(2 \cdot x))^5
I. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{1}{3} \cdot (\cos(2 \cdot x))^5
J. C + \frac{1}{3} \cdot (\cos(2 \cdot x))^3 + \frac{1}{7} \cdot (\cos(2 \cdot x))^7 - \frac{1}{10} \cdot (\cos(2 \cdot x))^5

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
We need to evaluate
\[
2\int \sin(-2x)^5\cos(2x)^2\,dx.
\]

Since \(\sin(-2x)=-\sin(2x)\), we have
\[
\sin(-2x)^5=-\sin^5(2x),
\]
so the integral becomes
\[
-2\int \sin^5(2x)\cos^2(2x)\,dx.
\]

Write
\[
\sin^5(2x)=\sin(2x)\bigl(1-\cos^2(2x)\bigr)^2.
\]
Then
\[
-2\int \sin(2x)\cos^2(2x)\bigl(1-\cos^2(2x)\bigr)^2\,dx.
\]

Let
\[
u=\cos(2x), \qquad du=-2\sin(2x)\,dx.
\]
So the integral becomes
\[
\int u^2(1-u^2)^2\,du.
\]

Expand:
\[
u^2(1-2u^2+u^4)=u^2-2u^4+u^6.
\]

Integrate term by term:
\[
\int (u^2-2u^4+u^6)\,du
=\frac{u^3}{3}-\frac{2u^5}{5}+\frac{u^7}{7}+C.
\]

Substitute back \(u=\cos(2x)\):
\[
C+\frac{1}{3}\cos^3(2x)+\frac{1}{7}\cos^7(2x)-\frac{2}{5}\cos^5(2x).
\]

This matches option H.

\boxed{H}

## Metadata
- Model: gpt-5.4
- Input tokens: 907
- Output tokens: 395
- Hit token cap: False
- Generation time: 4.80s
- Request ID: chatcmpl-DhOGmfuJJ19QeDcCv8ZbBIVUUWkA3
