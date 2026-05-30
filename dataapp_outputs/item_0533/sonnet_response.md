# sonnet Response

## Prompt
```
A dean in the business school claims that GMAT scores of applicants to the school's MBA program have increased during the past 5 years. Five years ago, the mean and standard deviation of GMAT scores of MBA applicants were 530 and 50, respectively. 29 applications for this year's program were randomly selected and the GMAT scores recorded. If we assume that the distribution of GMAT scores of this year's applicants is the same as that of 5 years ago, find the probability of erroneously concluding that there is not enough evidence to supports the claim when, in fact, the true mean GMAT score is 560. Assume $\alpha$ is 0.05. P(Type II Error)=[ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
# sonnet Response

## Prompt
```
A dean in the business school claims that GMAT scores of applicants to the school's MBA program have increased during the past 5 years. Five years ago, the mean and standard deviation of GMAT scores of MBA applicants were 530 and 50, respectively. 29 applications for this year's program were randomly selected and the GMAT scores recorded. If we assume that the distribution of GMAT scores of this year's applicants is the same as that of 5 years ago, find the probability of erroneously concluding that there is not enough evidence to supports the claim when, in fact, the true mean GMAT score is 560. Assume $\alpha$ is 0.05. P(Type II Error)=[ANS]

Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

## Reasoning + Response
I need to find the probability of a Type II error (β) for a one-tailed test about the mean GMAT score.

## Setup

**Hypotheses:**
- H₀: μ = 530
- H₁: μ > 530 (dean claims scores increased)

**Given:**
- σ = 50, n = 29, α = 0.05
- True mean: μ₁ = 560

## Find the Critical Region

For a one-tailed (right-tail) test at α = 0.05:
- Critical z-value: z₀.₀₅ = 1.645

The rejection region: reject H₀ when z > 1.645

Critical value of x̄:
$$\bar{x}_c = \mu_0 + z_\alpha \cdot \frac{\sigma}{\sqrt{n}} = 530 + 1.645 \cdot \frac{50}{\sqrt{29}}$$

$$\frac{50}{\sqrt{29}} = \frac{50}{5.385} = 9.285$$

$$\bar{x}_c = 530 + 1.645 \times 9.285 = 530 + 15.274 = 545.274$$

## Calculate Type II Error

Type II error = P(fail to reject H₀ | μ = 560)
= P(x̄ < 545.274 | μ = 560)

Standardize using the true mean:
$$z = \frac{545.274 - 560}{9.285} = \frac{-14.726}{9.285} = -1.586$$

$$\beta = P(Z < -1.586)$$

From standard normal tables:
P(Z < -1.59) ≈ 0.0559
P(Z < -1.58) ≈ 0.0571

Interpolating: P(Z < -1.586) ≈ 0.0564

$$\boxed{0.0564}$$

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 345
- Output tokens: 499
- Hit token cap: False
- Generation time: 7.70s
- Request ID: msg_01QPy9PuYpjwdqbX1Q16SdkG

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 345
- Output tokens: 499
- Hit token cap: False
- Generation time: 7.70s
- Request ID: msg_01QPy9PuYpjwdqbX1Q16SdkG
