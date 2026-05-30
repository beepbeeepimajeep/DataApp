# sonnet Response

## Prompt
```
To express $\operatorname{cos} 3\theta$ in terms of $\operatorname{sin} \theta$ and $\operatorname{cos} \theta$ is ().

Options:
A. $$
cos3 \theta\!=\! \operatorname{s i n}^{2} \, \theta\!-\! 3 \operatorname{c o s} \, \theta\! \operatorname{s i n} \, \theta\!=\! 4 \operatorname{s i n}^{2} \, \theta\!-\! 3 \operatorname{c o s} \, \theta\
$$
B. $$
cos3 \theta\!=\! \operatorname{s i n}^{2} \, \theta\!+\! 3 \operatorname{c o s}^{2} \, \theta\! \operatorname{s i n} \, \theta\!=\! 4 \operatorname{s i n}^{2} \, \theta\!+\! 3 \operatorname{c o s}^{2} \, \theta\
$$
C. $$
cos3 \theta\!=\! \operatorname{c o s}^{3} \, \theta\!-\! 3 \operatorname{c o s} \, \theta\! \operatorname{s i n}^{2} \, \theta\!=\! 4 \operatorname{c o s}^{3} \, \theta\!-\! 3 \operatorname{c o s} \, \theta\
$$
D. $$
cos3 \theta\!=\! \operatorname{s i n}^{3} \, \theta\!+\! 3 \operatorname{c o s} \, \theta\! \operatorname{s i n} \, \theta\!=\! 4 \operatorname{s i n}^{3} \, \theta\!+\! 3 \operatorname{c o s} \, \theta\
$$
E. $$
cos3 \theta\!=\! \operatorname{c o s}^{2} \, \theta\!+\! 3 \operatorname{c o s} \, \theta\! \operatorname{s i n}^{2} \, \theta\!=\! 4 \operatorname{c o s}^{2} \, \theta\!+\! 3 \operatorname{c o s} \, \theta\
$$
F. $$
cos3 \theta\!=\! \operatorname{c o s}^{3} \, \theta\!+\! 3 \operatorname{s i n} \, \theta\! \operatorname{c o s}^{2} \, \theta\!=\! 4 \operatorname{c o s}^{3} \, \theta\!+\! 3 \operatorname{s i n} \, \theta\
$$
G. $$
cos3 \theta\!=\! \operatorname{c o s}^{3} \, \theta\!+\! 3 \operatorname{s i n}^{2} \, \theta\! \operatorname{c o s} \, \theta\!=\! 4 \operatorname{c o s}^{3} \, \theta\!+\! 3 \operatorname{s i n}^{2} \, \theta\
$$
H. $$
cos3 \theta\!=\! \operatorname{s i n}^{3} \, \theta\!-\! 3 \operatorname{s i n} \, \theta\! \operatorname{c o s}^{2} \, \theta\!=\! 4 \operatorname{s i n}^{3} \, \theta\!-\! 3 \operatorname{s i n} \, \theta\
$$
I. $$
cos3 \theta\!=\! \operatorname{s i n}^{3} \, \theta \!+\! 3 \operatorname{c o s} \, \theta\! \operatorname{s i n}^{2} \, \theta\!=\! 4 \operatorname{s i n}^{3} \, \theta\!+\! 3 \operatorname{c o s} \, \theta\
$$
J. $$
cos3 \theta\!=\! \operatorname{c o s}^{2} \, \theta\!-\! 3 \operatorname{s i n} \, \theta\! \operatorname{c o s} \, \theta\!=\! 4 \operatorname{c o s}^{2} \, \theta\!-\! 3 \operatorname{s i n} \, \theta\
$$

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
We need to expand cos(3θ).

cos(3θ) = cos(2θ + θ) = cos2θ·cosθ - sin2θ·sinθ

= (cos²θ - sin²θ)cosθ - (2sinθcosθ)sinθ

= cos³θ - sin²θcosθ - 2sin²θcosθ

= cos³θ - 3sin²θcosθ

Now simplify using sin²θ = 1 - cos²θ:

= cos³θ - 3(1 - cos²θ)cosθ

= cos³θ - 3cosθ + 3cos³θ

= 4cos³θ - 3cosθ

So: cos3θ = cos³θ - 3cosθsin²θ = 4cos³θ - 3cosθ

This matches option C.

\boxed{C}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 1425
- Output tokens: 237
- Hit token cap: False
- Generation time: 3.99s
- Request ID: msg_01Qf69RSfqLWmwHeAH4qtXG3
