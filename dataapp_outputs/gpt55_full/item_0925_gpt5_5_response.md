We need count the digit 7 in all ID numbers from 101 through 977.

The last tag is:

\(101+877-1=977\)

Count 7s by digit place:

- Hundreds place: \(700\) to \(799\) gives \(100\) sevens.
- Tens place: From \(100\) to \(899\), there are \(8\) full hundred-blocks, each with \(10\) tens-place 7s: \(8\cdot 10=80\). From \(900\) to \(977\), the numbers \(970\) to \(977\) add \(8\). Total: \(88\).
- Ones place: Numbers ending in 7 from \(107\) to \(977\):

\[
\frac{977-107}{10}+1=88
\]

Total number of 7 stickers:

\[
100+88+88=276
\]

\(\boxed{276}\)