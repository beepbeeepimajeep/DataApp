We need find \(a,b,c\) from the given general solution.

The homogeneous solution is
\[
(C_1+C_2x)e^{-x},
\]
which means the characteristic equation has repeated root \(r=-1\). Therefore,
\[
r^2+ar+b=(r+1)^2=r^2+2r+1.
\]
So
\[
a=2,\qquad b=1.
\]

The particular solution is \(y_p=e^x\). Substitute into the differential equation:
\[
y_p'=e^x,\qquad y_p''=e^x.
\]
Thus,
\[
y_p''+ay_p'+by_p=e^x+2e^x+1e^x=4e^x.
\]
So
\[
c=4.
\]

Hence \((a,b,c)=(2,1,4)\), which is option G.

\[
\boxed{G}
\]