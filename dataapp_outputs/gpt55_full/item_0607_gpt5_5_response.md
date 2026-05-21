We need the requested centers and bounding-box corners, in order.

- Radius 4 sphere touching the xy-plane at the origin: center is (0,0,4).
- Radius 6 sphere on top of it: centers are vertically separated by 4+6=10, so center is (0,0,14).
- Tight axis-parallel box around these two spheres has x,y ranges [-6,6] and z range [0,20]. Corners: (6,6,20) and (-6,-6,0).
- Radius 9 sphere sitting on top of (-4,-4,1): center is (-4,-4,10).
- Radius 13 sphere hanging below it: centers are separated by 9+13=22 downward, so center is (-4,-4,-12).

Verification: there are exactly 6 coordinate triples, in the requested order.

\boxed{0,0,4,0,0,14,6,6,20,-6,-6,0,-4,-4,10,-4,-4,-12}