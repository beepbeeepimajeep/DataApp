# gpt_oss Response

## Prompt
```
Suppose that for a given least-squares regression, the sum of squares for error is 70 and the sum of squares for regression is 95. Find the coefficient of determination. Coefficient of Determination=[ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
The coefficient of determination \(R^{2}\) is the proportion of total variation explained by the regression:

\[
R^{2}= \frac{\text{SSR}}{\text{SST}}, \qquad 
\text{with } \text{SST}= \text{SSR}+\text{SSE}.
\]

Given  
\(\text{SSR}=95\) and \(\text{SSE}=70\),

\[
\text{SST}=95+70=165,
\qquad
R^{2}= \frac{95}{165}= \frac{19}{33}.
\]

\[
\boxed{\frac{19}{33}}
\]

## Metadata
- Model: api-gpt-oss-120b
- Input tokens: 267
- Output tokens: 243
- Hit token cap: False
- Generation time: 1.37s
- Request ID: chatcmpl-b65cba8b54d5f8c0
