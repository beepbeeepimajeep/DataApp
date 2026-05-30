# gpt_oss Response

## Prompt
```
Fabrienne hired a face-painter for a birthday party. The painter charged a flat fee of ${\$90}$, and then charged ${\$4.50}$ per person. In the end, Fabrienne paid a total of ${\$193.50}$. How many people used the face-painter’s service? [ANS] people used the face-painter’s service.

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
The total cost consists of the flat fee plus the charge per person:

\[
193.50 = 90 + 4.50 \times n
\]

Subtract the flat fee:

\[
193.50 - 90 = 103.50 = 4.50 \times n
\]

Solve for \(n\):

\[
n = \frac{103.50}{4.50} = 23
\]

\[
\boxed{23}
\]

## Metadata
- Model: api-gpt-oss-120b
- Input tokens: 299
- Output tokens: 227
- Hit token cap: False
- Generation time: 1.29s
- Request ID: chatcmpl-8b3ea915b084c40b
