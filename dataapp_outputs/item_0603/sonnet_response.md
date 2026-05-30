# sonnet Response

## Prompt
```
For each problem, select the best response.
(a) Which of the following is least affected if an extreme high outlier is added to your data? [ANS] A. The mean.  B. The standard deviation.  C. The median.  D. None of the above.
(b) What percent of the observations in a distribution lie between the first quartile and the third quartile? [ANS] A. 50\%.  B. 25\%.  C. 75\%.  D. None of the above.
(c) To make a boxplot of a distribution, you must know [ANS] A. the mean and the standard deviation.  B. the five-number summary.  C. all of the individual observations.  D. None of the above.

Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \boxed{...} with comma-separated values

End with: \boxed{value1,value2,value3}
```

## Reasoning + Response
(a) The median is a positional measure and is resistant to outliers. Adding an extreme high value shifts the mean and inflates the standard deviation significantly, but the median barely changes. → **C**

(b) By definition, the interquartile range spans from Q1 to Q3, capturing the middle 50% of observations. → **A**

(c) A boxplot requires the five-number summary: minimum, Q1, median, Q3, maximum. → **B**

Three answers required, in order (a), (b), (c). ✓

\boxed{C,A,B}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 406
- Output tokens: 141
- Hit token cap: False
- Generation time: 3.49s
- Request ID: msg_012RjBvq95EFKY2889PdLEQ3
