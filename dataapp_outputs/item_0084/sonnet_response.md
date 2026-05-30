# sonnet Response

## Prompt
```
Subtract the following integers:
${4-8=}$ [ANS]
${8-3=}$ [ANS]
${3-14=}$ [ANS]

Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \boxed{...} with comma-separated values

End with: \boxed{value1,value2,value3}
```

## Reasoning + Response
4 - 8 = -4
8 - 3 = 5
3 - 14 = -11

\boxed{-4,5,-11}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 275
- Output tokens: 45
- Hit token cap: False
- Generation time: 1.90s
- Request ID: msg_01MDDC7UMTnvcFySmAY5uest
