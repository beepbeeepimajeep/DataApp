We need the largest power of 2 dividing the difference, i.e. its 2-adic valuation.

Using LTE for odd integers \(a,b\) and even \(m\):

\[
v_2(a^m-b^m)=v_2(a-b)+v_2(a+b)+v_2(m)-1.
\]

Here \(a=2005\), \(b=2003\), and \(m=2^{100}\).

\[
v_2(2005-2003)=v_2(2)=1
\]

\[
2005+2003=4008=8\cdot 501 \implies v_2(4008)=3
\]

\[
v_2(2^{100})=100
\]

So

\[
v_2\left(2005^{2^{100}}-2003^{2^{100}}\right)
=1+3+100-1=103.
\]

Thus the correct option is G.

\[
\boxed{G}
\]