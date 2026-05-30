# sonnet Response

## Prompt
```
For the purposes of this question a household corresponds to a single residential address, while household size is the number of individuals living at that address. Say you conduct a simple random sample of individuals living in Vancouver. Those sampled are asked to report their household sizes. The sample average of household size will be: [ANS] A. systematically biased downwards as an estimator of the average size of Vancouver households.  B. sensible as an estimator of the average size of Vancouver households.  C. systematically biased upwards as an estimator of the average size of Vancouver households.

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
When sampling individuals (not households), larger households are overrepresented because each person in a size-k household has the same chance of being selected, meaning a household of size k is k times more likely to contribute a respondent than a household of size 1. This is the "size-biased sampling" or "inspection paradox" effect. The sample mean of reported household sizes will therefore be higher than the true average household size.

\boxed{C}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 303
- Output tokens: 101
- Hit token cap: False
- Generation time: 3.29s
- Request ID: msg_01ThwG75Sh8wZ13RzWZnFcGS
