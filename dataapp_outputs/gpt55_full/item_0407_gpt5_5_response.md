We need the minimum weighted path length using Huffman coding for weights \(7,8,10,12,13,14\).

Combine the two smallest weights repeatedly:

\[
7+8=15
\]

Remaining: \(10,12,13,14,15\)

\[
10+12=22
\]

Remaining: \(13,14,15,22\)

\[
13+14=27
\]

Remaining: \(15,22,27\)

\[
15+22=37
\]

Remaining: \(27,37\)

\[
27+37=64
\]

The Huffman weighted path length is the sum of all combined weights:

\[
W(T)=15+22+27+37+64=165
\]

So the correct option is C.

\boxed{C}