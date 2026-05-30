# gpt5_4 Response

## Prompt
```
Determine the greatest possible value of $\sum_{i=1}^{10} \cos(3x_i)$ for real numbers $x_1,x_2,\dots,x_{10}$ satisfying $\sum_{i=1}^{10} \cos(x_i) = 0$.

Options:
A. \frac{480}{49}
B. \frac{480}{56}
C. \frac{480}{51}
D. \frac{480}{48}
E. \frac{480}{47}
F. \frac{480}{52}
G. \frac{480}{55}
H. \frac{480}{53}
I. \frac{480}{50}
J. \frac{480}{54}

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
We want the maximum of
\[
\sum_{i=1}^{10}\cos(3x_i)
\]
given
\[
\sum_{i=1}^{10}\cos x_i=0.
\]

Let
\[
y_i=\cos x_i \in [-1,1].
\]
Using the triple-angle identity,
\[
\cos(3x_i)=4\cos^3 x_i-3\cos x_i=4y_i^3-3y_i.
\]
So we must maximize
\[
\sum_{i=1}^{10}(4y_i^3-3y_i)
\]
subject to
\[
\sum_{i=1}^{10} y_i=0,\qquad -1\le y_i\le 1.
\]

Because \(\sum y_i=0\), the linear term vanishes:
\[
\sum_{i=1}^{10}(4y_i^3-3y_i)=4\sum_{i=1}^{10} y_i^3.
\]
Thus we need to maximize
\[
\sum y_i^3
\quad\text{subject to}\quad
\sum y_i=0,\ -1\le y_i\le 1.
\]

Since \(t^3\) is convex on \([0,1]\) and concave on \([-1,0]\), the maximum under a linear constraint occurs at extreme values. So take as many variables as possible at endpoints.

Let \(k\) of the \(y_i\)'s be \(1\), one value be \(a\in[-1,1]\), and the remaining \(9-k\) values be \(-1\), arranged to make the sum \(0\).

Try the natural extremal pattern:
\[
4\text{ of them }=1,\quad 5\text{ of them }=-1,\quad 1\text{ remaining }=a.
\]
Then
\[
4(1)+5(-1)+a=0 \implies a=1.
\]
That gives \(5\) ones and \(5\) minus ones, yielding
\[
\sum \cos(3x_i)=5(1)+5(-1)=0,
\]
not maximal.

A better extremal balance is:
\[
6\text{ of them }=1,\quad 4\text{ of them }=b.
\]
Then
\[
6+4b=0 \implies b=-\frac32,
\]
impossible.

So use
\[
5\text{ of them }=1,\quad 1\text{ of them }=a,\quad 4\text{ of them }=-1.
\]
Then
\[
5+a-4=0 \implies a=-1,
\]
again just endpoints.

To get a nontrivial optimum, use Lagrange multipliers on interior points:
maximize \(4\sum y_i^3\) with \(\sum y_i=0\). Then for interior values,
\[
12y_i^2=\lambda,
\]
so all interior \(y_i\) have the same absolute value. Hence at optimum, values are among \(\{1,-1,t,-t\}\), and by convexity the best arrangement is \(8\) variables at \(1\) or \(-1\) and two equal interior values.

Take
\[
4\text{ of them }=1,\quad 4\text{ of them }=-1,\quad y_9=t,\ y_{10}=-t.
\]
Then the sum constraint holds automatically, and
\[
\sum \cos(3x_i)=4(1)+4(-1)+(4t^3-3t)+(4(-t)^3-3(-t))=0.
\]
Still not good.

So instead take \(m\) ones and \(10-m\) equal negatives \(c\), with
\[
m+(10-m)c=0 \implies c=-\frac{m}{10-m}.
\]
We need \(c\in[-1,1]\), so \(m\le 5\).

Then
\[
S=\sum \cos(3x_i)=m+(10-m)(4c^3-3c).
\]
Substitute \(c=-\frac{m}{10-m}\):
\[
S=m+(10-m)\left(4\left(-\frac{m}{10-m}\right)^3-3\left(-\frac{m}{10-m}\right)\right).
\]
This simplifies to
\[
S=4m-\frac{4m^3}{(10-m)^2}.
\]

Now test \(m=1,2,3,4,5\):

- \(m=1:\ S=4-\frac{4}{81}=\frac{320}{81}\)
- \(m=2:\ S=8-\frac{32}{64}=\frac{15}{2}\)
- \(m=3:\ S=12-\frac{108}{49}=\frac{480}{49}\)
- \(m=4:\ S=16-\frac{256}{36}=\frac{80}{9}\)
- \(m=5:\ S=20-\frac{500}{25}=0\)

The largest is
\[
\frac{480}{49}.
\]

Thus the correct option is A.

\boxed{A}

## Metadata
- Model: gpt-5.4
- Input tokens: 314
- Output tokens: 1159
- Hit token cap: False
- Generation time: 15.90s
- Request ID: chatcmpl-DhOAG1lCN1IJYOP3UemGXTaP6mZxv
