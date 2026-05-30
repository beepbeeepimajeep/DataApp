# gpt_oss Response

## Prompt
```
What is the coefficient of $x^3y^{13}$ in $\left(\frac 12x + y\right)^{17}$ ?

Options:
A. 34
B. 136
C. 17
D. 170
E. 68
F. 340
G. 0
H. 85

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
The binomial expansion of \(\left(\frac12 x + y\right)^{17}\) is  

\[
\sum_{k=0}^{17} \binom{17}{k}\left(\frac12 x\right)^{k} y^{\,17-k}.
\]

Each term has total degree \(k+(17-k)=17\).  
For a term \(x^{3}y^{13}\) the total degree would be \(3+13=16\), which cannot occur in the expansion. Hence its coefficient is zero.

\[
\boxed{G}
\]

## Metadata
- Model: api-gpt-oss-120b
- Input tokens: 297
- Output tokens: 404
- Hit token cap: False
- Generation time: 2.30s
- Request ID: chatcmpl-9d1affe66baf1210
