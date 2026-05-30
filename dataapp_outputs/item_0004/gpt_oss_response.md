# gpt_oss Response

## Prompt
```
If the point (10,-7) is on the terminal side of the angle $\theta$ in standard position, $\sin (\theta)=$ [ANS] ; $\cos (\theta)=$ [ANS] ; $\tan (\theta)=$ [ANS].

Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \boxed{...} with comma-separated values

End with: \boxed{value1,value2,value3}
```

## Reasoning + Response
The point \((10,-7)\) lies on the terminal side of \(\theta\).  
Its distance from the origin is  

\[
r=\sqrt{10^{2}+(-7)^{2}}=\sqrt{100+49}=\sqrt{149}.
\]

Hence  

\[
\sin\theta=\frac{y}{r}= \frac{-7}{\sqrt{149}},\qquad
\cos\theta=\frac{x}{r}= \frac{10}{\sqrt{149}},\qquad
\tan\theta=\frac{y}{x}= \frac{-7}{10}.
\]

\[
\boxed{-\frac{7}{\sqrt{149}},\frac{10}{\sqrt{149}},-\frac{7}{10}}
\]

## Metadata
- Model: api-gpt-oss-120b
- Input tokens: 322
- Output tokens: 358
- Hit token cap: False
- Generation time: 3.20s
- Request ID: chatcmpl-88611c9a3bc63892
