from math import *

point1=[ 3, -5, 0]
point2=[ 7,  1, 0]
point3=[-2, 10, 0]
point4=[-7, -4, 0]

ins = [10, -30, 40]

def distance(a,b):
    return sqrt(pow(b[0]-a[0],2)+pow(b[1]-a[1],2)+pow(b[2]-a[2],2))

def adj_over_hyp(a,b,c):
    """a,b are adjacent, c is the third side"""
    hyp=max(a,b,c)
    if hyp==a: adj=b
    else: adj=a
    return adj/hyp

d12=distance(point1, point2)
d23=distance(point2, point3)
d34=distance(point3, point4)
d41=distance(point4, point1)

di1=distance(ins, point1)
di2=distance(ins, point2)
di3=distance(ins, point3)
di4=distance(ins, point4)

theta12=adj_over_hyp(di1, di2, d12)
theta23=adj_over_hyp(di2, di3, d23)
theta34=adj_over_hyp(di3, di4, d34)
theta41=adj_over_hyp(di4, di1, d41)

a=ins[0]
b=ins[1]
c=ins[2]

x1=point1[0]
x2=point2[0]
x3=point3[0]
x4=point4[0]
y1=point1[1]
y2=point2[1]
y3=point3[1]
y4=point4[1]

eq1_left=(x1 - a)* (x2 - a) + (y1 - b)* (y2 - b) + c
eq1_right=(
    sqrt(pow(abs(-x1 + a ),2)  + pow(abs(-y1 + b),2) +abs(c)) *
    sqrt(pow(abs(-x2 + a ),2)  + pow(abs(-y2 + b),2) +abs(c)) * theta12)

eq2_left=(x2 - a)* (x3 - a) + (y2 - b)* (y3 - b) + c
eq2_right=(
    sqrt(pow(abs(-x2 + a ),2)  + pow(abs(-y2 + b),2) +abs(c)) *
    sqrt(pow(abs(-x3 + a ),2)  + pow(abs(-y3 + b),2) +abs(c)) * theta23)

eq3_left=(x3 - a)* (x4 - a) + (y3 - b)* (y4 - b) + c
eq3_right=(
    sqrt(pow(abs(-x3 + a ),2)  + pow(abs(-y3 + b),2) +abs(c)) *
    sqrt(pow(abs(-x4 + a ),2)  + pow(abs(-y4 + b),2) +abs(c)) * theta34)

eq4_left=(x4 - a)* (x1 - a) + (y4 - b)* (y1 - b) + c
eq4_right=(
    sqrt(pow(abs(-x4 + a ),2)  + pow(abs(-y4 + b),2) +abs(c)) *
    sqrt(pow(abs(-x1 + a ),2)  + pow(abs(-y1 + b),2) +abs(c)) * theta41)

print eq1_left, eq1_right
print eq2_left, eq2_right
print eq3_left, eq3_right
print eq4_left, eq4_right
