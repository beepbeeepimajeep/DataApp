# sonnet Response

## Prompt
```
Mr. Cleary's class and Ms. Ntuala's class go to use the computer lab. There are 20 computers available, two of which do not work. Mr. Cleary's class has 14 kids, and Ms. Ntuala's class has 12 kids. If every student must use a computer and there can only be 2 students on a computer at most, what is the maximum number of students who can have a computer to themselves?

Options:
A. 10
B. 24
C. 18
D. 20
E. 8
F. 6
G. 2
H. 12
I. 16
J. 14

Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Reasoning + Response
Total students: 14 + 12 = 26
Working computers: 20 - 2 = 18

Each computer holds at most 2 students. With 18 computers and 26 students, we need to seat all 26 students.

Let x = number of computers with 1 student, y = number of computers with 2 students.

x + y ≤ 18 (can't exceed available computers)
x + 2y = 26 (all students must be seated)

From these: y = 26 - x - y... let me solve properly.

x + 2y = 26 and x + y ≤ 18

From x + y ≤ 18: y ≥ 26 - 18 = 8

To maximize x (students alone), minimize y. Minimum y = 8.

Then x = 26 - 2(8) = 26 - 16 = 10.

Check: 10 + 8 = 18 computers used ✓

Maximum students with a computer to themselves = **10**.

\boxed{A}

## Metadata
- Model: claude-sonnet-4-6
- Input tokens: 339
- Output tokens: 268
- Hit token cap: False
- Generation time: 5.50s
- Request ID: msg_01FcMvVBuGqcsszxbhgZBuSn
