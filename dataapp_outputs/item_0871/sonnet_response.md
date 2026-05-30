# sonnet Response

## Prompt
```
The locus of the mid point of the line segment joining the focus to a moving point on the parabola $y^{2}=4ax$ is another parabola with directrix

Options:
A. x=a
B. x=-a
C. x=$\frac {a}{2}$
D. x=\frac{a}{3}
E. x=-\frac{3a}{2}
F. x=\frac{3a}{2}
G. x=0
H. x=\frac{2a}{3}
I. x=-\frac{a}{2}

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
The focus of y² = 4ax is (a, 0). A point on the parabola is (at², 2at).

Midpoint M = (h, k):
- h = (a + at²)/2
- k = (0 + 2at)/2 = at

From k = at: t = k/a

Substitute into h:
h = (a + a(k/a)²)/2 = (a + k²/a)/2

2h = a + k²/a

k² = a(2h - a)

Replace (h,k) with (x,y):
y² = a(2x - a) = 2a(x - a/2)

This is a parabola of the form y² = 4A(x - h₀) where 4A = 2a, so A = a/2, and vertex at (a/2, 0).

The directrix is at x - h₀ = -A:
x = a/2 - a/2 = 0

\boxed{G}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 327
- Output tokens: 259
- Hit token cap: False
- Generation time: 4.59s
- Request ID: msg_01DCgCztRsRidm9AC9CNRvKv
