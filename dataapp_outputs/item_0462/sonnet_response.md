# sonnet Response

## Prompt
```
Let $f(x)=\sqrt{56-x}$ and $g(x)=x^2-x$. Then the domain of $f\circ g$ is equal to $[a,b]$ for $a=$ [ANS]
and $b=$ [ANS]

Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \boxed{...} with comma-separated values

End with: \boxed{value1,value2,value3}
```

## Reasoning + Response
We need the domain of f∘g, where f(g(x)) = √(56 - (x²-x)) = √(56 - x² + x).

Require: 56 - x² + x ≥ 0, i.e., x² - x - 56 ≤ 0.

Factor: x² - x - 56 = (x-8)(x+7) ≤ 0.

This holds for -7 ≤ x ≤ 8.

So a = -7, b = 8.

\boxed{-7,8}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 302
- Output tokens: 150
- Hit token cap: False
- Generation time: 2.90s
- Request ID: msg_01ENF7iZByLeyWL7yGxGavTV
