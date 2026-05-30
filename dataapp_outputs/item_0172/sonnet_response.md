# sonnet Response

## Prompt
```
Find the exact value. $\small{\sin} \left(\small{2 \cos^{-1}} \large{\left(\frac{11}{61}\right)} \right)$=[ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
We need sin(2cos⁻¹(11/61)).

Let θ = cos⁻¹(11/61), so cos θ = 11/61.

sin θ = √(1 - (11/61)²) = √(1 - 121/3721) = √(3600/3721) = 60/61.

sin(2θ) = 2 sin θ cos θ = 2 · (60/61) · (11/61) = 1320/3721.

\boxed{\dfrac{1320}{3721}}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 227
- Output tokens: 144
- Hit token cap: False
- Generation time: 2.81s
- Request ID: msg_01NvviScKPTRU5G4wrEdANdJ
