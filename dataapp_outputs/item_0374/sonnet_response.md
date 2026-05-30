# sonnet Response

## Prompt
```
Among a town’s registered voters, there are $36\%$ Democrats and $33\%$ Republicans. The rest are Independents. If there are $1240$ registered Independent voters in this town, how many total registered voters are there? Solution: This town has [ANS] registered Independent voters.

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
Independents make up 100% - 36% - 33% = 31% of registered voters.

If total voters = T, then 0.31T = 1240, so T = 1240/0.31 = 4000.

\boxed{4000}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 245
- Output tokens: 69
- Hit token cap: False
- Generation time: 2.00s
- Request ID: msg_0148Np9uEVHxxZ2gf8kgUFAw
