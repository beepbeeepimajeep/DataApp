We need count pairs \((w,m)\), where \(w\) is days per week and \(m\) is days per month.

Conditions:
- \(w,m\) are integers,
- \(1<w<m<360\),
- \(m\mid 360\), since the number of months in a year is an integer.

For each valid month length \(m\), the week length \(w\) can be any integer from \(2\) to \(m-1\), giving \(m-2\) choices.

Now \(360=2^3\cdot 3^2\cdot 5\), so

\[
\sigma(360)=(1+2+4+8)(1+3+9)(1+5)=15\cdot 13\cdot 6=1170.
\]

The sum of proper divisors is

\[
1170-360=810.
\]

We exclude \(m=1,2\), which contribute no choices. The sum of valid \(m\)'s is

\[
810-1-2=807.
\]

There are \(24\) divisors total, so after excluding \(1,2,360\), there are

\[
24-3=21
\]

valid month lengths. Thus the total number of choices is

\[
807-2\cdot 21=765.
\]

So the correct option is I.

\boxed{I}