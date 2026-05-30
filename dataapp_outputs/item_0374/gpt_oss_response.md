# gpt_oss Response

## Prompt
```
Among a town’s registered voters, there are $36\%$ Democrats and $33\%$ Republicans. The rest are Independents. If there are $1240$ registered Independent voters in this town, how many total registered voters are there? Solution: This town has [ANS] registered Independent voters.

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
The percentages give  

\[
\text{Independents}=100\%-36\%-33\%=31\%
\]

If the total number of voters is \(N\),

\[
0.31N = 1240 \quad\Longrightarrow\quad N = \frac{1240}{0.31}= \frac{1240\cdot100}{31}= \frac{124000}{31}=4000.
\]

\[
\boxed{4000}
\]

## Metadata
- Model: api-gpt-oss-120b
- Input tokens: 285
- Output tokens: 282
- Hit token cap: False
- Generation time: 1.70s
- Request ID: chatcmpl-8baa2a519ca7b6ed
