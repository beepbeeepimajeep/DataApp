# sonnet Response

## Prompt
```
If $x+4=5 \sin(\theta)$ for $0 < \theta < \pi/2$ express $\cos(2\theta)$ in terms of $x$. $\cos(2\theta)$=[ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We need cos(2θ) in terms of x.

Given: x + 4 = 5sin(θ), so sin(θ) = (x+4)/5.

Using the double angle formula:
cos(2θ) = 1 - 2sin²(θ) = 1 - 2·((x+4)/5)² = 1 - 2(x+4)²/25 = (25 - 2(x+4)²)/25

\boxed{\dfrac{25-2(x+4)^2}{25}}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 237
- Output tokens: 141
- Hit token cap: False
- Generation time: 2.87s
- Request ID: msg_01QE1AVfErrd3gBU5JrtCNNr
