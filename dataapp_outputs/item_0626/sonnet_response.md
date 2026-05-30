# sonnet Response

## Prompt
```
Calculate the integral $\int_{-1}^{1} \mid z \mid \mathrm{d} z$, with the integration path as: (1) a straight line segment; (2) the semicircle of the unit circle on the upper half; (3) the semicircle of the unit circle on the lower half.

Options:
A. $$0$$
$$1$$
$$2$$
B. $$2$$
$$1$$
$$2$$
C. $$2$$
$$2$$
$$0$$
D. $$2$$
$$1$$
$$1$$
E. $$0$$
$$2$$
$$1$$
F. $$1$$
$$2$$
$$0$$
G. $$1$$
$$2$$
$$2$$
H. $$1$$
$$1$$
$$2$$
I. $$0$$
$$2$$
$$2$$
J. $$2$$
$$2$$
$$1$$

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
We need to compute $\int_{-1}^{1} |z|\, dz$ along three different paths.

**Path (1): Straight line segment from -1 to 1**

Parametrize: $z = t$, $t$ from $-1$ to $1$, $dz = dt$.

$|z| = |t|$

$$\int_{-1}^{1} |t|\, dt = 2\int_0^1 t\, dt = 2 \cdot \frac{1}{2} = 1$$

**Path (2): Upper semicircle of unit circle**

Parametrize: $z = e^{i\theta}$, $\theta$ from $\pi$ to $0$ (going from $-1$ to $1$ along upper semicircle).

$|z| = |e^{i\theta}| = 1$, $dz = ie^{i\theta}\, d\theta$

$$\int_{\pi}^{0} 1 \cdot ie^{i\theta}\, d\theta = i\int_{\pi}^{0} e^{i\theta}\, d\theta = i\left[\frac{e^{i\theta}}{i}\right]_{\pi}^{0} = \left[e^{i\theta}\right]_{\pi}^{0} = e^{0} - e^{i\pi} = 1 - (-1) = 2$$

**Path (3): Lower semicircle of unit circle**

Parametrize: $z = e^{i\theta}$, $\theta$ from $-\pi$ to $0$ (going from $-1$ to $1$ along lower semicircle).

$|z| = 1$, $dz = ie^{i\theta}\, d\theta$

$$\int_{-\pi}^{0} 1 \cdot ie^{i\theta}\, d\theta = i\left[\frac{e^{i\theta}}{i}\right]_{-\pi}^{0} = \left[e^{i\theta}\right]_{-\pi}^{0} = e^{0} - e^{-i\pi} = 1 - (-1) = 2$$

Results: (1) = 1, (2) = 2, (3) = 2

\boxed{G}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 411
- Output tokens: 591
- Hit token cap: False
- Generation time: 6.20s
- Request ID: msg_01AdEwSbdqo5KWUg4wVBhCVf
