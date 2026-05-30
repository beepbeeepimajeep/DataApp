# sonnet Response

## Prompt
```
Use a sum or difference identity to find the exact value of each expression: Note: You are not allowed to use decimals in your answer. $\tan(285 ^ \circ)$=[ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
Find the exact value of tan(285°).

Write 285° = 240° + 45°.

Use the tangent addition formula:
$$\tan(A+B) = \frac{\tan A + \tan B}{1 - \tan A \tan B}$$

With A = 240°, B = 45°:
- tan(240°) = tan(180°+60°) = tan(60°) = √3
- tan(45°) = 1

$$\tan(285°) = \frac{\sqrt{3} + 1}{1 - \sqrt{3} \cdot 1} = \frac{\sqrt{3}+1}{1-\sqrt{3}}$$

Rationalize by multiplying numerator and denominator by (1+√3):

$$= \frac{(\sqrt{3}+1)(1+\sqrt{3})}{(1-\sqrt{3})(1+\sqrt{3})} = \frac{\sqrt{3}+3+1+\sqrt{3}}{1-3} = \frac{4+2\sqrt{3}}{-2} = -(2+\sqrt{3})$$

\boxed{-2-\sqrt{3}}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 225
- Output tokens: 295
- Hit token cap: False
- Generation time: 3.79s
- Request ID: msg_01EkTmTnj96VYvGZNXX5P1w5
