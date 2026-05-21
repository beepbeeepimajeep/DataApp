We need the limit and the corresponding multiple-choice option.

\[
L=\lim_{x\to 0}\left(\frac1{x^2}-\cot^2 x\right)
=\lim_{x\to 0}\left(\frac1{x^2}-\frac1{\tan^2 x}\right)
\]

\[
L=\lim_{x\to 0}\frac{\tan^2 x-x^2}{x^2\tan^2 x}
=\lim_{x\to 0}\frac{(\tan x-x)(\tan x+x)}{x^2\tan^2 x}
\]

Rewrite:

\[
L=\left(\lim_{x\to 0}\frac{\tan x-x}{x^3}\right)
\left(\lim_{x\to 0}\frac{x(\tan x+x)}{\tan^2 x}\right)
\]

Using L’Hopital’s Rule,

\[
\lim_{x\to 0}\frac{\tan x-x}{x^3}
=\lim_{x\to 0}\frac{\sec^2 x-1}{3x^2}
=\frac13\lim_{x\to 0}\left(\frac{\tan x}{x}\right)^2
=\frac13
\]

Also,

\[
\lim_{x\to 0}\frac{x(\tan x+x)}{\tan^2 x}=2
\]

Thus,

\[
L=\frac13\cdot 2=\frac23
\]

So the correct option is D.

\boxed{D}