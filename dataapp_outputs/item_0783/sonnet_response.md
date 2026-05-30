# sonnet Response

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
We need to evaluate $2\int \sin^5(-2x)\cos^2(2x)\,dx$.

Since $\sin(-2x) = -\sin(2x)$, we have $\sin^5(-2x) = -\sin^5(2x)$.

So the integral becomes:
$$2\int (-\sin^5(2x))\cos^2(2x)\,dx = -2\int \sin^5(2x)\cos^2(2x)\,dx$$

Let $u = \cos(2x)$, so $du = -2\sin(2x)\,dx$, meaning $\sin(2x)\,dx = -\frac{du}{2}$.

Write $\sin^5(2x) = \sin^4(2x)\cdot\sin(2x) = (1-\cos^2(2x))^2\sin(2x) = (1-u^2)^2\sin(2x)$.

The integral becomes:
$$-2\int (1-u^2)^2 u^2 \cdot \left(-\frac{du}{2}\right) = -2 \cdot \left(-\frac{1}{2}\right)\int (1-u^2)^2 u^2\,du = \int (1-u^2)^2 u^2\,du$$

Expand $(1-u^2)^2 = 1 - 2u^2 + u^4$:
$$\int (u^2 - 2u^4 + u^6)\,du = \frac{u^3}{3} - \frac{2u^5}{5} + \frac{u^7}{7} + C$$

Substituting back $u = \cos(2x)$:
$$\frac{\cos^3(2x)}{3} - \frac{2\cos^5(2x)}{5} + \frac{\cos^7(2x)}{7} + C$$

This equals:
$$C + \frac{1}{3}\cos^3(2x) + \frac{1}{7}\cos^7(2x) - \frac{2}{5}\cos^5(2x)$$

This matches option H.

\boxed{H}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 1045
- Output tokens: 562
- Hit token cap: False
- Generation time: 8.30s
- Request ID: msg_01Jq2y5H7VafPFgkCFJoR7uT
