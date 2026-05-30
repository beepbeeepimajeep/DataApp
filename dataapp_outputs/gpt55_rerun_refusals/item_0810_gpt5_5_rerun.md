We need the general solution of the nonhomogeneous ODE.

Homogeneous equation:
\[
y''+y=0 \implies y_h=C_1\sin x+C_2\cos x.
\]

Since \(\sin x\) is part of the homogeneous solution, try
\[
y_p=Ax\cos x.
\]
Then
\[
y_p''+y_p=-2A\sin x.
\]
Set \(-2A=1\), so \(A=-\frac12\). Thus
\[
y_p=-\frac{x\cos x}{2}.
\]

So the exact general solution is
\[
y=C_1\sin x+C_2\cos x-\frac{x\cos x}{2}.
\]

None of the options matches exactly, but option E has the correct particular term and is likely the intended choice.

\boxed{E}