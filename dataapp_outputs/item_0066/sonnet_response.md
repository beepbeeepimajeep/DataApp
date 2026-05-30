# sonnet Response

## Prompt
```
A pilot flies in a straight path for 1 hour and 30 min. She then makes a course correction, heading 10 degrees to the right of her original course, and flies 2 hours in the new direction. If she maintains a constant speed of 675 miles per hour, how far is she from her starting position?
Answer: [ANS] miles

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
I need to find the straight-line distance from the starting position after two legs of flight.

**Setup:**
- Speed: 675 mph
- Leg 1: 1.5 hours → distance = 675 × 1.5 = 1012.5 miles
- Leg 2: 2 hours → distance = 675 × 2 = 1350 miles
- Angle between the two legs: 10° (course correction to the right means the angle between the two directions is 10°)

**Using the Law of Cosines:**

The angle between the two path segments is 180° - 10° = 170° (the interior angle at the turning point, since she deviated only 10° from her original direction).

Wait — let me think carefully. If she's flying in direction θ and then turns 10° to the right, the new direction is θ + 10°. The angle between the two legs at the vertex is 180° - 10° = 170°.

The triangle has sides a = 1012.5, b = 1350, and the included angle at the turning point = 180° - 10° = 170°.

**Law of Cosines:**
$$c^2 = a^2 + b^2 - 2ab\cos(\theta)$$

where θ = 170°.

$$c^2 = (1012.5)^2 + (1350)^2 - 2(1012.5)(1350)\cos(170°)$$

Calculate each term:
- $(1012.5)^2 = 1{,}025{,}156.25$
- $(1350)^2 = 1{,}822{,}500$
- $2(1012.5)(1350) = 2{,}733{,}750$
- $\cos(170°) \approx -0.98481$

$$c^2 = 1{,}025{,}156.25 + 1{,}822{,}500 - 2{,}733{,}750 \times (-0.98481)$$
$$c^2 = 2{,}847{,}656.25 + 2{,}691{,}929.6$$
$$c^2 = 5{,}539{,}585.85$$
$$c \approx \sqrt{5{,}539{,}585.85} \approx 2353.6$$

Rounding to the nearest mile:

$$c \approx 2354 \text{ miles}$$

\boxed{2354}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 260
- Output tokens: 624
- Hit token cap: False
- Generation time: 8.59s
- Request ID: msg_018DVSTfpfx4e4GADYu4fTmA
