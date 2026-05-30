# sonnet Response

## Prompt
```
A man invests his savings in two accounts, one paying 6 percent and the other paying 10 percent simple interest per year. He puts twice as much in the lower-yielding account because it is less risky. His annual interest is 572 dollars. How much did he invest at each rate? Your answer is total in the account paying 6 percent interest is [ANS]
total in the account paying 10 percent interest is [ANS]

Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \boxed{...} with comma-separated values

End with: \boxed{value1,value2,value3}
```

## Reasoning + Response
Let x = amount at 10%, then 2x = amount at 6%.

Interest equation:
0.06(2x) + 0.10(x) = 572
0.12x + 0.10x = 572
0.22x = 572
x = 2600

So:
- Amount at 6%: 2x = 5200
- Amount at 10%: x = 2600

\boxed{5200,2600}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 333
- Output tokens: 114
- Hit token cap: False
- Generation time: 2.70s
- Request ID: msg_01EG5JGP3bScEPcyenbRjf5b
