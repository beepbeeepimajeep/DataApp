# sonnet Response

## Prompt
```
Find the equation of a sine wave that is obtained by shifting the graph of $y=\sin(x)$ to the right 7 units and downward 6 units and is vertically stretched by a factor of 6 when compared to $y=\sin(x)$. $y=$ [ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We need to shift right 7, down 6, and vertically stretch by 6.

- Shift right 7: replace x with (x - 7)
- Vertical stretch by 6: multiply sin by 6
- Shift down 6: subtract 6

Result: y = 6sin(x - 7) - 6

\boxed{6\sin(x-7)-6}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 251
- Output tokens: 97
- Hit token cap: False
- Generation time: 2.48s
- Request ID: msg_01SHcwhgRrj9nMEMZVt2RDDc
