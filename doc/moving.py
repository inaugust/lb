
print "v1 := [x1-a,y1-b,-c];"
print "v2 := [x2-a,y2-b,-c];"
print "v3 := [x3-a,y3-b,-c];"
print "v4 := [x4-a,y4-b,-c];"
print "with(linalg);"
print "eq1 := v1 &* v2 = norm(v1,2) * norm(v2,2) * cos(theta1);"
print "eq2 := v2 &* v3 = norm(v2,2) * norm(v3,2) * cos(theta2);"
print "eq3 := v3 &* v4 = norm(v3,2) * norm(v4,2) * cos(theta3);"
print "eq4 := v4 &* v1 = norm(v4,2) * norm(v1,2) * cos(theta4);"
print "eq1 := evalm(eq1);"
print "eq2 := evalm(eq2);"
print "eq3 := evalm(eq3);"
print "eq4 := evalm(eq4);"
#print "solve( {eq1, eq2, eq3}, {a,b,c});"


from math import *

point1=[ 3, -5, 0]
point2=[ 7,  1, 0]
point3=[-2, 10, 0]
point4=[-7, -4, 0]

ins = [11, -32, 41]

def distance(a,b):
    return sqrt(pow(b[0]-a[0],2)+pow(b[1]-a[1],2)+pow(b[2]-a[2],2))

def adj_over_hyp(a,b,c):
    """a,b are adjacent, c is the third side"""
    # return the cosine of ab
    #return a/b
    #return a/c
    #return b/a
    #return b/c
    #return c/a
    #return c/b

    #hyp=max(a,b,c)
    #if hyp==a: adj=b
    #else: adj=a
    #return adj/hyp

    top = pow(a,2)+pow(b,2)-pow(c,2)
    bot = 2*a*b
    return top/bot

d12=distance(point1, point2)
d23=distance(point2, point3)
d34=distance(point3, point4)
d41=distance(point4, point1)

di1=distance(ins, point1)
di2=distance(ins, point2)
di3=distance(ins, point3)
di4=distance(ins, point4)

# These are actually cosines of theta
theta12=adj_over_hyp(di1, di2, d12)
theta23=adj_over_hyp(di2, di3, d23)
theta34=adj_over_hyp(di3, di4, d34)
theta41=adj_over_hyp(di4, di1, d41)

# Ony for maple
theta1=acos(theta12)
theta2=acos(theta23)
theta3=acos(theta34)
theta4=acos(theta41)

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

print 'a:=%f;' % a
print 'b:=%f;' % b
print 'c:=%f;' % c

print 'x1:=%f;' % x1
print 'x2:=%f;' % x2
print 'x3:=%f;' % x3
print 'x4:=%f;' % x4

print 'y1:=%f;' % y1
print 'y2:=%f;' % y2
print 'y3:=%f;' % y3
print 'y4:=%f;' % y4

print 'theta1:=%f;' % theta1
print 'theta2:=%f;' % theta2
print 'theta3:=%f;' % theta3
print 'theta4:=%f;' % theta4

print 'eq1;'
print 'eq2;'
print 'eq3;'
print 'eq4;'

def eval_equations(a,b,c):
    eq1_left=(x1 - a)* (x2 - a) + (y1 - b)* (y2 - b) + pow(c,2)
    eq1_right=(
        sqrt(pow(abs(-x1 + a ),2)  + pow(abs(-y1 + b),2) +pow(abs(c),2)) *
        sqrt(pow(abs(-x2 + a ),2)  + pow(abs(-y2 + b),2) +pow(abs(c),2)) *
        theta12)

    eq2_left=(x2 - a)* (x3 - a) + (y2 - b)* (y3 - b) + pow(c,2)
    eq2_right=(
        sqrt(pow(abs(-x2 + a ),2)  + pow(abs(-y2 + b),2) +pow(abs(c),2)) *
        sqrt(pow(abs(-x3 + a ),2)  + pow(abs(-y3 + b),2) +pow(abs(c),2)) *
        theta23)

    eq3_left=(x3 - a)* (x4 - a) + (y3 - b)* (y4 - b) + pow(c,2)
    eq3_right=(
        sqrt(pow(abs(-x3 + a ),2)  + pow(abs(-y3 + b),2) +pow(abs(c),2)) *
        sqrt(pow(abs(-x4 + a ),2)  + pow(abs(-y4 + b),2) +pow(abs(c),2)) *
        theta34)

    eq4_left=(x4 - a)* (x1 - a) + (y4 - b)* (y1 - b) + pow(c,2)
    eq4_right=(
        sqrt(pow(abs(-x4 + a ),2)  + pow(abs(-y4 + b),2) +pow(abs(c),2)) *
        sqrt(pow(abs(-x1 + a ),2)  + pow(abs(-y1 + b),2) +pow(abs(c),2)) *
        theta41)

    #print eq1_left, eq1_right
    #print eq2_left, eq2_right
    #print eq3_left, eq3_right
    #print eq4_left, eq4_right
    
    val = (abs(eq1_left-eq1_right) + abs(eq2_left-eq2_right) +
           abs(eq3_left-eq3_right) + abs(eq4_left-eq4_right))
    return val

print

def brute_force_a():
    done=0
    step=10.0
    xrange = [-100.0, 100.0]
    yrange = [-100.0, 100.0]
    zrange = [0.0, 100.0]
    while not done:
        vals = {}
        x=xrange[0]
        while x<=xrange[1]:
            print 'x=',x
            y=yrange[0]
            while y<=yrange[1]:
                z=zrange[0]
                while z<=zrange[1]:
                    #print x,y,z
                    vals[(x,y,z)]=eval_equations(x,y,z)
                    z=z+step
                y=y+step
            x=x+step
                
        vals_items = vals.items()
        l=[vals_items[0]]
        for (c,v) in vals.items():
            if v < l[0][1]:
                l.insert(0,(c,v))
                continue
            if (len(l)<2): continue
            if v < l[1][1]:
                l.insert(1,(c,v))
                continue
            if (len(l)<3): continue
            if v < l[2][1]:
                l.insert(2,(c,v))
                continue
            if (len(l)<4): continue
            if v < l[3][1]:
                l.insert(3,(c,v))
                continue
        
        print l[0]
        print l[1]
        print l[2]
        print l[3]
        xrange[0] = min (l[0][0][0], l[1][0][0], l[2][0][0], l[3][0][0])-step
        xrange[1] = max (l[0][0][0], l[1][0][0], l[2][0][0], l[3][0][0])+step
        
        yrange[0] = min (l[0][0][1], l[1][0][1], l[2][0][1], l[3][0][1])-step
        yrange[1] = max (l[0][0][1], l[1][0][1], l[2][0][1], l[3][0][1])+step
        
        zrange[0] = min (l[0][0][2], l[1][0][2], l[2][0][2], l[3][0][2])-step
        zrange[1] = max (l[0][0][2], l[1][0][2], l[2][0][2], l[3][0][2])+step
        step=step/10.0
        if (step==0.01): done=1

def brute_force_b():
    done=0
    step=10.0
    xrange = [-100.0, 100.0]

    while not done:
        vals = {}
        x=xrange[0]
        y=0
        z=0
        while x<=xrange[1]:
            vals[(x,y,z)]=eval_equations(x,y,z)
            x=x+step
                
        vals_items = vals.items()
        l=[vals_items[0]]
        for (c,v) in vals.items():
            if v < l[0][1]:
                l.insert(0,(c,v))
                continue
            if (len(l)<2): continue
            if v < l[1][1]:
                l.insert(1,(c,v))
                continue
            if (len(l)<3): continue
            if v < l[2][1]:
                l.insert(2,(c,v))
                continue
            if (len(l)<4): continue
            if v < l[3][1]:
                l.insert(3,(c,v))
                continue
        
        print l[0]
        print l[1]
        print l[2]
        print l[3]
        xrange[0] = min (l[0][0][0], l[1][0][0], l[2][0][0], l[3][0][0])-step
        xrange[1] = max (l[0][0][0], l[1][0][0], l[2][0][0], l[3][0][0])+step
        step=step/10
        if (step==0.01): done=1

    done=0
    step=10.0
    yrange = [-100.0, 100.0]
    while not done:
        vals = {}
        x=0
        y=yrange[0]
        z=0
        while y<=yrange[1]:
            vals[(x,y,z)]=eval_equations(x,y,z)
            y=y+step
                
        vals_items = vals.items()
        l=[vals_items[0]]
        for (c,v) in vals.items():
            if v < l[0][1]:
                l.insert(0,(c,v))
                continue
            if (len(l)<2): continue
            if v < l[1][1]:
                l.insert(1,(c,v))
                continue
            if (len(l)<3): continue
            if v < l[2][1]:
                l.insert(2,(c,v))
                continue
            if (len(l)<4): continue
            if v < l[3][1]:
                l.insert(3,(c,v))
                continue
        
        print l[0]
        print l[1]
        print l[2]
        print l[3]
        yrange[0] = min (l[0][0][1], l[1][0][1], l[2][0][1], l[3][0][1])-step
        yrange[1] = max (l[0][0][1], l[1][0][1], l[2][0][1], l[3][0][1])+step
        step=step/10
        if (step==0.01): done=1

    done=0
    step=10.0
    zrange = [0.0, 100.0]
    while not done:
        vals = {}
        x=0
        y=0
        z=zrange[0]
        while z<=zrange[1]:
            vals[(x,y,z)]=eval_equations(x,y,z)
            z=z+step
                
        vals_items = vals.items()
        l=[vals_items[0]]
        for (c,v) in vals.items():
            if v < l[0][1]:
                l.insert(0,(c,v))
                continue
            if (len(l)<2): continue
            if v < l[1][1]:
                l.insert(1,(c,v))
                continue
            if (len(l)<3): continue
            if v < l[2][1]:
                l.insert(2,(c,v))
                continue
            if (len(l)<4): continue
            if v < l[3][1]:
                l.insert(3,(c,v))
                continue
        
        print l[0]
        print l[1]
        print l[2]
        print l[3]
        zrange[0] = min (l[0][0][2], l[1][0][2], l[2][0][2], l[3][0][2])-step
        zrange[1] = max (l[0][0][2], l[1][0][2], l[2][0][2], l[3][0][2])+step
        step=step/10
        if (step==0.01): done=1


brute_force_a()
