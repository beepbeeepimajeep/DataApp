# sonnet Response

## Prompt
```
If f(2x) = x + 5 and f(g(6)) = 13, then 2 * g(6) =

Options:
A. 6
B. 18
C. 36
D. 8
E. 16
F. 32
G. 24
H. 12
I. 40
J. 30

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
Find 2·g(6).

From f(2x) = x + 5, let u = 2x, so x = u/2, giving f(u) = u/2 + 5.

f(g(6)) = 13 → g(6)/2 + 5 = 13 → g(6)/2 = 8 → g(6) = 16.

Therefore 2·g(6) = 32.

\boxed{F}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 269
- Output tokens: 118
- Hit token cap: False
- Generation time: 2.46s
- Request ID: msg_01Es3EQNeZ5TtRLUU6ApdSb4
