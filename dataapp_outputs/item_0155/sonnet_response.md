# sonnet Response

## Prompt
```
A guy wire needs to be installed to support a pole. The end of the wire on the pole will be ${14\ {\rm ft}}$ from the ground, and the angle formed by the wire and the ground will be $49$ degrees. On the ground, how far away is the guy wire from the pole? Round your answer to two decimal places if needed. On the ground, the distance from the guy wire to the pole is [ANS]ft.

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We need the horizontal distance from the pole to where the wire meets the ground.

The pole height = 14 ft (opposite side), the angle at the ground = 49°, and we want the adjacent side.

tan(49°) = opposite/adjacent = 14/d

d = 14/tan(49°) = 14/1.15037... ≈ 12.17 ft

\boxed{12.17}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 277
- Output tokens: 103
- Hit token cap: False
- Generation time: 2.89s
- Request ID: msg_018cJymLCHA4fkkk2SGVRM6t
