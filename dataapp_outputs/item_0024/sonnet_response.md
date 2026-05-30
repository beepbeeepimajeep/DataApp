# sonnet Response

## Prompt
```
Suppose that the line $\hat{y}=3+2x$ is fitted to the data points (-1,2), (2,7), and (5,13). Determine the sum of the squared residuals. Sum of the Squared Residuals=[ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
For each point, compute the residual (actual y - predicted y):

Point (-1, 2): ŷ = 3 + 2(-1) = 1, residual = 2 - 1 = 1
Point (2, 7): ŷ = 3 + 2(2) = 7, residual = 7 - 7 = 0
Point (5, 13): ŷ = 3 + 2(5) = 13, residual = 13 - 13 = 0

Sum of squared residuals = 1² + 0² + 0² = 1

\boxed{1}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 241
- Output tokens: 163
- Hit token cap: False
- Generation time: 3.08s
- Request ID: msg_01XHRfBmMrZjoGAqAmfRaaZb
