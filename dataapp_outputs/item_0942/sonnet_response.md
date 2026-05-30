# sonnet Response

## Prompt
```
Solve the equation 5\sqrt{n}=n-6. Solutions (separate by commas): $n=$ [ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We need to solve 5√n = n - 6.

Let u = √n (u ≥ 0), so n = u².

5u = u² - 6
u² - 5u - 6 = 0
(u - 6)(u + 1) = 0

u = 6 or u = -1

Since u ≥ 0, u = 6, so n = 36.

Check: 5√36 = 30, and 36 - 6 = 30. ✓

\boxed{36}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 211
- Output tokens: 141
- Hit token cap: False
- Generation time: 2.25s
- Request ID: msg_01Dvie3xqmGrQV68GgW7sXDh
