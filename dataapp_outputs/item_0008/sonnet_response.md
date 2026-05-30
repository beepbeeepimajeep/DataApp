# sonnet Response

## Prompt
```
What quantity of 70 per cent acid solution must be mixed with a 25 solution to produce 756 mL of a 50 per cent solution? [ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
Find the volume of 70% acid solution needed.

Let x = volume of 70% solution, then (756 - x) = volume of 25% solution.

Acid balance:
0.70x + 0.25(756 - x) = 0.50(756)

0.70x + 189 - 0.25x = 378

0.45x = 189

x = 420 mL

\boxed{420}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 219
- Output tokens: 110
- Hit token cap: False
- Generation time: 2.80s
- Request ID: msg_01Aaq5Ns6pdorB8t4fdVxRhe
