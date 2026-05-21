We need the antiderivative and then match it to the given options.

Let  
\[
u=x+1,\qquad R=\sqrt{u^2+1}.
\]
Then
\[
I=5\int \frac{du}{1+R}.
\]

Use \(u=\sinh t\), so \(R=\cosh t\) and \(du=\cosh t\,dt\). Then
\[
I=5\int \frac{\cosh t}{1+\cosh t}\,dt
=5\int\left(1-\frac1{1+\cosh t}\right)dt.
\]
Since
\[
1+\cosh t=2\cosh^2\frac t2,
\]
we get
\[
I=5\left(t-\tanh\frac t2\right)+C.
\]

Back-substitute:
\[
t=\operatorname{arsinh}u=\ln(u+R),
\]
and
\[
\tanh\frac t2=\frac{u}{R+1}.
\]
Thus
\[
I=5\ln(u+R)-5\frac{u}{R+1}+C.
\]

This is equivalent to
\[
I=5\ln(u+R)+\frac{10}{u+R+1}+C.
\]
Substitute \(u=x+1\), \(R=\sqrt{x^2+2x+2}\):
\[
I=5\ln\left(x+1+\sqrt{x^2+2x+2}\right)
+\frac{10}{x+2+\sqrt{x^2+2x+2}}+C.
\]

This matches option E.

\[
\boxed{E}
\]