We need the volume inside the cylinder and below the upper half of the cone.

Use polar coordinates: \(x=r\cos\theta,\ y=r\sin\theta\).  
The cone is

\[
z^2=4r^2 \implies z=2r
\]

since the solid is above \(z=0\).

The cylinder is

\[
x^2+y^2=x \implies r^2=r\cos\theta \implies r=\cos\theta
\]

so the region is

\[
-\frac{\pi}{2}\le \theta \le \frac{\pi}{2}, \qquad 0\le r\le \cos\theta.
\]

Thus,

\[
V=\int_{-\pi/2}^{\pi/2}\int_0^{\cos\theta}\int_0^{2r} r\, dz\, dr\, d\theta.
\]

Compute:

\[
V=\int_{-\pi/2}^{\pi/2}\int_0^{\cos\theta} 2r^2\, dr\, d\theta
=\frac{2}{3}\int_{-\pi/2}^{\pi/2}\cos^3\theta\, d\theta.
\]

Since

\[
\int_{-\pi/2}^{\pi/2}\cos^3\theta\, d\theta=\frac{4}{3},
\]

we get

\[
V=\frac{2}{3}\cdot \frac{4}{3}=\frac{8}{9}.
\]

So the correct option is H.

\boxed{H}