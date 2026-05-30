# gpt_oss Response

## Prompt
```
In a group of healthy cows and chickens, the number of legs is 22 more than twice the number of heads. The number of the cows in the group is [ANS].

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
The variables are:
- \(c\): number of cows  
- \(k\): number of chickens  

Heads = total animals = \(c+k\).  
Legs = \(4c + 2k\).

Given that legs are 22 more than twice the number of heads:

\[
4c + 2k = 2(c+k) + 22.
\]

Simplify:

\[
4c + 2k = 2c + 2k + 22 \\
4c - 2c = 22 \\
2c = 22 \\
c = 11.
\]

Thus the group contains **11 cows**.

\[
\boxed{11}
\]

## Metadata
- Model: api-gpt-oss-120b
- Input tokens: 258
- Output tokens: 458
- Hit token cap: False
- Generation time: 2.52s
- Request ID: chatcmpl-a05c2dd2cd3eb529
