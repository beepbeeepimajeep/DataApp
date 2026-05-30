# sonnet Response

## Prompt
```
A survey team is trying to estimate the height of a mountain above a level plain. From one point on the plain, they observe that the angle of elevation to the top of the mountain is $30 ^\circ$. From a point 1500 feet closer to the mountain along the plain, they find that the angle of elevation is $34 ^\circ$. How high (in feet) is the mountain? [ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
Let h be the height of the mountain and d be the horizontal distance from the closer point to the base.

From the closer point: tan(34°) = h/d, so d = h/tan(34°)

From the farther point: tan(30°) = h/(d + 1500), so d + 1500 = h/tan(30°)

Subtracting: 1500 = h/tan(30°) - h/tan(34°)

1500 = h(1/tan(30°) - 1/tan(34°))

1/tan(30°) = cot(30°) = √3 ≈ 1.73205
1/tan(34°) = cot(34°) ≈ 1/0.67451 ≈ 1.48256

h = 1500/(1.73205 - 1.48256) = 1500/0.24949 ≈ 6013

\boxed{6013}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 274
- Output tokens: 244
- Hit token cap: False
- Generation time: 4.32s
- Request ID: msg_01WeEASbVEB9n2TTffedFbdw
