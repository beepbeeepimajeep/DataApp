We need the initial population, the population at 75 minutes, and the time when the population reaches 11000.

From the two data points,
\[
\frac{1600}{700}=e^{25k}
\]
so
\[
k=\frac{\ln(16/7)}{25}.
\]

(a)
\[
P_0=700e^{-15k}=700\left(\frac{7}{16}\right)^{3/5}.
\]

(b)
\[
P(75)=700e^{60k}=700\left(\frac{16}{7}\right)^{12/5}.
\]

(c)
\[
11000=700e^{k(t-15)}
\]
so
\[
t=15+\frac{\ln(11000/700)}{k}
=15+\frac{25\ln(110/7)}{\ln(16/7)}.
\]

Verification: there are exactly 3 answers, ordered as (a) initial size, (b) population after 75 minutes, (c) time to reach 11000.

\boxed{700\left(\frac{7}{16}\right)^{3/5},\ 700\left(\frac{16}{7}\right)^{12/5},\ 15+\frac{25\ln(110/7)}{\ln(16/7)}}