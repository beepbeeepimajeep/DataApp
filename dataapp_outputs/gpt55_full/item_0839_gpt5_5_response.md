We need evaluate the infinite series and choose the matching option.

Let \(a_n=\mathrm{Arccot}(n)\). Then

\[
\cot(a_n-a_{n+1})
=\frac{\cot a_n\cot a_{n+1}+1}{\cot a_{n+1}-\cot a_n}
=\frac{n(n+1)+1}{(n+1)-n}
=n^2+n+1.
\]

Since \(a_n-a_{n+1}>0\), we have

\[
\mathrm{Arccot}(n^2+n+1)=a_n-a_{n+1}.
\]

Thus the series telescopes:

\[
\sum_{n=0}^\infty \mathrm{Arccot}(n^2+n+1)
=\sum_{n=0}^\infty (a_n-a_{n+1})
=a_0-\lim_{N\to\infty}a_{N+1}.
\]

Now \(a_0=\mathrm{Arccot}(0)=\frac{\pi}{2}\), and \(\lim_{N\to\infty}\mathrm{Arccot}(N+1)=0\). Therefore the sum is

\[
\frac{\pi}{2}.
\]

This corresponds to option G.

\boxed{G}