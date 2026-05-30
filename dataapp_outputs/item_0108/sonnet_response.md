# sonnet Response

## Prompt
```
Using a double-angle or half-angle formula to simplify the given expressions.
(a) If $\cos^2 36^\circ-\sin^2 36^\circ=\cos A^\circ,$ then $A=$ [ANS] degrees; (b) If $\cos^2 6x-\sin^2 6x=\cos B,$ then $B=$ [ANS].

Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \boxed{...} with comma-separated values

End with: \boxed{value1,value2,value3}
```

## Reasoning + Response
Using the double-angle formula: cos²θ - sin²θ = cos(2θ)

(a) cos²36° - sin²36° = cos(2·36°) = cos(72°), so A = 72

(b) cos²6x - sin²6x = cos(2·6x) = cos(12x), so B = 12x

\boxed{72, 12x}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 330
- Output tokens: 102
- Hit token cap: False
- Generation time: 2.08s
- Request ID: msg_01G9Es2awfJXpAAQ2odw4xyc
