# sonnet Response

## Prompt
```
The option that represents the area of the plane figure enclosed by ( x = 1 - {y^2},;x = 0 ) is

Options:
A. ( int_0^1 {left[ {sqrt {1 - x} + sqrt {1 - x} } right]dx} )
B. ( int_0^1 {left[ {sqrt {1 - x} - sqrt {1 - x} } right]dx} )
C. ( int_0^1 {left[ {sqrt {1 - x} - ( - sqrt {1 - x} )} right]dx} )
D. ( int_0^1 {sqrt {1 - x} dx} )
E. ( int_0^1 {left[ {sqrt {1 - x} + ( - sqrt {1 - x} )} right]dx} )
F. ( int_0^1 {left[ {sqrt {1 - x} + (1 - sqrt {1 - x})} right]dx} )
G. ( int_0^1 {( - sqrt {1 - x} )dx} )
H. ( int_0^1 {(1 - {y^2})dy} )
I. ( int_0^1 {left[ {sqrt {1 - x} + ( - 2sqrt {1 - x} )} right]dx} )
J. ( int_0^1 {left[ {sqrt {1 - x} - 2( - sqrt {1 - x} )} right]dx} )

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
The curve is x = 1 - y², x = 0.

From x = 1 - y², we get y² = 1 - x, so y = ±√(1-x).

The parabola x = 1 - y² opens left, vertex at (1, 0), intersecting x = 0 at y = ±1.

**Method 1: Integrate with respect to y**

The region is bounded by x = 1 - y² (right boundary) and x = 0 (left boundary), for y from -1 to 1.

Area = ∫₋₁¹ (1 - y²) dy

By symmetry = 2∫₀¹ (1 - y²) dy

This matches option H if we note: ∫₀¹ (1 - y²) dy = [y - y³/3]₀¹ = 2/3, so 2×(2/3) = 4/3.

Wait, option H is ∫₀¹ (1-y²) dy = 2/3, which is only half the area. Let me reconsider.

Actually, let me check option A: ∫₀¹ [√(1-x) + √(1-x)] dx = ∫₀¹ 2√(1-x) dx

= 2 · [-(2/3)(1-x)^(3/2)]₀¹ = 2 · (2/3) = 4/3. ✓

**Method 2: Integrate with respect to x**

For a given x ∈ [0,1], the region spans from y = -√(1-x) to y = √(1-x).

Area = ∫₀¹ [√(1-x) - (-√(1-x))] dx = ∫₀¹ 2√(1-x) dx = 4/3 ✓

This is option C: ∫₀¹ [√(1-x) - (-√(1-x))] dx

Let me verify the actual area: 4/3.

Option A: ∫₀¹ [√(1-x) + √(1-x)] dx = ∫₀¹ 2√(1-x) dx = 4/3 ✓

Option C: ∫₀¹ [√(1-x) - (-√(1-x))] dx = ∫₀¹ 2√(1-x) dx = 4/3 ✓

Both A and C equal 4/3, but C is the proper form for area between two curves (upper minus lower), where upper = √(1-x) and lower = -√(1-x).

Option C is the mathematically correct representation of area as [upper function - lower function].

\boxed{C}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 551
- Output tokens: 709
- Hit token cap: False
- Generation time: 9.79s
- Request ID: msg_01ErDo53peoQEeeqMUuy8KDm
