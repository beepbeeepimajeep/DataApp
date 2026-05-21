We need find the antiderivative and match it to an option.

Let
\[
t=\sqrt[3]{\frac{x+1}{x-1}}.
\]
Then
\[
t^3=\frac{x+1}{x-1}
\]
so
\[
x=\frac{t^3+1}{t^3-1},\qquad dx=\frac{-6t^2}{(t^3-1)^2}\,dt.
\]
Also,
\[
\sqrt[3]{(x-1)(x+1)^2}=(x-1)t^2=\frac{2t^2}{t^3-1}.
\]
Thus
\[
\int \frac{dx}{\sqrt[3]{(x-1)(x+1)^2}}
=
\int \frac{-3}{t^3-1}\,dt.
\]
Now
\[
\frac{-3}{t^3-1}
=
-\frac1{t-1}+\frac{t+2}{t^2+t+1}.
\]
So
\[
\int \frac{-3}{t^3-1}\,dt
=
-\ln|t-1|+\frac12\ln|t^2+t+1|
+\sqrt3\arctan\left(\frac{2\sqrt3}{3}\left(t+\frac12\right)\right)+C.
\]
Substitute back
\[
t=\sqrt[3]{\frac{x+1}{x-1}}.
\]
This matches option D.

\boxed{D}