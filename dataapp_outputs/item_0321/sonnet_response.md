# sonnet Response

## Prompt
```
What's the value of a > 0, such that the tangent line to the graph of f(x) = (x^2) (e^(-x)) at x = a passes through the origin?

Options:
A. 0
B. 5
C. sqrt(2) (the square root of 2, approximately 1.41421)
D. -1 (note that this is not a valid option since the question specifies a > 0)
E. 1/2
F. 3
G. 2
H. 1
I. 4
J. e (Euler's number, approximately 2.71828)

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
Find a > 0 such that the tangent line to f(x) = x²e^(-x) at x = a passes through the origin.

**Setup:**
The tangent line at x = a has:
- Point: (a, a²e^(-a))
- Slope: f'(a)

f'(x) = 2x·e^(-x) - x²·e^(-x) = x·e^(-x)(2 - x)

So f'(a) = a·e^(-a)(2 - a)

**Tangent line equation:**
y - a²e^(-a) = a·e^(-a)(2-a)·(x - a)

For this to pass through (0, 0):
0 - a²e^(-a) = a·e^(-a)(2-a)·(0 - a)

-a²e^(-a) = -a²·e^(-a)(2-a)

Divide both sides by -a²e^(-a) (valid since a > 0):

1 = 2 - a

a = 1... wait, let me recheck.

Actually: 1 = (2 - a)

a = 1

Let me verify: At a = 1:
- f(1) = 1·e^(-1) = e^(-1)
- f'(1) = 1·e^(-1)(2-1) = e^(-1)
- Tangent line: y - e^(-1) = e^(-1)(x - 1) → y = e^(-1)·x

At x = 0: y = 0 ✓

The answer is a = 1.

\boxed{H}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 332
- Output tokens: 421
- Hit token cap: False
- Generation time: 5.89s
- Request ID: msg_01JdtJvP37gYwn4XCWo82cUf
